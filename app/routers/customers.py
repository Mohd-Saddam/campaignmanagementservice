from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import CustomerCreate, CustomerResponse
from app import crud
from app.logger import get_logger

# Get logger instance
logger = get_logger(__name__)

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("/", response_model=CustomerResponse, status_code=201)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer."""
    logger.info(f"Attempting to create customer: {customer.email}")
    
    # Check if customer with email already exists
    existing = crud.get_customer_by_email(db, customer.email)
    if existing:
        logger.log_validation_error(
            entity="customer",
            field="email",
            value=customer.email,
            reason="Email already registered"
        )
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_customer = crud.create_customer(db, customer)
    return new_customer


@router.get("/", response_model=List[CustomerResponse])
def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all customers with pagination."""
    return crud.get_customers(db, skip=skip, limit=limit)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Get a specific customer by ID."""
    customer = crud.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
