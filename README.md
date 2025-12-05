# Campaign Management Service

A FastAPI-based discount campaign management system for e-commerce platforms.

## Features

- **Campaign CRUD Operations**: Create, read, update, and delete discount campaigns
- **Discount Types**: Support for cart-level and delivery-level discounts
- **Budget Control**: Set total budget limits for campaigns
- **Time-based Campaigns**: Run campaigns for specific date ranges
- **Usage Limits**: Restrict discount usage per customer per day
- **Targeted Campaigns**: Target specific customer segments
- **Discount Calculation**: Automatic calculation of applicable discounts

## Project Structure

```
task_mi/
├── app/
│   ├── __init__.py          # App package initializer
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database configuration and session
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic validation schemas
│   ├── crud.py              # Database CRUD operations
│   └── routers/
│       ├── __init__.py      # Routers package initializer
│       ├── campaigns.py     # Campaign API endpoints
│       ├── customers.py     # Customer API endpoints
│       └── discounts.py     # Discount API endpoints
├── alembic/                 # Database migrations
│   ├── env.py               # Alembic environment config
│   └── versions/            # Migration files
├── tests/
│   ├── __init__.py
│   └── test_api.py          # Unit and integration tests
├── .env                     # Environment variables (create this)
├── .env.example             # Example environment file
├── alembic.ini              # Alembic configuration
├── Dockerfile               # Docker container config
├── docker-compose.yml       # Docker compose config
├── requirements.txt         # Python dependencies
└── README.md
```

---

## Setup Instructions

### Prerequisites

- Python 3.10+
- PostgreSQL database (or use Neon, Supabase, etc.)
- pip (Python package manager)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd task_mi
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
DATABASE_URL=postgresql://username:password@host:port/database?sslmode=require
```

### 5. Run Database Migrations

```bash
# Initialize alembic (skip if alembic folder exists)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
```

### 6. Start the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 7. Access the API

- **API Base URL**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Using Docker Only

```bash
# Build image
docker build -t campaign-api .

# Run container
docker run -d -p 8000:8000 --env-file .env --name campaign-api campaign-api
```

---

## API Testing Guide

### Using Swagger UI (Recommended)

1. Open http://localhost:8000/docs in your browser
2. Click on any endpoint to expand it
3. Click "Try it out" button
4. Fill in the request body/parameters
5. Click "Execute" to send the request

### Using cURL

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Create Customer
```bash
curl -X POST http://localhost:8000/api/v1/customers/ \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "name": "John Doe"}'
```

#### Create Campaign
```bash
curl -X POST http://localhost:8000/api/v1/campaigns/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Summer Sale",
    "description": "20% off on all items",
    "discount_type": "cart",
    "discount_percentage": 20,
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-12-31T23:59:59",
    "total_budget": 10000,
    "max_usage_per_customer_per_day": 2,
    "min_cart_value": 100,
    "max_discount_amount": 500,
    "is_targeted": false
  }'
```

#### Get Available Discounts
```bash
curl -X POST http://localhost:8000/api/v1/discounts/available \
  -H "Content-Type: application/json" \
  -d '{"customer_id": 1, "cart_value": 500, "delivery_charge": 50}'
```

#### Apply Discount
```bash
curl -X POST http://localhost:8000/api/v1/discounts/apply \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": 1, "customer_id": 1, "cart_value": 500}'
```

### Using Postman

1. Import the following endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Detailed health check |
| POST | `/api/v1/customers/` | Create customer |
| GET | `/api/v1/customers/` | List all customers |
| GET | `/api/v1/customers/{id}` | Get customer by ID |
| POST | `/api/v1/campaigns/` | Create campaign |
| GET | `/api/v1/campaigns/` | List all campaigns |
| GET | `/api/v1/campaigns/{id}` | Get campaign by ID |
| PUT | `/api/v1/campaigns/{id}` | Update campaign |
| DELETE | `/api/v1/campaigns/{id}` | Delete campaign |
| POST | `/api/v1/discounts/available` | Get available discounts |
| POST | `/api/v1/discounts/apply` | Apply discount |
| GET | `/api/v1/discounts/usage/{customer_id}` | Get usage history |

### Using Python requests

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Create customer
response = requests.post(f"{BASE_URL}/customers/", json={
    "email": "test@example.com",
    "name": "Test User"
})
customer = response.json()
print(f"Created customer: {customer}")

# Create campaign
response = requests.post(f"{BASE_URL}/campaigns/", json={
    "name": "Flash Sale",
    "discount_type": "cart",
    "discount_percentage": 15,
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-12-31T23:59:59",
    "total_budget": 5000,
    "max_usage_per_customer_per_day": 1,
    "min_cart_value": 50,
    "is_targeted": False
})
campaign = response.json()
print(f"Created campaign: {campaign}")

# Get available discounts
response = requests.post(f"{BASE_URL}/discounts/available", json={
    "customer_id": customer["id"],
    "cart_value": 200,
    "delivery_charge": 30
})
discounts = response.json()
print(f"Available discounts: {discounts}")
```

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app

# Run specific test class
pytest tests/test_api.py::TestCampaignEndpoints -v
```

---

## API Endpoints Reference

### Customers

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/customers/` | Create a new customer |
| GET | `/api/v1/customers/` | Get all customers |
| GET | `/api/v1/customers/{id}` | Get customer by ID |

### Campaigns

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/campaigns/` | Create a new campaign |
| GET | `/api/v1/campaigns/` | Get all campaigns (supports filters) |
| GET | `/api/v1/campaigns/{id}` | Get campaign by ID |
| PUT | `/api/v1/campaigns/{id}` | Update a campaign |
| DELETE | `/api/v1/campaigns/{id}` | Delete a campaign |
| PATCH | `/api/v1/campaigns/{id}/status` | Update campaign status |

### Discounts

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/discounts/available` | Get available discounts for cart |
| POST | `/api/v1/discounts/apply` | Apply discount to transaction |
| GET | `/api/v1/discounts/usage/{customer_id}` | Get customer usage history |

---

## Business Rules

### Campaign Constraints
1. **Date Range**: Campaigns are only active between `start_date` and `end_date`
2. **Budget Limit**: Campaign becomes inactive when `used_budget >= total_budget`
3. **Daily Usage**: Each customer is limited to `max_usage_per_customer_per_day` transactions
4. **Minimum Cart Value**: Discount only applies if `cart_value >= min_cart_value`
5. **Maximum Discount**: Discount is capped at `max_discount_amount` if specified

### Discount Calculation
1. **Percentage discount**: `value × (discount_percentage / 100)`
2. **Flat discount**: Fixed `discount_flat` amount
3. Final discount is the **minimum** of:
   - Calculated discount
   - `max_discount_amount` (if set)
   - Remaining campaign budget
   - Original value (cannot exceed the value being discounted)

### Targeted Campaigns
- When `is_targeted = true`, only customers in `target_customer_ids` can use the discount
- Non-targeted campaigns are available to all customers

---

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (Neon)
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Validation**: Pydantic
- **Testing**: Pytest + HTTPx
- **Containerization**: Docker
- **Rate Limiting**: SlowAPI

---

## Security Features

### Rate Limiting
API endpoints are protected with rate limiting to prevent abuse:

| Endpoint Type | Rate Limit |
|---------------|------------|
| Health Check | 100/minute |
| Get Discounts | 60/minute |
| Apply Discount | 30/minute |

### Security Headers
All responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`

### Input Validation
- All inputs are validated using Pydantic schemas
- SQL injection protection via SQLAlchemy ORM
- Type checking and constraints enforced at API level

---

## Performance Features

### Database Connection Pooling
- **Pool Size**: 5 persistent connections
- **Max Overflow**: 10 additional connections during peak load
- **Pool Pre-ping**: Validates connections before use
- **Pool Recycle**: Refreshes connections every 30 minutes

### Request Processing
- Async-capable endpoints
- Request timing logged in `X-Process-Time` header
- Efficient database queries with proper indexing

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host/db` |

---

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify `DATABASE_URL` is set correctly in `.env`
   - Ensure PostgreSQL server is running
   - Check network connectivity to database host

2. **Rate Limit Exceeded (429 Error)**
   - Wait for the rate limit window to reset
   - Consider implementing request queuing for high-traffic scenarios

3. **Migration Errors**
   - Ensure `alembic/env.py` imports models correctly
   - Check database permissions

---

## License

MIT License
