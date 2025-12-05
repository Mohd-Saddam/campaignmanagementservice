import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from app.main import app
from app.database import Base, get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_campaign.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestCustomerEndpoints:
    """Test customer CRUD endpoints."""
    
    def test_create_customer(self):
        response = client.post(
            "/api/v1/customers/",
            json={"email": "test@example.com", "name": "Test User"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert "id" in data
    
    def test_create_duplicate_customer(self):
        # Create first customer
        client.post(
            "/api/v1/customers/",
            json={"email": "test@example.com", "name": "Test User"}
        )
        # Try to create duplicate
        response = client.post(
            "/api/v1/customers/",
            json={"email": "test@example.com", "name": "Another User"}
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_get_customer(self):
        # Create customer
        create_response = client.post(
            "/api/v1/customers/",
            json={"email": "test@example.com", "name": "Test User"}
        )
        customer_id = create_response.json()["id"]
        
        # Get customer
        response = client.get(f"/api/v1/customers/{customer_id}")
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"
    
    def test_get_nonexistent_customer(self):
        response = client.get("/api/v1/customers/999")
        assert response.status_code == 404
    
    def test_get_all_customers(self):
        # Create customers
        client.post("/api/v1/customers/", json={"email": "test1@example.com", "name": "User 1"})
        client.post("/api/v1/customers/", json={"email": "test2@example.com", "name": "User 2"})
        
        response = client.get("/api/v1/customers/")
        assert response.status_code == 200
        assert len(response.json()) == 2


class TestCampaignEndpoints:
    """Test campaign CRUD endpoints."""
    
    def get_valid_campaign_data(self):
        return {
            "name": "Summer Sale",
            "description": "20% off on all items",
            "discount_type": "cart",
            "discount_percentage": 20,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "total_budget": 10000,
            "max_usage_per_customer_per_day": 2,
            "min_cart_value": 100,
            "max_discount_amount": 500,
            "is_targeted": False
        }
    
    def test_create_campaign(self):
        response = client.post("/api/v1/campaigns/", json=self.get_valid_campaign_data())
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Summer Sale"
        assert data["discount_type"] == "cart"
        assert data["status"] == "active"
    
    def test_create_campaign_without_discount(self):
        campaign_data = self.get_valid_campaign_data()
        del campaign_data["discount_percentage"]
        
        response = client.post("/api/v1/campaigns/", json=campaign_data)
        assert response.status_code == 400
        assert "discount_percentage or discount_flat" in response.json()["detail"]
    
    def test_create_targeted_campaign(self):
        # Create customer first
        customer_response = client.post(
            "/api/v1/customers/",
            json={"email": "vip@example.com", "name": "VIP User"}
        )
        customer_id = customer_response.json()["id"]
        
        # Create targeted campaign
        campaign_data = self.get_valid_campaign_data()
        campaign_data["is_targeted"] = True
        campaign_data["target_customer_ids"] = [customer_id]
        
        response = client.post("/api/v1/campaigns/", json=campaign_data)
        assert response.status_code == 201
        assert response.json()["is_targeted"] == True
        assert customer_id in response.json()["target_customer_ids"]
    
    def test_create_targeted_campaign_without_customers(self):
        campaign_data = self.get_valid_campaign_data()
        campaign_data["is_targeted"] = True
        
        response = client.post("/api/v1/campaigns/", json=campaign_data)
        assert response.status_code == 400
        assert "target_customer_ids required" in response.json()["detail"]
    
    def test_get_campaign(self):
        # Create campaign
        create_response = client.post("/api/v1/campaigns/", json=self.get_valid_campaign_data())
        campaign_id = create_response.json()["id"]
        
        response = client.get(f"/api/v1/campaigns/{campaign_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Summer Sale"
    
    def test_update_campaign(self):
        # Create campaign
        create_response = client.post("/api/v1/campaigns/", json=self.get_valid_campaign_data())
        campaign_id = create_response.json()["id"]
        
        # Update campaign
        response = client.put(
            f"/api/v1/campaigns/{campaign_id}",
            json={"name": "Updated Sale", "discount_percentage": 25}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Sale"
        assert response.json()["discount_percentage"] == 25
    
    def test_delete_campaign(self):
        # Create campaign
        create_response = client.post("/api/v1/campaigns/", json=self.get_valid_campaign_data())
        campaign_id = create_response.json()["id"]
        
        # Delete campaign
        response = client.delete(f"/api/v1/campaigns/{campaign_id}")
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(f"/api/v1/campaigns/{campaign_id}")
        assert get_response.status_code == 404
    
    def test_filter_campaigns_by_status(self):
        # Create active campaign
        client.post("/api/v1/campaigns/", json=self.get_valid_campaign_data())
        
        response = client.get("/api/v1/campaigns/?status=active")
        assert response.status_code == 200
        assert len(response.json()) >= 1
    
    def test_filter_campaigns_by_discount_type(self):
        # Create cart campaign
        client.post("/api/v1/campaigns/", json=self.get_valid_campaign_data())
        
        # Create delivery campaign
        delivery_campaign = self.get_valid_campaign_data()
        delivery_campaign["name"] = "Free Delivery"
        delivery_campaign["discount_type"] = "delivery"
        client.post("/api/v1/campaigns/", json=delivery_campaign)
        
        response = client.get("/api/v1/campaigns/?discount_type=cart")
        assert response.status_code == 200
        assert all(c["discount_type"] == "cart" for c in response.json())


class TestDiscountEndpoints:
    """Test discount eligibility and application endpoints."""
    
    def setup_test_data(self):
        """Create test customer and campaign."""
        # Create customer
        customer_response = client.post(
            "/api/v1/customers/",
            json={"email": "buyer@example.com", "name": "Buyer"}
        )
        customer_id = customer_response.json()["id"]
        
        # Create cart campaign
        cart_campaign = {
            "name": "Cart Discount",
            "discount_type": "cart",
            "discount_percentage": 10,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "total_budget": 10000,
            "max_usage_per_customer_per_day": 2,
            "min_cart_value": 100,
            "is_targeted": False
        }
        cart_response = client.post("/api/v1/campaigns/", json=cart_campaign)
        cart_campaign_id = cart_response.json()["id"]
        
        # Create delivery campaign
        delivery_campaign = {
            "name": "Free Delivery",
            "discount_type": "delivery",
            "discount_flat": 50,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "total_budget": 5000,
            "max_usage_per_customer_per_day": 1,
            "min_cart_value": 0,
            "is_targeted": False
        }
        delivery_response = client.post("/api/v1/campaigns/", json=delivery_campaign)
        delivery_campaign_id = delivery_response.json()["id"]
        
        return customer_id, cart_campaign_id, delivery_campaign_id
    
    def test_get_available_discounts(self):
        customer_id, cart_campaign_id, delivery_campaign_id = self.setup_test_data()
        
        response = client.post(
            "/api/v1/discounts/available",
            json={
                "customer_id": customer_id,
                "cart_value": 500,
                "delivery_charge": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["cart_discounts"]) >= 1
        assert len(data["delivery_discounts"]) >= 1
        assert data["best_cart_discount"] is not None
        assert data["best_delivery_discount"] is not None
    
    def test_get_discounts_nonexistent_customer(self):
        response = client.post(
            "/api/v1/discounts/available",
            json={
                "customer_id": 999,
                "cart_value": 500,
                "delivery_charge": 100
            }
        )
        assert response.status_code == 404
    
    def test_apply_discount(self):
        customer_id, cart_campaign_id, _ = self.setup_test_data()
        
        response = client.post(
            "/api/v1/discounts/apply",
            json={
                "campaign_id": cart_campaign_id,
                "customer_id": customer_id,
                "cart_value": 500
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["campaign_id"] == cart_campaign_id
        assert data["customer_id"] == customer_id
        assert data["discount_amount"] == 50  # 10% of 500
    
    def test_daily_usage_limit(self):
        customer_id, cart_campaign_id, _ = self.setup_test_data()
        
        # Use the discount twice (max allowed per day)
        for _ in range(2):
            client.post(
                "/api/v1/discounts/apply",
                json={
                    "campaign_id": cart_campaign_id,
                    "customer_id": customer_id,
                    "cart_value": 500
                }
            )
        
        # Third attempt should fail
        response = client.post(
            "/api/v1/discounts/apply",
            json={
                "campaign_id": cart_campaign_id,
                "customer_id": customer_id,
                "cart_value": 500
            }
        )
        assert response.status_code == 400
        assert "not eligible" in response.json()["detail"]
    
    def test_targeted_campaign_eligibility(self):
        # Create two customers
        vip_response = client.post(
            "/api/v1/customers/",
            json={"email": "vip@example.com", "name": "VIP"}
        )
        vip_id = vip_response.json()["id"]
        
        regular_response = client.post(
            "/api/v1/customers/",
            json={"email": "regular@example.com", "name": "Regular"}
        )
        regular_id = regular_response.json()["id"]
        
        # Create targeted campaign for VIP only
        campaign = {
            "name": "VIP Only",
            "discount_type": "cart",
            "discount_percentage": 30,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "total_budget": 10000,
            "max_usage_per_customer_per_day": 1,
            "min_cart_value": 0,
            "is_targeted": True,
            "target_customer_ids": [vip_id]
        }
        campaign_response = client.post("/api/v1/campaigns/", json=campaign)
        campaign_id = campaign_response.json()["id"]
        
        # VIP should see the discount
        vip_discounts = client.post(
            "/api/v1/discounts/available",
            json={"customer_id": vip_id, "cart_value": 500, "delivery_charge": 0}
        )
        assert any(d["campaign_id"] == campaign_id for d in vip_discounts.json()["cart_discounts"])
        
        # Regular customer should NOT see the discount
        regular_discounts = client.post(
            "/api/v1/discounts/available",
            json={"customer_id": regular_id, "cart_value": 500, "delivery_charge": 0}
        )
        assert not any(d["campaign_id"] == campaign_id for d in regular_discounts.json()["cart_discounts"])
    
    def test_min_cart_value(self):
        customer_id, cart_campaign_id, _ = self.setup_test_data()
        
        # Cart value below minimum (100)
        response = client.post(
            "/api/v1/discounts/available",
            json={
                "customer_id": customer_id,
                "cart_value": 50,
                "delivery_charge": 0
            }
        )
        assert response.status_code == 200
        # Should not have any cart discounts due to min value
        assert not any(d["campaign_id"] == cart_campaign_id for d in response.json()["cart_discounts"])
    
    def test_get_customer_usage_history(self):
        customer_id, cart_campaign_id, _ = self.setup_test_data()
        
        # Apply discount
        client.post(
            "/api/v1/discounts/apply",
            json={
                "campaign_id": cart_campaign_id,
                "customer_id": customer_id,
                "cart_value": 500
            }
        )
        
        # Get usage history
        response = client.get(f"/api/v1/discounts/usage/{customer_id}")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["campaign_id"] == cart_campaign_id


class TestBudgetConstraints:
    """Test budget-related constraints."""
    
    def test_budget_exhaustion(self):
        # Create customer
        customer_response = client.post(
            "/api/v1/customers/",
            json={"email": "spender@example.com", "name": "Big Spender"}
        )
        customer_id = customer_response.json()["id"]
        
        # Create campaign with small budget
        campaign = {
            "name": "Limited Budget",
            "discount_type": "cart",
            "discount_flat": 100,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "total_budget": 150,  # Only enough for 1.5 uses
            "max_usage_per_customer_per_day": 10,
            "min_cart_value": 0,
            "is_targeted": False
        }
        campaign_response = client.post("/api/v1/campaigns/", json=campaign)
        campaign_id = campaign_response.json()["id"]
        
        # First use - should work
        response1 = client.post(
            "/api/v1/discounts/apply",
            json={
                "campaign_id": campaign_id,
                "customer_id": customer_id,
                "cart_value": 500
            }
        )
        assert response1.status_code == 200
        assert response1.json()["discount_amount"] == 100
        
        # Second use - should get partial discount (remaining budget)
        response2 = client.post(
            "/api/v1/discounts/apply",
            json={
                "campaign_id": campaign_id,
                "customer_id": customer_id,
                "cart_value": 500
            }
        )
        assert response2.status_code == 200
        assert response2.json()["discount_amount"] == 50  # Remaining budget
        
        # Third use - should fail (budget exhausted)
        response3 = client.post(
            "/api/v1/discounts/apply",
            json={
                "campaign_id": campaign_id,
                "customer_id": customer_id,
                "cart_value": 500
            }
        )
        assert response3.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
