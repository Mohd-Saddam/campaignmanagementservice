"""
Pydantic Schemas Module

This module defines all Pydantic models for request/response validation.
Schemas ensure data integrity and provide automatic API documentation.
"""

from pydantic import BaseModel, Field, field_validator, EmailStr  # Pydantic base and validators
from datetime import datetime  # Date and time handling
from typing import Optional, List  # Type hints for optional fields and lists
from enum import Enum  # Python enumeration support


class DiscountType(str, Enum):
    """
    Enumeration for discount types in API requests/responses.
    
    CART: Discount applies to the overall cart value
    DELIVERY: Discount applies to delivery charges only
    """
    CART = "cart"
    DELIVERY = "delivery"


class CampaignStatus(str, Enum):
    """
    Enumeration for campaign status in API requests/responses.
    
    ACTIVE: Campaign is currently running
    INACTIVE: Campaign has been manually deactivated
    EXPIRED: Campaign end date has passed
    BUDGET_EXHAUSTED: Campaign budget has been fully used
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    BUDGET_EXHAUSTED = "budget_exhausted"


# ============================================
# Customer Schemas
# ============================================

class CustomerBase(BaseModel):
    """Base schema for customer with common fields."""
    email: EmailStr  # Customer email address (validated)
    name: str = Field(..., min_length=1, max_length=100)  # Customer display name


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer (inherits from CustomerBase)."""
    pass


class CustomerResponse(CustomerBase):
    """
    Schema for customer response with all fields.
    Includes database-generated fields like id and created_at.
    """
    id: int  # Database ID
    created_at: datetime  # When customer was created

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models


# ============================================
# Campaign Schemas
# ============================================

class CampaignBase(BaseModel):
    """
    Base schema for campaign with all configurable fields.
    Used as base for create and update schemas.
    """
    # Campaign name - required, 1-255 characters
    name: str = Field(..., min_length=1, max_length=255)
    # Optional description
    description: Optional[str] = None
    # Type of discount: 'cart' or 'delivery'
    discount_type: DiscountType
    # Percentage discount (0-100), optional
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    # Flat discount amount, optional
    discount_flat: Optional[float] = Field(None, ge=0)
    # Campaign start date
    start_date: datetime
    # Campaign end date (must be after start_date)
    end_date: datetime
    # Total budget for the campaign (must be > 0)
    total_budget: float = Field(..., gt=0)
    # Max uses per customer per day (default: 1)
    max_usage_per_customer_per_day: int = Field(default=1, ge=1)
    # Minimum cart value to apply discount (default: 0)
    min_cart_value: float = Field(default=0.0, ge=0)
    # Maximum discount cap (optional)
    max_discount_amount: Optional[float] = Field(None, ge=0)
    # Whether campaign is targeted to specific customers
    is_targeted: bool = False
    # List of customer IDs for targeted campaigns
    target_customer_ids: Optional[List[int]] = None

    @field_validator('end_date')
    @classmethod
    def end_date_must_be_after_start_date(cls, v, info):
        """Validate that end_date is after start_date."""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

    @field_validator('discount_percentage', 'discount_flat')
    @classmethod
    def at_least_one_discount(cls, v, info):
        """Validator placeholder - actual validation done in route."""
        return v


class CampaignCreate(CampaignBase):
    """Schema for creating a new campaign (inherits all fields from CampaignBase)."""
    pass


class CampaignUpdate(BaseModel):
    """
    Schema for updating a campaign.
    All fields are optional - only provided fields will be updated.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    discount_type: Optional[DiscountType] = None
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    discount_flat: Optional[float] = Field(None, ge=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_budget: Optional[float] = Field(None, gt=0)
    max_usage_per_customer_per_day: Optional[int] = Field(None, ge=1)
    min_cart_value: Optional[float] = Field(None, ge=0)
    max_discount_amount: Optional[float] = Field(None, ge=0)
    is_targeted: Optional[bool] = None
    target_customer_ids: Optional[List[int]] = None
    status: Optional[CampaignStatus] = None


class CampaignResponse(BaseModel):
    """
    Schema for campaign response with all fields.
    Includes database-generated fields like id, used_budget, timestamps.
    """
    id: int  # Database ID
    name: str  # Campaign name
    description: Optional[str]  # Optional description
    discount_type: DiscountType  # 'cart' or 'delivery'
    discount_percentage: Optional[float]  # Percentage discount
    discount_flat: Optional[float]  # Flat discount amount
    start_date: datetime  # Campaign start
    end_date: datetime  # Campaign end
    total_budget: float  # Total budget
    used_budget: float  # Amount already used
    max_usage_per_customer_per_day: int  # Daily limit per customer
    min_cart_value: float  # Minimum cart value
    max_discount_amount: Optional[float]  # Maximum discount cap
    is_targeted: bool  # Whether targeted to specific customers
    status: CampaignStatus  # Current status
    created_at: datetime  # Creation timestamp
    updated_at: datetime  # Last update timestamp
    target_customer_ids: Optional[List[int]] = None  # List of targeted customer IDs
    targeted_customers: Optional[List[CustomerResponse]] = None  # Full customer details

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models


# ============================================
# Cart Parameters & Discount Response Schemas
# ============================================

class CartParameters(BaseModel):
    """
    Schema for cart parameters when fetching available discounts.
    Sent by client to check what discounts are available.
    """
    customer_id: int  # ID of the customer
    cart_value: float = Field(..., gt=0)  # Total cart value (must be > 0)
    delivery_charge: float = Field(default=0.0, ge=0)  # Delivery charge amount


class AvailableDiscount(BaseModel):
    """
    Schema for a single available discount.
    Represents one discount option the customer can use.
    """
    campaign_id: int  # ID of the campaign
    campaign_name: str  # Name of the campaign
    discount_type: DiscountType  # 'cart' or 'delivery'
    discount_amount: float  # Amount of discount
    original_value: float  # Original value before discount
    final_value: float  # Value after discount applied
    message: str  # User-friendly message about the discount


class AvailableDiscountsResponse(BaseModel):
    """
    Schema for response containing all available discounts.
    Separates cart and delivery discounts for easy processing.
    """
    cart_discounts: List[AvailableDiscount]  # All available cart discounts
    delivery_discounts: List[AvailableDiscount]  # All available delivery discounts
    best_cart_discount: Optional[AvailableDiscount] = None  # Best cart discount (highest value)
    best_delivery_discount: Optional[AvailableDiscount] = None  # Best delivery discount


# ============================================
# Discount Usage Schemas
# ============================================

class DiscountUsageCreate(BaseModel):
    """Schema for applying a discount to a transaction."""
    campaign_id: int  # ID of the campaign to use
    customer_id: int  # ID of the customer using the discount
    cart_value: float = Field(..., gt=0)  # Cart value for discount calculation
    delivery_charge: float = Field(default=0.0, ge=0)  # Delivery charge for delivery discounts


class DiscountUsageResponse(BaseModel):
    """
    Schema for discount usage response.
    Returned after successfully applying a discount.
    """
    id: int  # Usage record ID
    campaign_id: int  # Campaign that was used
    customer_id: int  # Customer who used it
    discount_amount: float  # Amount of discount applied
    cart_value: float  # Cart value at time of use
    used_at: datetime  # When the discount was used

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models


class EnhancedDiscountUsageResponse(BaseModel):
    """
    Enhanced schema for discount usage response with campaign and customer details.
    """
    id: int
    campaign_id: int
    customer_id: int
    discount_amount: float
    original_amount: float
    final_amount: float
    used_at: datetime
    campaign_name: str
    discount_type: DiscountType
    customer_name: str
    customer_email: str

    class Config:
        from_attributes = True


# ============================================
# Generic API Response Schema
# ============================================

class APIResponse(BaseModel):
    """
    Generic API response wrapper schema.
    Can be used for standardized API responses.
    """
    success: bool  # Whether the operation was successful
    message: str  # Human-readable message
    data: Optional[dict] = None  # Optional response data
