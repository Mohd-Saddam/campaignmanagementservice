"""
FastAPI Application Entry Point

This is the main module that initializes and configures the FastAPI application.
It sets up middleware, includes routers, and defines health check endpoints.
"""

from fastapi import FastAPI, Request, Depends  # FastAPI framework
from fastapi.middleware.cors import CORSMiddleware  # CORS middleware for cross-origin requests
from fastapi.responses import JSONResponse  # JSON response for error handling
from slowapi import Limiter, _rate_limit_exceeded_handler  # Rate limiting
from slowapi.util import get_remote_address  # Get client IP address
from slowapi.errors import RateLimitExceeded  # Rate limit exception
from starlette.middleware.base import BaseHTTPMiddleware  # Custom middleware base
from sqlalchemy.orm import Session  # Database session type
from sqlalchemy import text  # SQL text for raw queries
import time  # For request timing
import logging  # Logging support

from app.database import engine, Base, get_db  # Database engine, base model, session dependency
from app.routers import campaigns, customers, discounts  # API route handlers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create all database tables defined in models
# This is useful for development - in production, use Alembic migrations
Base.metadata.create_all(bind=engine)

# Initialize rate limiter - limits requests per IP address
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI application with metadata for API documentation
app = FastAPI(
    title="Campaign Management Service",  # API title shown in docs
    description="""
## Campaign Management API

A comprehensive discount campaign management system for e-commerce platforms.

### Features:
- **Campaign Management**: Create, update, delete, and manage discount campaigns
- **Discount Types**: Support for both cart-level and delivery-level discounts
- **Budget Control**: Set total budget limits for campaigns
- **Time-based Campaigns**: Run campaigns for specific date ranges
- **Usage Limits**: Restrict discount usage per customer per day
- **Targeted Campaigns**: Target specific customer segments

### Key Endpoints:
- `/campaigns/` - CRUD operations for campaigns
- `/customers/` - Customer management
- `/discounts/available` - Get available discounts for a cart
- `/discounts/apply` - Apply a discount to a transaction
    """,
    version="1.0.0",  # API version
    docs_url="/docs",  # Swagger UI documentation URL
    redoc_url="/redoc"  # ReDoc documentation URL
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Custom middleware for request logging and timing
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log requests and measure response time."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log request details (only for API endpoints)
        if request.url.path.startswith("/api"):
            logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
        
        # Add timing header to response
        response.headers["X-Process-Time"] = str(process_time)
        return response


# Custom middleware for security headers
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


# Add custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Add CORS middleware to allow cross-origin requests
# This enables frontend applications from different domains to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (configure for production)
    allow_credentials=True,  # Allow cookies and authorization headers
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include API routers with /api/v1 prefix for versioning
app.include_router(campaigns.router, prefix="/api/v1")  # Campaign endpoints
app.include_router(customers.router, prefix="/api/v1")  # Customer endpoints
app.include_router(discounts.router, prefix="/api/v1")  # Discount endpoints


# Global exception handler for unhandled errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions gracefully."""
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"}
    )


@app.get("/", tags=["Health"])
@limiter.limit("100/minute")  # Rate limit health checks
def root(request: Request):
    """
    Root endpoint - Basic health check.
    
    Returns:
        dict: Service status information
    """
    return {
        "status": "healthy",
        "service": "Campaign Management Service",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
@limiter.limit("100/minute")  # Rate limit health checks
def health_check(request: Request, db: Session = Depends(get_db)):
    """
    Detailed health check endpoint.
    
    Returns:
        dict: Detailed service status including database connection
    """
    # Actually check database connection
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "version": "1.0.0"
    }
