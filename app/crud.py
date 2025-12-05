"""
CRUD Operations Module

This module contains all database operations (Create, Read, Update, Delete)
for customers, campaigns, and discount usage. It also includes business logic
for calculating discounts and checking eligibility.
"""

from sqlalchemy.orm import Session  # SQLAlchemy session for database operations
from sqlalchemy import and_, func  # SQL query helpers
from datetime import datetime, timedelta  # Date and time handling
from typing import List, Optional  # Type hints

# Import models and schemas
from app.models import Campaign, Customer, DiscountUsage, CampaignStatus, DiscountType, campaign_customers
from app.schemas import CampaignCreate, CampaignUpdate, CustomerCreate


# ============================================
# Customer CRUD Operations
# ============================================

def create_customer(db: Session, customer: CustomerCreate) -> Customer:
    """
    Create a new customer in the database.
    
    Args:
        db: Database session
        customer: Customer data from request
        
    Returns:
        Customer: The created customer object
    """
    # Create new Customer instance from request data
    db_customer = Customer(
        email=customer.email,
        name=customer.name
    )
    db.add(db_customer)  # Add to session
    db.commit()  # Save to database
    db.refresh(db_customer)  # Refresh to get generated ID
    return db_customer


def get_customer(db: Session, customer_id: int) -> Optional[Customer]:
    """
    Get a customer by their ID.
    
    Args:
        db: Database session
        customer_id: ID of the customer to retrieve
        
    Returns:
        Customer or None: The customer if found, None otherwise
    """
    return db.query(Customer).filter(Customer.id == customer_id).first()


def get_customer_by_email(db: Session, email: str) -> Optional[Customer]:
    """
    Get a customer by their email address.
    
    Args:
        db: Database session
        email: Email address to search for
        
    Returns:
        Customer or None: The customer if found, None otherwise
    """
    return db.query(Customer).filter(Customer.email == email).first()


def get_customers(db: Session, skip: int = 0, limit: int = 100) -> List[Customer]:
    """
    Get all customers with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
    Returns:
        List[Customer]: List of customer objects
    """
    return db.query(Customer).offset(skip).limit(limit).all()


# ============================================
# Campaign CRUD Operations
# ============================================

def create_campaign(db: Session, campaign: CampaignCreate) -> Campaign:
    """
    Create a new campaign in the database.
    
    Args:
        db: Database session
        campaign: Campaign data from request
        
    Returns:
        Campaign: The created campaign object
    """
    # Convert request data to dict, excluding target_customer_ids (handled separately)
    campaign_data = campaign.model_dump(exclude={'target_customer_ids'})
    db_campaign = Campaign(**campaign_data)
    
    # If campaign is targeted, add the target customers
    if campaign.is_targeted and campaign.target_customer_ids:
        # Fetch all target customers from database
        target_customers = db.query(Customer).filter(
            Customer.id.in_(campaign.target_customer_ids)
        ).all()
        db_campaign.target_customers = target_customers
    
    db.add(db_campaign)  # Add to session
    db.commit()  # Save to database
    db.refresh(db_campaign)  # Refresh to get generated ID
    return db_campaign


def get_campaign(db: Session, campaign_id: int) -> Optional[Campaign]:
    """
    Get a campaign by its ID.
    
    Args:
        db: Database session
        campaign_id: ID of the campaign to retrieve
        
    Returns:
        Campaign or None: The campaign if found, None otherwise
    """
    return db.query(Campaign).filter(Campaign.id == campaign_id).first()


def get_campaigns(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[CampaignStatus] = None,
    discount_type: Optional[DiscountType] = None
) -> List[Campaign]:
    """
    Get all campaigns with optional filters and pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        status: Optional filter by campaign status
        discount_type: Optional filter by discount type
        
    Returns:
        List[Campaign]: List of campaign objects matching filters
    """
    query = db.query(Campaign)
    
    # Apply optional filters
    if status:
        query = query.filter(Campaign.status == status)
    if discount_type:
        query = query.filter(Campaign.discount_type == discount_type)
    
    return query.offset(skip).limit(limit).all()


def update_campaign(db: Session, campaign_id: int, campaign_update: CampaignUpdate) -> Optional[Campaign]:
    """
    Update an existing campaign.
    
    Args:
        db: Database session
        campaign_id: ID of the campaign to update
        campaign_update: New campaign data (only provided fields are updated)
        
    Returns:
        Campaign or None: Updated campaign if found, None otherwise
    """
    # Get existing campaign
    db_campaign = get_campaign(db, campaign_id)
    if not db_campaign:
        return None
    
    # Get only the fields that were explicitly set in the request
    update_data = campaign_update.model_dump(exclude_unset=True, exclude={'target_customer_ids'})
    
    # Update each field
    for field, value in update_data.items():
        setattr(db_campaign, field, value)
    
    # Update target customers if specified
    if campaign_update.target_customer_ids is not None:
        target_customers = db.query(Customer).filter(
            Customer.id.in_(campaign_update.target_customer_ids)
        ).all()
        db_campaign.target_customers = target_customers
    
    db_campaign.updated_at = datetime.utcnow()  # Update timestamp
    db.commit()
    db.refresh(db_campaign)
    return db_campaign


def delete_campaign(db: Session, campaign_id: int) -> bool:
    """
    Delete a campaign from the database.
    
    Args:
        db: Database session
        campaign_id: ID of the campaign to delete
        
    Returns:
        bool: True if deleted successfully, False if not found
    """
    db_campaign = get_campaign(db, campaign_id)
    if not db_campaign:
        return False
    
    db.delete(db_campaign)
    db.commit()
    return True


def update_campaign_status(db: Session, campaign: Campaign) -> Campaign:
    """
    Update campaign status based on current date and budget usage.
    
    Automatically sets status to:
    - EXPIRED: if end_date has passed
    - BUDGET_EXHAUSTED: if used_budget >= total_budget
    
    Args:
        db: Database session
        campaign: Campaign to check and update
        
    Returns:
        Campaign: Updated campaign object
    """
    now = datetime.utcnow()
    
    # Check if campaign has expired
    if campaign.end_date < now:
        campaign.status = CampaignStatus.EXPIRED
    # Check if budget is exhausted
    elif campaign.used_budget >= campaign.total_budget:
        campaign.status = CampaignStatus.BUDGET_EXHAUSTED
    
    db.commit()
    db.refresh(campaign)
    return campaign


# ============================================
# Discount Usage Operations
# ============================================

def get_customer_daily_usage_count(
    db: Session, 
    campaign_id: int, 
    customer_id: int, 
    date: datetime = None
) -> int:
    """
    Get the number of times a customer has used a campaign today.
    
    Used to enforce the max_usage_per_customer_per_day limit.
    
    Args:
        db: Database session
        campaign_id: ID of the campaign
        customer_id: ID of the customer
        date: Date to check (defaults to today)
        
    Returns:
        int: Number of times the customer used this campaign today
    """
    if date is None:
        date = datetime.utcnow()
    
    # Calculate start and end of the day
    start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    
    # Count usage records for this customer/campaign combination today
    count = db.query(DiscountUsage).filter(
        and_(
            DiscountUsage.campaign_id == campaign_id,
            DiscountUsage.customer_id == customer_id,
            DiscountUsage.used_at >= start_of_day,
            DiscountUsage.used_at < end_of_day
        )
    ).count()
    
    return count


def create_discount_usage(
    db: Session, 
    campaign_id: int, 
    customer_id: int, 
    discount_amount: float,
    cart_value: float
) -> DiscountUsage:
    """
    Record a discount usage and update campaign budget.
    
    Args:
        db: Database session
        campaign_id: ID of the campaign being used
        customer_id: ID of the customer using the discount
        discount_amount: Amount of discount applied
        cart_value: Cart value at time of discount
        
    Returns:
        DiscountUsage: The created usage record
    """
    # Create new usage record
    db_usage = DiscountUsage(
        campaign_id=campaign_id,
        customer_id=customer_id,
        discount_amount=discount_amount,
        cart_value=cart_value
    )
    db.add(db_usage)
    
    # Update campaign's used budget
    campaign = get_campaign(db, campaign_id)
    if campaign:
        campaign.used_budget += discount_amount  # Add discount to used budget
        update_campaign_status(db, campaign)  # Check if budget exhausted
    
    db.commit()
    db.refresh(db_usage)
    return db_usage


def get_eligible_campaigns(
    db: Session,
    customer_id: int,
    cart_value: float,
    discount_type: Optional[DiscountType] = None
) -> List[Campaign]:
    """
    Get all campaigns that a customer is eligible to use.
    
    Checks the following eligibility criteria:
    1. Campaign is active
    2. Current date is within campaign date range
    3. Campaign has remaining budget
    4. Cart value meets minimum requirement
    5. Customer is in target list (for targeted campaigns)
    6. Customer hasn't exceeded daily usage limit
    
    Args:
        db: Database session
        customer_id: ID of the customer
        cart_value: Current cart value
        discount_type: Optional filter by discount type
        
    Returns:
        List[Campaign]: List of eligible campaigns
    """
    now = datetime.utcnow()
    
    # Base query: active campaigns within date range with remaining budget
    query = db.query(Campaign).filter(
        and_(
            Campaign.status == CampaignStatus.ACTIVE,  # Must be active
            Campaign.start_date <= now,  # Must have started
            Campaign.end_date >= now,  # Must not have ended
            Campaign.used_budget < Campaign.total_budget,  # Must have budget
            Campaign.min_cart_value <= cart_value  # Cart value requirement
        )
    )
    
    # Apply optional discount type filter
    if discount_type:
        query = query.filter(Campaign.discount_type == discount_type)
    
    campaigns = query.all()
    eligible_campaigns = []
    
    for campaign in campaigns:
        # Check targeting: if targeted, customer must be in target list
        if campaign.is_targeted:
            target_customer_ids = [c.id for c in campaign.target_customers]
            if customer_id not in target_customer_ids:
                continue  # Skip - customer not in target list
        
        # Check daily usage limit
        daily_usage = get_customer_daily_usage_count(db, campaign.id, customer_id)
        if daily_usage >= campaign.max_usage_per_customer_per_day:
            continue  # Skip - customer exceeded daily limit
        
        # Check remaining budget
        remaining_budget = campaign.total_budget - campaign.used_budget
        if remaining_budget <= 0:
            continue  # Skip - no budget remaining
        
        eligible_campaigns.append(campaign)
    
    return eligible_campaigns


# ============================================
# Discount Calculation
# ============================================

def calculate_discount_amount(campaign: Campaign, value: float) -> float:
    """
    Calculate the discount amount for a given value.
    
    The discount is calculated based on the campaign's discount configuration,
    then capped by various limits:
    1. max_discount_amount (if set)
    2. Remaining campaign budget
    3. The original value (can't discount more than the value)
    
    Args:
        campaign: Campaign containing discount configuration
        value: Value to calculate discount for (cart value or delivery charge)
        
    Returns:
        float: Calculated discount amount, rounded to 2 decimal places
    """
    discount = 0.0
    
    # Calculate base discount based on type
    if campaign.discount_percentage:
        # Percentage discount: value * (percentage / 100)
        discount = value * (campaign.discount_percentage / 100)
    elif campaign.discount_flat:
        # Flat discount: fixed amount
        discount = campaign.discount_flat
    
    # Cap 1: Apply max discount cap if set
    if campaign.max_discount_amount and discount > campaign.max_discount_amount:
        discount = campaign.max_discount_amount
    
    # Cap 2: Ensure discount doesn't exceed remaining campaign budget
    remaining_budget = campaign.total_budget - campaign.used_budget
    if discount > remaining_budget:
        discount = remaining_budget
    
    # Cap 3: Ensure discount doesn't exceed the value being discounted
    if discount > value:
        discount = value
    
    # Round to 2 decimal places for currency
    return round(discount, 2)
