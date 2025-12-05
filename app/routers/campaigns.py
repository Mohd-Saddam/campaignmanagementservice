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

# Initialize rate limiter for this router
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


def campaign_to_response(campaign) -> CampaignResponse:
    """Convert Campaign model to CampaignResponse."""
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
        target_customer_ids=[c.id for c in campaign.target_customers] if campaign.target_customers else []
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
    # Validate that at least one discount type is provided
    if not campaign.discount_percentage and not campaign.discount_flat:
        raise HTTPException(
            status_code=400,
            detail="Either discount_percentage or discount_flat must be provided"
        )
    
    # Validate target customers if campaign is targeted
    if campaign.is_targeted and not campaign.target_customer_ids:
        raise HTTPException(
            status_code=400,
            detail="target_customer_ids required for targeted campaigns"
        )
    
    db_campaign = crud.create_campaign(db, campaign)
    return campaign_to_response(db_campaign)


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
    campaign = crud.update_campaign(db, campaign_id, campaign_update)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign_to_response(campaign)


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
