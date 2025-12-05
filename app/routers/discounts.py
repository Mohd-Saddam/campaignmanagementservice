from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.schemas import (
    CartParameters, AvailableDiscountsResponse, AvailableDiscount,
    DiscountUsageCreate, DiscountUsageResponse, DiscountType
)
from app import crud
from app.models import DiscountType as ModelDiscountType

# Initialize rate limiter for this router
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/discounts", tags=["Discounts"])


@router.post("/available", response_model=AvailableDiscountsResponse)
@limiter.limit("60/minute")  # Rate limit discount checks
def get_available_discounts(request: Request, cart_params: CartParameters, db: Session = Depends(get_db)):
    """
    Get all available discount campaigns for a customer based on cart parameters.
    
    This endpoint checks:
    - Campaign is active and within date range
    - Budget is not exhausted
    - Customer hasn't exceeded daily usage limit
    - Customer is eligible (for targeted campaigns)
    - Cart value meets minimum requirement
    
    Returns both cart and delivery discounts with the best option highlighted.
    """
    # Verify customer exists
    customer = crud.get_customer(db, cart_params.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get eligible cart discounts
    cart_campaigns = crud.get_eligible_campaigns(
        db, 
        cart_params.customer_id, 
        cart_params.cart_value,
        ModelDiscountType.CART
    )
    
    # Get eligible delivery discounts
    delivery_campaigns = crud.get_eligible_campaigns(
        db,
        cart_params.customer_id,
        cart_params.delivery_charge,
        ModelDiscountType.DELIVERY
    )
    
    cart_discounts = []
    delivery_discounts = []
    
    # Calculate cart discounts
    for campaign in cart_campaigns:
        discount_amount = crud.calculate_discount_amount(campaign, cart_params.cart_value)
        if discount_amount > 0:
            cart_discounts.append(AvailableDiscount(
                campaign_id=campaign.id,
                campaign_name=campaign.name,
                discount_type=DiscountType.CART,
                discount_amount=discount_amount,
                original_value=cart_params.cart_value,
                final_value=round(cart_params.cart_value - discount_amount, 2),
                message=f"Save ₹{discount_amount} on your cart!"
            ))
    
    # Calculate delivery discounts
    for campaign in delivery_campaigns:
        discount_amount = crud.calculate_discount_amount(campaign, cart_params.delivery_charge)
        if discount_amount > 0:
            delivery_discounts.append(AvailableDiscount(
                campaign_id=campaign.id,
                campaign_name=campaign.name,
                discount_type=DiscountType.DELIVERY,
                discount_amount=discount_amount,
                original_value=cart_params.delivery_charge,
                final_value=round(cart_params.delivery_charge - discount_amount, 2),
                message=f"Save ₹{discount_amount} on delivery!"
            ))
    
    # Find best discounts
    best_cart = max(cart_discounts, key=lambda x: x.discount_amount) if cart_discounts else None
    best_delivery = max(delivery_discounts, key=lambda x: x.discount_amount) if delivery_discounts else None
    
    return AvailableDiscountsResponse(
        cart_discounts=cart_discounts,
        delivery_discounts=delivery_discounts,
        best_cart_discount=best_cart,
        best_delivery_discount=best_delivery
    )


@router.post("/apply", response_model=DiscountUsageResponse)
@limiter.limit("30/minute")  # Rate limit discount applications (more strict)
def apply_discount(request: Request, usage: DiscountUsageCreate, db: Session = Depends(get_db)):
    """
    Apply a discount to a customer's transaction.
    
    This will:
    - Validate the discount is still available
    - Check all eligibility criteria
    - Record the usage
    - Update the campaign's used budget
    """
    # Verify customer exists
    customer = crud.get_customer(db, usage.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Verify campaign exists
    campaign = crud.get_campaign(db, usage.campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Check eligibility using appropriate value based on discount type
    # Cart discounts check against cart_value, delivery discounts check against delivery_charge
    eligibility_value = usage.cart_value if campaign.discount_type == ModelDiscountType.CART else usage.delivery_charge
    eligible_campaigns = crud.get_eligible_campaigns(
        db,
        usage.customer_id,
        eligibility_value,
        campaign.discount_type
    )
    
    if campaign not in eligible_campaigns:
        raise HTTPException(
            status_code=400,
            detail="Customer is not eligible for this discount"
        )
    
    # Calculate and apply discount based on discount type
    # For cart discounts, use cart_value; for delivery discounts, use delivery_charge
    value = usage.cart_value if campaign.discount_type == ModelDiscountType.CART else usage.delivery_charge
    discount_amount = crud.calculate_discount_amount(campaign, value)
    
    if discount_amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="No discount available for this transaction"
        )
    
    # Record the usage
    db_usage = crud.create_discount_usage(
        db,
        usage.campaign_id,
        usage.customer_id,
        discount_amount,
        usage.cart_value
    )
    
    return db_usage


@router.get("/usage/{customer_id}")
def get_customer_discount_usage(
    customer_id: int,
    campaign_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get discount usage history for a customer."""
    customer = crud.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    usages = customer.discount_usages
    if campaign_id:
        usages = [u for u in usages if u.campaign_id == campaign_id]
    
    return [
        DiscountUsageResponse(
            id=u.id,
            campaign_id=u.campaign_id,
            customer_id=u.customer_id,
            discount_amount=u.discount_amount,
            cart_value=u.cart_value,
            used_at=u.used_at
        )
        for u in usages
    ]
