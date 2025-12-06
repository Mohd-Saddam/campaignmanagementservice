from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.schemas import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    CampaignStatus, DiscountType
)
from app import crud
from app.logger import get_logger

# Get logger instance
logger = get_logger(__name__)

# Initialize rate limiter for this router
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


def campaign_to_response(campaign) -> CampaignResponse:
    """Convert Campaign model to CampaignResponse with full customer details."""
    from app.schemas import CustomerResponse
    
    # Only include targeted customers if campaign is actually targeted
    # This prevents orphaned associations from showing in the API response
    if campaign.is_targeted and campaign.target_customers:
        target_customer_ids = [c.id for c in campaign.target_customers]
        targeted_customers = [
            CustomerResponse(
                id=c.id,
                email=c.email,
                name=c.name,
                created_at=c.created_at
            ) for c in campaign.target_customers
        ]
    else:
        target_customer_ids = []
        targeted_customers = []
    
    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        discount_type=campaign.discount_type,
        discount_percentage=campaign.discount_percentage,
        discount_flat=campaign.discount_flat,
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        total_budget=campaign.total_budget,
        used_budget=campaign.used_budget,
        max_usage_per_customer_per_day=campaign.max_usage_per_customer_per_day,
        min_cart_value=campaign.min_cart_value,
        max_discount_amount=campaign.max_discount_amount,
        is_targeted=campaign.is_targeted,
        status=campaign.status,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
        target_customer_ids=target_customer_ids,
        targeted_customers=targeted_customers
    )


@router.post("/", response_model=CampaignResponse, status_code=201)
def create_campaign(campaign: CampaignCreate, db: Session = Depends(get_db)):
    """
    Create a new discount campaign.
    
    - **name**: Campaign name
    - **discount_type**: Either 'cart' or 'delivery'
    - **discount_percentage**: Percentage discount (0-100)
    - **discount_flat**: Flat discount amount (alternative to percentage)
    - **start_date**: Campaign start date
    - **end_date**: Campaign end date (x days constraint)
    - **total_budget**: Maximum budget for the campaign
    - **max_usage_per_customer_per_day**: Limit transactions per customer per day
    - **is_targeted**: If true, only specified customers can use
    - **target_customer_ids**: List of customer IDs for targeted campaigns
    """
    logger.info(f"Creating campaign: {campaign.name}, type={campaign.discount_type}, targeted={campaign.is_targeted}")
    
    # Validate that at least one discount type is provided
    if not campaign.discount_percentage and not campaign.discount_flat:
        logger.log_validation_error(
            entity="campaign",
            field="discount",
            value=None,
            reason="Either discount_percentage or discount_flat must be provided"
        )
        raise HTTPException(
            status_code=400,
            detail="Either discount_percentage or discount_flat must be provided"
        )
    
    # Validate target customers if campaign is targeted
    if campaign.is_targeted and not campaign.target_customer_ids:
        logger.log_validation_error(
            entity="campaign",
            field="target_customer_ids",
            value=None,
            reason="Required for targeted campaigns"
        )
        raise HTTPException(
            status_code=400,
            detail="target_customer_ids required for targeted campaigns"
        )
    
    # Verify all target customers exist
    if campaign.is_targeted and campaign.target_customer_ids:
        logger.info(f"Validating {len(campaign.target_customer_ids)} target customers for campaign: {campaign.name}")
        for customer_id in campaign.target_customer_ids:
            customer = crud.get_customer(db, customer_id)
            if not customer:
                logger.log_validation_error(
                    entity="campaign",
                    field="target_customer_ids",
                    value=customer_id,
                    reason="Customer not found"
                )
                raise HTTPException(
                    status_code=404,
                    detail=f"Target customer with ID {customer_id} not found"
                )
    
    try:
        db_campaign = crud.create_campaign(db, campaign)
        logger.log_campaign_operation(
            operation="create",
            campaign_id=db_campaign.id,
            campaign_name=db_campaign.name,
            campaign_type=campaign.discount_type.value,
            success=True
        )
        return campaign_to_response(db_campaign)
    except Exception as e:
        logger.log_campaign_operation(
            operation="create",
            campaign_id=None,
            campaign_name=campaign.name,
            campaign_type=campaign.discount_type.value,
            success=False,
            error=str(e)
        )
        raise


@router.get("/", response_model=List[CampaignResponse])
def get_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[CampaignStatus] = None,
    discount_type: Optional[DiscountType] = None,
    db: Session = Depends(get_db)
):
    """
    Get all campaigns with optional filters.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **status**: Filter by campaign status
    - **discount_type**: Filter by discount type (cart/delivery)
    """
    campaigns = crud.get_campaigns(db, skip=skip, limit=limit, status=status, discount_type=discount_type)
    return [campaign_to_response(c) for c in campaigns]


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Get a specific campaign by ID."""
    campaign = crud.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Update status if needed
    campaign = crud.update_campaign_status(db, campaign)
    return campaign_to_response(campaign)


@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: int, 
    campaign_update: CampaignUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update a campaign.
    
    Only provide the fields you want to update.
    """
    logger.info(f"Updating campaign {campaign_id}: is_targeted={campaign_update.is_targeted}, target_customers={campaign_update.target_customer_ids}")
    
    # Validate date range if both dates provided
    if campaign_update.start_date and campaign_update.end_date:
        if campaign_update.end_date <= campaign_update.start_date:
            logger.log_validation_error(
                entity="campaign",
                field="date_range",
                value=f"{campaign_update.start_date} - {campaign_update.end_date}",
                reason="end_date must be after start_date"
            )
            raise HTTPException(
                status_code=400,
                detail="end_date must be after start_date"
            )
    
    # Validate targeted campaign logic
    if campaign_update.is_targeted is True and campaign_update.target_customer_ids is not None:
        if len(campaign_update.target_customer_ids) == 0:
            logger.log_validation_error(
                entity="campaign",
                field="target_customer_ids",
                value=None,
                reason="Targeted campaigns must have at least one customer"
            )
            raise HTTPException(
                status_code=400,
                detail="Targeted campaigns must have at least one target customer"
            )
        
        # Verify all target customers exist
        for customer_id in campaign_update.target_customer_ids:
            customer = crud.get_customer(db, customer_id)
            if not customer:
                logger.log_validation_error(
                    entity="campaign",
                    field="target_customer_ids",
                    value=customer_id,
                    reason="Customer not found"
                )
                raise HTTPException(
                    status_code=404,
                    detail=f"Target customer with ID {customer_id} not found"
                )
    
    # If setting is_targeted to False, ensure target_customer_ids is also cleared
    if campaign_update.is_targeted is False and campaign_update.target_customer_ids is None:
        campaign_update.target_customer_ids = []
        logger.info(f"Campaign {campaign_id} is_targeted=False, clearing target customers")
    
    try:
        campaign = crud.update_campaign(db, campaign_id, campaign_update)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        logger.log_campaign_operation(
            operation="update",
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            campaign_type=campaign.discount_type.value,
            success=True
        )
        return campaign_to_response(campaign)
    except HTTPException:
        raise
    except Exception as e:
        logger.log_campaign_operation(
            operation="update",
            campaign_id=campaign_id,
            campaign_name="unknown",
            campaign_type="unknown",
            success=False,
            error=str(e)
        )
        raise


@router.delete("/{campaign_id}", status_code=204)
def delete_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Delete a campaign."""
    success = crud.delete_campaign(db, campaign_id)
    if not success:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return None


@router.patch("/{campaign_id}/status", response_model=CampaignResponse)
def update_campaign_status(
    campaign_id: int,
    status: CampaignStatus,
    db: Session = Depends(get_db)
):
    """Update campaign status (activate/deactivate)."""
    campaign = crud.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign_update = CampaignUpdate(status=status)
    updated_campaign = crud.update_campaign(db, campaign_id, campaign_update)
    return campaign_to_response(updated_campaign)
