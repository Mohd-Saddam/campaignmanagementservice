# Campaign Management Service

[![FastAPI](https://img.shields.io/badge/FastAPI-0.123.9-009688.svg?style=flat&logo=FastAPI)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat&logo=python)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791.svg?style=flat&logo=postgresql)](https://neon.tech)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A production-ready FastAPI-based discount campaign management system for e-commerce platforms with comprehensive discount strategies, budget controls, and real-time analytics.

## Live Deployment

**API URL**: [https://campaignmanagementservice.onrender.com](https://campaignmanagementservice.onrender.com)

**API Documentation**: [https://campaignmanagementservice.onrender.com/docs](https://campaignmanagementservice.onrender.com/docs)

## Features

### Core Functionality
- **Campaign CRUD Operations**: Complete lifecycle management of discount campaigns
- **Dual Discount Types**: 
  - **Cart Discounts**: Percentage or flat discounts on cart value
  - **Delivery Discounts**: Percentage or flat discounts on delivery charges
- **Smart Budget Control**: Real-time budget tracking with automatic campaign deactivation
- **Time-based Campaigns**: Schedule campaigns with precise start and end dates
- **Usage Limits**: Prevent abuse with per-customer daily usage restrictions
- **Targeted Campaigns**: Segment-specific campaigns for premium customers
- **Intelligent Discount Engine**: Automatic selection of best discount for customers

### Enhanced Features
- **Enhanced Response Schemas**: Detailed responses with campaign names, customer details, and financial breakdowns
- **Email Validation**: Built-in email validation using Pydantic's EmailStr
- **Security Features**: Rate limiting, security headers, and SQL injection protection
- **Performance Optimized**: Database connection pooling, async operations
- **Comprehensive Testing**: 24 automated tests with 100% pass rate
- **Usage Analytics**: Track discount usage history per customer
- **Best Discount Finder**: Automatically identifies the best available discount for each transaction

## Project Structure

```
task_mi/
├── app/
│   ├── __init__.py          # App package initializer
│   ├── main.py              # FastAPI app with security & rate limiting
│   ├── database.py          # PostgreSQL config with connection pooling
│   ├── models.py            # SQLAlchemy ORM models (Customer, Campaign, DiscountUsage)
│   ├── schemas.py           # Pydantic schemas with enhanced responses
│   ├── crud.py              # Database operations & discount logic
│   └── routers/
│       ├── __init__.py      # Routers package initializer
│       ├── campaigns.py     # Campaign endpoints with validation
│       ├── customers.py     # Customer management endpoints
│       └── discounts.py     # Discount availability & application
├── alembic/                 # Database migrations
│   ├── env.py               # Alembic environment config
│   └── versions/            # Migration version files
├── tests/
│   ├── __init__.py
│   └── test_api.py          # 24 comprehensive tests
├── test_all_apis.ps1        # PowerShell test automation script
├── .env                     # Environment variables (create from .env.example)
├── .env.example             # Example environment configuration
├── alembic.ini              # Alembic configuration
├── requirements.txt         # Python dependencies (latest versions)
└── README.md                # This file
```

---

## Quick Start

### Prerequisites

- **Python**: 3.10 or higher
- **PostgreSQL Database**: Use [Neon](https://neon.tech), [Supabase](https://supabase.com), or local PostgreSQL
- **Git**: For cloning the repository
- **pip**: Python package manager (comes with Python)

### 1. Clone the Repository

```bash
git clone https://github.com/Mohd-Saddam/campaignmanagementservice.git
cd task_mi
```

### 2. Create Virtual Environment

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Windows (CMD)
python -m venv .venv
.venv\Scripts\activate.bat

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Latest Package Versions** (as of Dec 2025):
- FastAPI: 0.123.9
- Pydantic: 2.12.5
- SQLAlchemy: 2.0.36
- Uvicorn: 0.38.0
- Alembic: 1.14.1

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# PostgreSQL Database URL
DATABASE_URL=postgresql://username:password@host:5432/database?sslmode=require

# Example (Neon)
# DATABASE_URL=postgresql://user:pass@ep-xyz.us-east-2.aws.neon.tech/campaigndb?sslmode=require
```

### 5. Run Database Migrations

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations to database
alembic upgrade head
```

### 6. Start the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 7. Access the API

- **API Base URL**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 8. View Logs

Logs are automatically created in the `logs/` directory:

```bash
# View all application logs
cat logs/campaign_service.log

# View error logs only
cat logs/errors.log

# View API request logs (JSON format)
cat logs/api_requests.log

# Follow logs in real-time (Windows PowerShell)
Get-Content logs/campaign_service.log -Wait -Tail 50

# Follow logs in real-time (Linux/Mac)
tail -f logs/campaign_service.log
```

**Log Files**:
- `campaign_service.log` - All application logs with detailed context
- `errors.log` - Error and critical logs only
- `api_requests.log` - API requests in JSON format for analytics

---

## Logging System

### Centralized Logger

The application uses a singleton logger class (`CampaignLogger`) that provides:

- **Structured Logging**: All logs include timestamp, module, level, and context
- **Multiple Outputs**: Console (stdout), file logs, and error-specific logs
- **Dynamic Access**: Logger can be accessed from any module
- **Specialized Methods**: Dedicated logging methods for different operations

### Logger Methods

```python
from app.logger import get_logger

logger = get_logger(__name__)

# Basic logging
logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)

# Customer operations logging
logger.log_customer_operation(
    operation="create",
    customer_id=1,
    email="user@example.com",
    success=True
)

# Campaign operations logging
logger.log_campaign_operation(
    operation="create",
    campaign_id=1,
    campaign_name="Black Friday Sale",
    campaign_type="cart",
    success=True
)

# Discount operations logging
logger.log_discount_operation(
    operation="apply",
    campaign_id=1,
    customer_id=5,
    discount_amount=150.0,
    cart_value=500.0,
    success=True
)

# Validation error logging
logger.log_validation_error(
    entity="customer",
    field="email",
    value="invalid",
    reason="Email already exists"
)

# Business rule violation logging
logger.log_business_rule_violation(
    rule="daily_usage_limit",
    details="Customer exceeded 2 transactions per day"
)
```

### Log Format

**Console Output** (Simple):
```
2025-12-06 10:30:15 - INFO - Campaign created successfully
```

**File Output** (Detailed):
```
2025-12-06 10:30:15 - campaign_service.routers.campaigns - INFO - [campaigns.py:85] - Campaign created successfully: ID=1, Name=Black Friday Sale
```

**API Request Log** (JSON):
```json
{
  "timestamp": "2025-12-06T10:30:15.123456",
  "request_id": 140234567,
  "method": "POST",
  "path": "/api/v1/campaigns/",
  "status_code": 201,
  "process_time": 0.234,
  "client_ip": "127.0.0.1",
  "level": "INFO"
}
```

### What Gets Logged

1. **Application Startup**: Service initialization and configuration
2. **API Requests**: All incoming requests with method, path, status, timing
3. **Customer Operations**: Create, read, update operations with results
4. **Campaign Operations**: CRUD operations with campaign details
5. **Discount Operations**: Availability checks, applications, calculations
6. **Validation Errors**: All input validation failures with reasons
7. **Business Rules**: Violations of business logic constraints
8. **Database Operations**: Critical database operations and errors
9. **Errors & Exceptions**: Full stack traces for debugging

---

## Testing

### Automated Tests

```bash
# Run all 24 tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html

# Run specific test class
pytest tests/test_api.py::TestCampaignEndpoints -v
```

**Test Results**: All 24 tests passing

### PowerShell Test Script

Run comprehensive API tests:

```powershell
# Execute all 20 API endpoint tests
.\test_all_apis.ps1
```

**Test Coverage**:
- Customer CRUD operations
- Campaign CRUD operations  
- Discount availability checks
- Discount application
- Usage history tracking
- Validation & error handling
- Targeted campaigns
- Budget constraints
- Daily usage limits

---

## API Endpoints Reference

### Health & Status

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| GET | `/` | Root endpoint | 100/min |
| GET | `/health` | Health check with DB status | 100/min |

### Customers

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/customers/` | Create new customer | No |
| GET | `/api/v1/customers/` | List all customers | No |
| GET | `/api/v1/customers/{id}` | Get customer by ID | No |

**Request Example**:
```json
{
  "email": "john.doe@example.com",
  "name": "John Doe"
}
```

**Response Example**:
```json
{
  "id": 1,
  "email": "john.doe@example.com",
  "name": "John Doe",
  "created_at": "2025-12-06T10:30:00"
}
```

### Campaigns

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/campaigns/` | Create campaign | No |
| GET | `/api/v1/campaigns/` | List campaigns (with filters) | No |
| GET | `/api/v1/campaigns/{id}` | Get campaign details | No |
| PUT | `/api/v1/campaigns/{id}` | Update campaign | No |
| DELETE | `/api/v1/campaigns/{id}` | Delete campaign | No |

**Query Parameters** (GET all):
- `discount_type`: Filter by "cart" or "delivery"
- `status`: Filter by "active" or "inactive"
- `is_targeted`: Filter targeted campaigns (true/false)

**Request Example** (Create Campaign):
```json
{
  "name": "Black Friday Sale",
  "description": "Biggest sale of the year",
  "discount_type": "cart",
  "discount_percentage": 25,
  "start_date": "2025-11-24T00:00:00",
  "end_date": "2025-11-30T23:59:59",
  "total_budget": 50000,
  "max_usage_per_customer_per_day": 3,
  "min_cart_value": 100,
  "max_discount_amount": 1000,
  "is_targeted": false
}
```

**Response Example** (Enhanced with Targeted Customers):
```json
{
  "id": 1,
  "name": "VIP Members Only",
  "discount_type": "cart",
  "discount_percentage": 35.0,
  "status": "active",
  "used_budget": 210.0,
  "total_budget": 30000.0,
  "targeted_customers": [
    {
      "id": 3,
      "email": "john.doe@example.com",
      "name": "John Doe",
      "created_at": "2025-12-06T06:09:38"
    },
    {
      "id": 5,
      "email": "alice@example.com",
      "name": "Alice Johnson",
      "created_at": "2025-12-06T06:11:50"
    }
  ],
  "target_customer_ids": [3, 5]
}
```

### Discounts

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/api/v1/discounts/available` | Get available discounts | 60/min |
| POST | `/api/v1/discounts/apply` | Apply discount | 30/min |
| GET | `/api/v1/discounts/usage/{customer_id}` | Get usage history | 60/min |

**Get Available Discounts** Request:
```json
{
  "customer_id": 5,
  "cart_value": 600,
  "delivery_charge": 80
}
```

**Get Available Discounts** Response:
```json
{
  "cart_discounts": [
    {
      "campaign_id": 11,
      "campaign_name": "VIP Members Only",
      "discount_type": "cart",
      "discount_percentage": 35.0,
      "discount_amount": 210.0,
      "final_amount": 390.0,
      "is_best": true
    },
    {
      "campaign_id": 1,
      "campaign_name": "New Year Sale",
      "discount_type": "cart",
      "discount_percentage": 20.0,
      "discount_amount": 120.0,
      "final_amount": 480.0,
      "is_best": false
    }
  ],
  "delivery_discounts": [
    {
      "campaign_id": 2,
      "campaign_name": "Free Delivery Week",
      "discount_type": "delivery",
      "discount_percentage": 50.0,
      "discount_amount": 40.0,
      "final_amount": 40.0,
      "is_best": true
    }
  ],
  "best_cart_discount": {
    "campaign_id": 11,
    "discount_amount": 210.0,
    "savings": "35% off (₹210.00)"
  },
  "best_delivery_discount": {
    "campaign_id": 2,
    "discount_amount": 40.0,
    "savings": "50% off (₹40.00)"
  }
}
```

**Apply Discount** Request:
```json
{
  "campaign_id": 11,
  "customer_id": 5,
  "cart_value": 600,
  "delivery_charge": 80
}
```

**Apply Discount** Response (Enhanced):
```json
{
  "id": 7,
  "campaign_id": 11,
  "customer_id": 5,
  "discount_amount": 210.0,
  "original_amount": 600.0,
  "final_amount": 390.0,
  "used_at": "2025-12-06T06:28:08",
  "campaign_name": "VIP Members Only",
  "discount_type": "cart",
  "customer_name": "Alice Johnson",
  "customer_email": "alice@example.com"
}
```

**Usage History** Response:
```json
{
  "Count": 2,
  "value": [
    {
      "id": 7,
      "campaign_name": "VIP Members Only",
      "discount_type": "cart",
      "discount_amount": 210.0,
      "original_amount": 600.0,
      "final_amount": 390.0,
      "customer_name": "Alice Johnson",
      "customer_email": "alice@example.com",
      "used_at": "2025-12-06T06:28:08"
    },
    {
      "id": 8,
      "campaign_name": "Free Delivery Week",
      "discount_type": "delivery",
      "discount_amount": 40.0,
      "original_amount": 80.0,
      "final_amount": 40.0,
      "customer_name": "Alice Johnson",
      "customer_email": "alice@example.com",
      "used_at": "2025-12-06T06:30:03"
    }
  ]
}
```

---

## Business Rules & Logic

### Campaign Eligibility Criteria

A campaign is eligible if ALL conditions are met:

1. **Active Status**: Campaign must have `status = "active"`
2. **Date Range**: Current time is between `start_date` and `end_date`
3. **Budget Available**: `used_budget < total_budget`
4. **Minimum Cart Value**: `cart_value >= min_cart_value`
5. **Customer Targeting**: 
   - If `is_targeted = false`: Available to all customers
   - If `is_targeted = true`: Customer ID must be in `target_customer_ids`
6. **Daily Usage Limit**: Customer hasn't exceeded `max_usage_per_customer_per_day` for today

### Discount Calculation Formula

#### For Percentage Discounts:
```
calculated_discount = value × (discount_percentage / 100)
```

#### For Flat Discounts:
```
calculated_discount = discount_flat
```

#### Final Discount (capped by):
```
final_discount = MIN(
    calculated_discount,
    max_discount_amount (if set),
    remaining_budget,
    original_value
)
```

### Campaign Auto-Deactivation

Campaigns are automatically marked as `inactive` when:
- `used_budget >= total_budget` (Budget exhausted)
- Current time > `end_date` (Campaign expired)

### Discount Types

| Type | Applies To | Example Use Case |
|------|-----------|------------------|
| **cart** | Cart total value | "20% off on orders above ₹500" |
| **delivery** | Delivery charges | "Free delivery on all orders" |

### Validation Rules

#### Customer Creation:
- Email must be valid format (validated with EmailStr)
- Name is required
- Email must be unique

#### Campaign Creation:
- `start_date` must be before `end_date`
- `total_budget` must be > 0
- If `is_targeted = true`, `target_customer_ids` must contain valid customer IDs
- Cannot specify both `discount_percentage` and `discount_flat`
- `discount_percentage` must be between 0 and 100
- `max_usage_per_customer_per_day` must be >= 1

#### Discount Application:
- Campaign must be eligible
- `cart_value` must meet `min_cart_value`
- Customer must not have exceeded daily usage limit
- Sufficient budget must remain in campaign

---

## Technology Stack

### Backend Framework
- **FastAPI** `0.123.9` - Modern, fast (high-performance) web framework
- **Uvicorn** `0.38.0` - Lightning-fast ASGI server
- **Pydantic** `2.12.5` - Data validation using Python type hints

### Database
- **PostgreSQL** - Production-grade relational database
- **Neon** - Serverless PostgreSQL platform (cloud hosting)
- **SQLAlchemy** `2.0.36` - SQL toolkit and ORM
- **Alembic** `1.14.1` - Database migration tool

### Security & Performance
- **SlowAPI** `0.1.9` - Rate limiting middleware
- **email-validator** `2.3.0` - Email validation
- **Connection Pooling** - PostgreSQL connection pool (size: 5, overflow: 10)
- **Security Headers** - HSTS, X-Frame-Options, CSP

### Testing
- **Pytest** `8.3.4` - Testing framework
- **HTTPx** `0.28.1` - Async HTTP client for testing
- **Coverage.py** - Code coverage measurement

### Development Tools
- **Python** `3.10+` - Programming language
- **Git** - Version control
- **PowerShell** - Test automation scripts

---

## Security Features

### Rate Limiting Protection

Prevents API abuse with endpoint-specific rate limits:

| Endpoint | Rate Limit | Scope |
|----------|------------|-------|
| Health Check (`/`, `/health`) | 100 requests/minute | Per IP |
| Get Discounts (`/discounts/available`) | 60 requests/minute | Per IP |
| Apply Discount (`/discounts/apply`) | 30 requests/minute | Per IP |
| All Other Endpoints | 100 requests/minute | Per IP |

**Error Response** (429 Too Many Requests):
```json
{
  "error": "Rate limit exceeded: 30 per 1 minute"
}
```

### Security Headers

All API responses include security headers:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME-type sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Enable XSS filter |
| `Strict-Transport-Security` | `max-age=31536000` | Force HTTPS |

### Input Validation & Sanitization

- **Pydantic Schemas**: All inputs validated with type checking
- **SQLAlchemy ORM**: Protection against SQL injection
- **Email Validation**: RFC-compliant email validation
- **Constraint Enforcement**: Database-level constraints
- **Error Handling**: Graceful error messages (no stack traces in production)

---

## Performance Optimizations

### Database Connection Pooling

Optimized PostgreSQL connection management:

```python
# Configuration
Pool Size: 5 connections (persistent)
Max Overflow: 10 connections (during peak load)
Pool Pre-ping: True (validates connections before use)
Pool Recycle: 1800 seconds (30 minutes)
```

**Benefits**:
- Faster query execution (reuses connections)
- Handles concurrent requests efficiently
- Auto-recovery from stale connections
- Scales to handle traffic spikes

### Async Operations

- Non-blocking I/O operations
- Concurrent request handling
- Process time tracking in `X-Process-Time` header

### Database Indexing

Optimized queries with indexes on:
- `customer.email` (unique)
- `campaign.status`
- `campaign.discount_type`
- `discount_usage.customer_id`
- `discount_usage.campaign_id`



## API Usage Examples

### Example 1: Create VIP Campaign

```bash
curl -X POST "https://campaignmanagementservice.onrender.com/api/v1/campaigns/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "VIP Members Only",
    "description": "Exclusive for premium customers",
    "discount_type": "cart",
    "discount_percentage": 35,
    "start_date": "2025-01-01T00:00:00",
    "end_date": "2025-12-31T23:59:59",
    "total_budget": 30000,
    "max_usage_per_customer_per_day": 10,
    "min_cart_value": 500,
    "max_discount_amount": 2000,
    "is_targeted": true,
    "target_customer_ids": [3, 5]
  }'
```

### Example 2: Check Available Discounts

```bash
curl -X POST "https://campaignmanagementservice.onrender.com/api/v1/discounts/available" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 5,
    "cart_value": 600,
    "delivery_charge": 80
  }'
```

### Example 3: Apply Best Discount

```bash
curl -X POST "https://campaignmanagementservice.onrender.com/api/v1/discounts/apply" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": 11,
    "customer_id": 5,
    "cart_value": 600
  }'
```

### Example 4: View Usage Analytics

```bash
curl -X GET "https://campaignmanagementservice.onrender.com/api/v1/discounts/usage/5"
```

---

## Troubleshooting

### Common Issues & Solutions

#### 1. Database Connection Error

**Error**: `could not connect to server`

**Solutions**:
- Verify `DATABASE_URL` in `.env` file
- Check PostgreSQL server is running
- Ensure network allows connections to database host
- For Render: Use **Internal Database URL**, not External
- Verify SSL mode: `?sslmode=require` at end of URL

#### 2. Rate Limit Exceeded (429 Error)

**Error**: `Rate limit exceeded: 30 per 1 minute`

**Solutions**:
- Wait 60 seconds for rate limit to reset
- Implement request queuing in your client
- Contact admin to increase limits for your IP

#### 3. Migration Errors

**Error**: `Target database is not up to date`

**Solutions**:
```bash
# Check migration status
alembic current

# Apply pending migrations
alembic upgrade head

# If issues persist, reset migrations
alembic downgrade base
alembic upgrade head
```

#### 4. Import Errors

**Error**: `ModuleNotFoundError: No module named 'app'`

**Solutions**:
```bash
# Ensure virtual environment is activated
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Linux/Mac

# Reinstall dependencies
pip install -r requirements.txt
```

#### 5. Validation Errors

**Error**: `Target customer with ID 9999 not found`

**Solutions**:
- Create customers before creating targeted campaigns
- Use valid customer IDs from `/api/v1/customers/`
- Check customer exists: `GET /api/v1/customers/{id}`

#### 6. Empty Usage History

**Error**: `No discount usage history found for customer`

**Solutions**:
- This is normal if customer hasn't used any discounts yet
- Apply a discount first using `/api/v1/discounts/apply`
- Verify correct customer ID

### Debug Mode

Enable debug logging:

```python
# app/main.py
import logging

logging.basicConfig(level=logging.DEBUG)
```

View detailed logs:
```bash
uvicorn app.main:app --reload --log-level debug
```

---

## License

MIT License - see [LICENSE](LICENSE) file for details

---

## Author

**Mohd Saddam**
- GitHub: [@Mohd-Saddam](https://github.com/Mohd-Saddam)
- Repository: [campaignmanagementservice](https://github.com/Mohd-Saddam/campaignmanagementservice)

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact: [GitHub Profile](https://github.com/Mohd-Saddam)



## Version History

### v1.0.0 (December 2025)
- Complete campaign management system
- Cart and delivery discount support
- Enhanced response schemas with customer details
- Email validation with EmailStr
- Rate limiting and security headers
- Database connection pooling
- Comprehensive test coverage (24 tests)
- Deployed to Render
- PowerShell test automation script

---

**Star this repository if you find it helpful!**

Made with FastAPI
