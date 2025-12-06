# Comprehensive API Testing Script
$baseUrl = "http://127.0.0.1:8000"
$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "🧪 COMPREHENSIVE API TESTING" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Test 1: Health Check
Write-Host "✅ TEST 1: Health Check" -ForegroundColor Green
$response = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET
Write-Host "Response:" -ForegroundColor Yellow
$response | ConvertTo-Json -Depth 10
Write-Host "`n"

# Test 2: Create Customer 1
Write-Host "✅ TEST 2: Create Customer 1" -ForegroundColor Green
$body = @{
    email = "john.doe@example.com"
    name = "John Doe"
} | ConvertTo-Json
$customer1 = Invoke-RestMethod -Uri "$baseUrl/api/v1/customers/" -Method POST -Body $body -ContentType "application/json"
Write-Host "Response:" -ForegroundColor Yellow
$customer1 | ConvertTo-Json -Depth 10
Write-Host "`n"

# Test 3: Create Customer 2
Write-Host "✅ TEST 3: Create Customer 2" -ForegroundColor Green
$body = @{
    email = "jane.smith@example.com"
    name = "Jane Smith"
} | ConvertTo-Json
$customer2 = Invoke-RestMethod -Uri "$baseUrl/api/v1/customers/" -Method POST -Body $body -ContentType "application/json"
Write-Host "Response:" -ForegroundColor Yellow
$customer2 | ConvertTo-Json -Depth 10
Write-Host "`n"

# Test 4: Get All Customers
Write-Host "✅ TEST 4: Get All Customers" -ForegroundColor Green
$customers = Invoke-RestMethod -Uri "$baseUrl/api/v1/customers/" -Method GET
Write-Host "Response:" -ForegroundColor Yellow
$customers | ConvertTo-Json -Depth 10
Write-Host "`n"

# Test 5: Create Cart Discount Campaign
Write-Host "✅ TEST 5: Create Cart Discount Campaign (20% Off)" -ForegroundColor Green
$body = @{
    name = "Summer Sale - 20% Off"
    description = "Get 20% discount on your entire cart"
    discount_type = "cart"
    discount_percentage = 20
    start_date = "2025-01-01T00:00:00"
    end_date = "2025-12-31T23:59:59"
    total_budget = 10000
    max_usage_per_customer_per_day = 3
    min_cart_value = 100
    max_discount_amount = 500
    is_targeted = $false
} | ConvertTo-Json
$campaign1 = Invoke-RestMethod -Uri "$baseUrl/api/v1/campaigns/" -Method POST -Body $body -ContentType "application/json"
Write-Host "Response:" -ForegroundColor Yellow
$campaign1 | ConvertTo-Json -Depth 10
Write-Host "`n"

# Test 6: Create Delivery Discount Campaign
Write-Host "✅ TEST 6: Create Delivery Discount Campaign (50% Off)" -ForegroundColor Green
$body = @{
    name = "Free Delivery Week"
    description = "50% off on delivery charges"
    discount_type = "delivery"
    discount_percentage = 50
    start_date = "2025-01-01T00:00:00"
    end_date = "2025-12-31T23:59:59"
    total_budget = 5000
    max_usage_per_customer_per_day = 2
    min_cart_value = 50
    is_targeted = $false
} | ConvertTo-Json
$campaign2 = Invoke-RestMethod -Uri "$baseUrl/api/v1/campaigns/" -Method POST -Body $body -ContentType "application/json"
Write-Host "Response:" -ForegroundColor Yellow
$campaign2 | ConvertTo-Json -Depth 10
Write-Host "`n"

# Test 7: Create Targeted Campaign with Full Customer Details
Write-Host "✅ TEST 7: Create Targeted Campaign (30% Off for VIPs)" -ForegroundColor Green
$body = @{
    name = "VIP Customer Special - 30% Off"
    description = "Exclusive discount for VIP customers"
    discount_type = "cart"
    discount_percentage = 30
    start_date = "2025-01-01T00:00:00"
    end_date = "2025-12-31T23:59:59"
    total_budget = 15000
    max_usage_per_customer_per_day = 5
    min_cart_value = 200
    max_discount_amount = 1000
    is_targeted = $true
    target_customer_ids = @($customer1.id, $customer2.id)
} | ConvertTo-Json
$campaign3 = Invoke-RestMethod -Uri "$baseUrl/api/v1/campaigns/" -Method POST -Body $body -ContentType "application/json"
Write-Host "Response (Should show targeted_customers with full details):" -ForegroundColor Yellow
$campaign3 | ConvertTo-Json -Depth 10
Write-Host "`n"

# Test 8: Try Creating Campaign with Non-existent Customer (Should Fail)
Write-Host "❌ TEST 8: Try Creating Campaign with Invalid Customer ID (Should Fail)" -ForegroundColor Red
try {
    $body = @{
        name = "Invalid Campaign"
        discount_type = "cart"
        discount_percentage = 10
        start_date = "2025-01-01T00:00:00"
        end_date = "2025-12-31T23:59:59"
        total_budget = 1000
        is_targeted = $true
        target_customer_ids = @(9999)
    } | ConvertTo-Json
    $invalid = Invoke-RestMethod -Uri "$baseUrl/api/v1/campaigns/" -Method POST -Body $body -ContentType "application/json"
    Write-Host "ERROR: Should have failed!" -ForegroundColor Red
} catch {
    Write-Host "✅ Correctly returned error:" -ForegroundColor Green
    $_.Exception.Response.StatusCode
    Write-Host ($_.ErrorDetails.Message | ConvertFrom-Json | ConvertTo-Json -Depth 10) -ForegroundColor Yellow
}
Write-Host "`n"

# Test 9: Get All Campaigns
Write-Host "✅ TEST 9: Get All Campaigns" -ForegroundColor Green
$campaigns = Invoke-RestMethod -Uri "$baseUrl/api/v1/campaigns/" -Method GET
Write-Host "Response:" -ForegroundColor Yellow
$campaigns | ConvertTo-Json -Depth 10
Write-Host "`n"

# Test 10: Get Specific Campaign by ID (Should show targeted_customers)
Write-Host "✅ TEST 10: Get Campaign by ID (Should show full customer details)" -ForegroundColor Green
$campaignDetail = Invoke-RestMethod -Uri "$baseUrl/api/v1/campaigns/$($campaign3.id)" -Method GET
Write-Host "Response:" -ForegroundColor Yellow
$campaignDetail | ConvertTo-Json -Depth 10
Write-Host "`n"

# Test 11: Get Available Discounts
Write-Host "✅ TEST 11: Get Available Discounts for Customer" -ForegroundColor Green
$body = @{
    customer_id = $customer1.id
    cart_value = 500
    delivery_charge = 50
} | ConvertTo-Json
$available = Invoke-RestMethod -Uri "$baseUrl/api/v1/discounts/available" -Method POST -Body $body -ContentType "application/json"
Write-Host "Response:" -ForegroundColor Yellow
$available | ConvertTo-Json -Depth 10
Write-Host "`n"

# Test 12: Apply Cart Discount
Write-Host "✅ TEST 12: Apply Cart Discount" -ForegroundColor Green
$body = @{
    campaign_id = $campaign1.id
    customer_id = $customer1.id
    cart_value = 500
} | ConvertTo-Json
$usage1 = Invoke-RestMethod -Uri "$baseUrl/api/v1/discounts/apply" -Method POST -Body $body -ContentType "application/json"
Write-Host "Response (Enhanced with campaign name, customer details):" -ForegroundColor Yellow
$usage1 | ConvertTo-Json -Depth 10
Write-Host "`n"

# Test 13: Apply Delivery Discount
Write-Host "✅ TEST 13: Apply Delivery Discount" -ForegroundColor Green
$body = @{
    campaign_id = $campaign2.id
    customer_id = $customer1.id
    cart_value = 300
    delivery_charge = 100
} | ConvertTo-Json
$usage2 = Invoke-RestMethod -Uri "$baseUrl/api/v1/discounts/apply" -Method POST -Body $body -ContentType "application/json"
Write-Host "Response (Enhanced with campaign name, customer details):" -ForegroundColor Yellow
$usage2 | ConvertTo-Json -Depth 10
Write-Host "`n"

# Test 14: Get Usage History
Write-Host "✅ TEST 14: Get Customer Usage History (All Campaigns)" -ForegroundColor Green
$history = Invoke-RestMethod -Uri "$baseUrl/api/v1/discounts/usage/$($customer1.id)" -Method GET
Write-Host "Response:" -ForegroundColor Yellow
$history | ConvertTo-Json -Depth 10
Write-Host "`n"

# Test 15: Get Usage History for Specific Campaign
Write-Host "✅ TEST 15: Get Usage History for Specific Campaign" -ForegroundColor Green
$historyFiltered = Invoke-RestMethod -Uri "$baseUrl/api/v1/discounts/usage/$($customer1.id)?campaign_id=$($campaign1.id)" -Method GET
Write-Host "Response:" -ForegroundColor Yellow
$historyFiltered | ConvertTo-Json -Depth 10
Write-Host "`n"

# Test 16: Try Getting Usage for Non-existent Campaign (Should Fail with Message)
Write-Host "❌ TEST 16: Get Usage for Campaign with No History (Should Return Error)" -ForegroundColor Red
try {
    $noUsage = Invoke-RestMethod -Uri "$baseUrl/api/v1/discounts/usage/$($customer1.id)?campaign_id=$($campaign3.id)" -Method GET
    Write-Host "Unexpected success" -ForegroundColor Red
} catch {
    Write-Host "✅ Correctly returned error:" -ForegroundColor Green
    Write-Host ($_.ErrorDetails.Message | ConvertFrom-Json | ConvertTo-Json -Depth 10) -ForegroundColor Yellow
}
Write-Host "`n"

# Test 17: Update Campaign
Write-Host "✅ TEST 17: Update Campaign" -ForegroundColor Green
$body = @{
    name = "Summer Sale - 25% Off (UPDATED)"
    discount_percentage = 25
} | ConvertTo-Json
$updated = Invoke-RestMethod -Uri "$baseUrl/api/v1/campaigns/$($campaign1.id)" -Method PUT -Body $body -ContentType "application/json"
Write-Host "Response:" -ForegroundColor Yellow
$updated | ConvertTo-Json -Depth 10
Write-Host "`n"

# Test 18: Filter Campaigns by Type
Write-Host "✅ TEST 18: Filter Campaigns by Type (cart)" -ForegroundColor Green
$filtered = Invoke-RestMethod -Uri "$baseUrl/api/v1/campaigns/?discount_type=cart" -Method GET
Write-Host "Response:" -ForegroundColor Yellow
$filtered | ConvertTo-Json -Depth 10
Write-Host "`n"

# Test 19: Test Daily Usage Limit
Write-Host "✅ TEST 19: Test Daily Usage Limit (Apply same discount 3 times)" -ForegroundColor Green
for ($i = 1; $i -le 2; $i++) {
    try {
        $body = @{
            campaign_id = $campaign1.id
            customer_id = $customer1.id
            cart_value = 500
        } | ConvertTo-Json
        $usage = Invoke-RestMethod -Uri "$baseUrl/api/v1/discounts/apply" -Method POST -Body $body -ContentType "application/json"
        Write-Host "Usage #$($i + 1) applied successfully" -ForegroundColor Green
    } catch {
        Write-Host "Usage #$($i + 1) failed (might be limit reached):" -ForegroundColor Yellow
        Write-Host ($_.ErrorDetails.Message | ConvertFrom-Json).detail -ForegroundColor Yellow
    }
}
Write-Host "`n"

# Test 20: Test Minimum Cart Value Validation (Should Fail)
Write-Host "❌ TEST 20: Try Applying Discount Below Minimum Cart Value (Should Fail)" -ForegroundColor Red
try {
    $body = @{
        campaign_id = $campaign1.id
        customer_id = $customer2.id
        cart_value = 50
    } | ConvertTo-Json
    $invalid = Invoke-RestMethod -Uri "$baseUrl/api/v1/discounts/apply" -Method POST -Body $body -ContentType "application/json"
    Write-Host "ERROR: Should have failed!" -ForegroundColor Red
} catch {
    Write-Host "✅ Correctly returned error:" -ForegroundColor Green
    Write-Host ($_.ErrorDetails.Message | ConvertFrom-Json | ConvertTo-Json -Depth 10) -ForegroundColor Yellow
}
Write-Host "`n"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ ALL TESTS COMPLETED!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
