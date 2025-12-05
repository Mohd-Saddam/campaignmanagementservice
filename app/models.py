"""
Database Models Module

This module defines all SQLAlchemy ORM models for the campaign management system.
Models represent database tables and their relationships.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, Table  # SQLAlchemy column types
from sqlalchemy.orm import relationship  # Define relationships between models
from datetime import datetime  # Date and time handling
import enum  # Python enumeration support

from app.database import Base  # Base class for all models


class DiscountType(str, enum.Enum):
    """
    Enumeration for discount types.
    
    CART: Discount applies to the overall cart value
    DELIVERY: Discount applies to delivery charges only
    """
    CART = "cart"
    DELIVERY = "delivery"


class CampaignStatus(str, enum.Enum):
    """
    Enumeration for campaign status.
    
    ACTIVE: Campaign is currently running and accepting discounts
    INACTIVE: Campaign has been manually deactivated
    EXPIRED: Campaign end date has passed
    BUDGET_EXHAUSTED: Campaign budget has been fully used
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    BUDGET_EXHAUSTED = "budget_exhausted"


# Association table for many-to-many relationship between campaigns and customers
# Used for targeted campaigns that only apply to specific customers
campaign_customers = Table(
    "campaign_customers",  # Table name in database
    Base.metadata,  # SQLAlchemy metadata
    Column("campaign_id", Integer, ForeignKey("campaigns.id"), primary_key=True),  # Foreign key to campaigns
    Column("customer_id", Integer, ForeignKey("customers.id"), primary_key=True)  # Foreign key to customers
)


class Customer(Base):
    """
    Customer Model
    
    Represents a customer in the system who can use discount campaigns.
    Customers can be targeted by specific campaigns.
    """
    __tablename__ = "customers"  # Database table name

    # Primary key - unique identifier for each customer
    id = Column(Integer, primary_key=True, index=True)
    # Customer email - must be unique, indexed for fast lookups
    email = Column(String, unique=True, index=True, nullable=False)
    # Customer display name
    name = Column(String, nullable=False)
    # Timestamp when customer was created
    created_at = Column(DateTime, default=datetime.utcnow)

    # Many-to-many relationship with campaigns (for targeted campaigns)
    targeted_campaigns = relationship(
        "Campaign",  # Related model
        secondary=campaign_customers,  # Junction table
        back_populates="target_customers"  # Reverse relationship name
    )
    
    # One-to-many relationship with discount usage records
    discount_usages = relationship("DiscountUsage", back_populates="customer")


class Campaign(Base):
    """
    Campaign Model
    
    Represents a discount campaign with all its configuration.
    Campaigns can apply to cart or delivery, have budget limits,
    date constraints, and can be targeted to specific customers.
    """
    __tablename__ = "campaigns"  # Database table name

    # Primary key - unique identifier for each campaign
    id = Column(Integer, primary_key=True, index=True)
    # Campaign name for display
    name = Column(String, nullable=False)
    # Optional description of the campaign
    description = Column(String, nullable=True)
    
    # === Discount Configuration ===
    # Type of discount: 'cart' or 'delivery'
    discount_type = Column(Enum(DiscountType), nullable=False)
    # Percentage discount (e.g., 10 means 10% off)
    discount_percentage = Column(Float, nullable=True)
    # Flat discount amount (e.g., 50 means $50 off)
    discount_flat = Column(Float, nullable=True)
    
    # === Campaign Constraints ===
    # Campaign start date - discount not valid before this
    start_date = Column(DateTime, nullable=False)
    # Campaign end date - discount not valid after this (x days constraint)
    end_date = Column(DateTime, nullable=False)
    # Total budget for the campaign - stops when exhausted
    total_budget = Column(Float, nullable=False)
    # Amount of budget already used
    used_budget = Column(Float, default=0.0)
    
    # === Usage Limits ===
    # Maximum times a customer can use this discount per day
    max_usage_per_customer_per_day = Column(Integer, default=1)
    # Minimum cart value required to apply discount
    min_cart_value = Column(Float, default=0.0)
    # Maximum discount amount cap (optional)
    max_discount_amount = Column(Float, nullable=True)
    
    # === Targeting ===
    # If True, only customers in target_customers can use this discount
    is_targeted = Column(Boolean, default=False)
    
    # === Status & Timestamps ===
    # Current status of the campaign
    status = Column(Enum(CampaignStatus), default=CampaignStatus.ACTIVE)
    # When the campaign was created
    created_at = Column(DateTime, default=datetime.utcnow)
    # When the campaign was last updated
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # === Relationships ===
    # Many-to-many relationship with customers (for targeting)
    target_customers = relationship(
        "Customer",  # Related model
        secondary=campaign_customers,  # Junction table
        back_populates="targeted_campaigns"  # Reverse relationship name
    )
    # One-to-many relationship with discount usage records
    discount_usages = relationship("DiscountUsage", back_populates="campaign")


class DiscountUsage(Base):
    """
    Discount Usage Model
    
    Tracks each time a customer uses a discount from a campaign.
    Used to enforce daily usage limits and track budget consumption.
    """
    __tablename__ = "discount_usages"  # Database table name

    # Primary key - unique identifier for each usage record
    id = Column(Integer, primary_key=True, index=True)
    # Foreign key to the campaign that was used
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    # Foreign key to the customer who used the discount
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    # Amount of discount that was applied
    discount_amount = Column(Float, nullable=False)
    # Cart value at the time of discount application
    cart_value = Column(Float, nullable=False)
    # Timestamp when the discount was used
    used_at = Column(DateTime, default=datetime.utcnow)

    # === Relationships ===
    # Link back to the campaign
    campaign = relationship("Campaign", back_populates="discount_usages")
    # Link back to the customer
    customer = relationship("Customer", back_populates="discount_usages")
