import requests
import uuid
import time
from datetime import datetime

# Use the public endpoint for testing
API_URL = "https://433806b5-1f2d-4f04-9e13-a9ca5a6ee55e.preview.emergentagent.com"

def test_priority_system():
    """Test the priority system functionality"""
    print("\n=== Testing Priority System ===")
    
    # Register a test user
    test_user = {
        "email": f"test_{uuid.uuid4()}@example.com",
        "password": "Test123!",
        "full_name": "Test User",
        "country": "Test Country",
        "phone": "1234567890"
    }
    
    print(f"Registering user: {test_user['email']}")
    response = requests.post(f"{API_URL}/api/auth/register", json=test_user)
    if response.status_code != 200:
        print(f"❌ User registration failed: {response.status_code} - {response.text}")
        return False
    
    data = response.json()
    token = data["access_token"]
    user_id = data["user"]["id"]
    print(f"✅ User registered with ID: {user_id}")
    
    # Create first finance application (should have priority 100)
    headers = {"Authorization": f"Bearer {token}"}
    app1_data = {
        "amount": 500,
        "purpose": "First application",
        "requested_duration_months": 6,
        "description": "Testing priority system"
    }
    
    print("Creating first finance application...")
    response = requests.post(f"{API_URL}/api/finance-applications", json=app1_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ First application failed: {response.status_code} - {response.text}")
        return False
    
    app1 = response.json()
    print(f"✅ First application created with priority: {app1['priority_score']}")
    if app1["priority_score"] != 100:
        print(f"❌ Expected priority 100, got {app1['priority_score']}")
        return False
    
    # Create second finance application (should have priority 90)
    app2_data = {
        "amount": 300,
        "purpose": "Second application",
        "requested_duration_months": 3,
        "description": "Testing priority system"
    }
    
    print("Creating second finance application...")
    response = requests.post(f"{API_URL}/api/finance-applications", json=app2_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Second application failed: {response.status_code} - {response.text}")
        return False
    
    app2 = response.json()
    print(f"✅ Second application created with priority: {app2['priority_score']}")
    if app2["priority_score"] != 90:
        print(f"❌ Expected priority 90, got {app2['priority_score']}")
        return False
    
    # Create third finance application (should have priority 80)
    app3_data = {
        "amount": 200,
        "purpose": "Third application",
        "requested_duration_months": 2,
        "description": "Testing priority system"
    }
    
    print("Creating third finance application...")
    response = requests.post(f"{API_URL}/api/finance-applications", json=app3_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Third application failed: {response.status_code} - {response.text}")
        return False
    
    app3 = response.json()
    print(f"✅ Third application created with priority: {app3['priority_score']}")
    if app3["priority_score"] != 80:
        print(f"❌ Expected priority 80, got {app3['priority_score']}")
        return False
    
    # Check admin view for priority sorting
    # Login as admin
    admin_login = {
        "email": "admin@fundmanager.com",
        "password": "FundAdmin2024!"
    }
    
    print("Logging in as admin...")
    response = requests.post(f"{API_URL}/api/auth/login", json=admin_login)
    if response.status_code != 200:
        print(f"❌ Admin login failed: {response.status_code} - {response.text}")
        return False
    
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    print("Checking admin applications view...")
    response = requests.get(f"{API_URL}/api/admin/applications", headers=admin_headers)
    if response.status_code != 200:
        print(f"❌ Admin applications view failed: {response.status_code} - {response.text}")
        return False
    
    admin_apps = response.json()
    
    # Filter applications for our test user
    user_apps = [app for app in admin_apps if app["user_id"] == user_id]
    
    # Check if applications are sorted by priority (highest first)
    priorities = [app["priority_score"] for app in user_apps]
    if priorities != sorted(priorities, reverse=True):
        print(f"❌ Applications not sorted by priority. Got: {priorities}")
        return False
    
    print("✅ Admin applications view shows correct priority sorting")
    return True

def test_guarantor_system():
    """Test the guarantor system functionality"""
    print("\n=== Testing Guarantor System ===")
    
    # Create test users
    user_b = {
        "email": f"user_b_{uuid.uuid4()}@example.com",
        "password": "Test123!",
        "full_name": "User B",
        "country": "Test Country",
        "phone": "1234567890"
    }
    
    guarantor_a = {
        "email": f"guarantor_a_{uuid.uuid4()}@example.com",
        "password": "Test123!",
        "full_name": "Guarantor A",
        "country": "Test Country",
        "phone": "1234567890"
    }
    
    guarantor_c = {
        "email": f"guarantor_c_{uuid.uuid4()}@example.com",
        "password": "Test123!",
        "full_name": "Guarantor C",
        "country": "Test Country",
        "phone": "1234567890"
    }
    
    # Register User B
    print(f"Registering User B: {user_b['email']}")
    response = requests.post(f"{API_URL}/api/auth/register", json=user_b)
    if response.status_code != 200:
        print(f"❌ User B registration failed: {response.status_code} - {response.text}")
        return False
    
    user_b_data = response.json()
    user_b_token = user_b_data["access_token"]
    user_b_id = user_b_data["user"]["id"]
    print(f"✅ User B registered with ID: {user_b_id}")
    
    # Register Guarantor A
    print(f"Registering Guarantor A: {guarantor_a['email']}")
    response = requests.post(f"{API_URL}/api/auth/register", json=guarantor_a)
    if response.status_code != 200:
        print(f"❌ Guarantor A registration failed: {response.status_code} - {response.text}")
        return False
    
    guarantor_a_data = response.json()
    guarantor_a_token = guarantor_a_data["access_token"]
    guarantor_a_id = guarantor_a_data["user"]["id"]
    print(f"✅ Guarantor A registered with ID: {guarantor_a_id}")
    
    # Register Guarantor C
    print(f"Registering Guarantor C: {guarantor_c['email']}")
    response = requests.post(f"{API_URL}/api/auth/register", json=guarantor_c)
    if response.status_code != 200:
        print(f"❌ Guarantor C registration failed: {response.status_code} - {response.text}")
        return False
    
    guarantor_c_data = response.json()
    guarantor_c_token = guarantor_c_data["access_token"]
    guarantor_c_id = guarantor_c_data["user"]["id"]
    print(f"✅ Guarantor C registered with ID: {guarantor_c_id}")
    
    # Add deposits to make guarantors eligible/ineligible
    # Guarantor A: $600 (eligible)
    headers = {"Authorization": f"Bearer {guarantor_a_token}"}
    deposit_data = {"amount": 600, "description": "Initial deposit"}
    
    print("Adding $600 deposit for Guarantor A...")
    response = requests.post(f"{API_URL}/api/deposits", json=deposit_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Guarantor A deposit failed: {response.status_code} - {response.text}")
        return False
    
    print("✅ Guarantor A deposit successful")
    
    # Guarantor C: $1000 (eligible)
    headers = {"Authorization": f"Bearer {guarantor_c_token}"}
    deposit_data = {"amount": 1000, "description": "Initial deposit"}
    
    print("Adding $1000 deposit for Guarantor C...")
    response = requests.post(f"{API_URL}/api/deposits", json=deposit_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Guarantor C deposit failed: {response.status_code} - {response.text}")
        return False
    
    print("✅ Guarantor C deposit successful")
    
    # User B checks eligible guarantors
    headers = {"Authorization": f"Bearer {user_b_token}"}
    
    print("User B checking eligible guarantors...")
    response = requests.get(f"{API_URL}/api/guarantors/eligible", headers=headers)
    if response.status_code != 200:
        print(f"❌ Get eligible guarantors failed: {response.status_code} - {response.text}")
        return False
    
    eligible_guarantors = response.json()
    guarantor_ids = [g["id"] for g in eligible_guarantors]
    
    if guarantor_a_id not in guarantor_ids:
        print(f"❌ Guarantor A should be eligible but wasn't found")
        return False
    
    if guarantor_c_id not in guarantor_ids:
        print(f"❌ Guarantor C should be eligible but wasn't found")
        return False
    
    print("✅ Eligible guarantors check successful")
    
    # User B creates application with guarantors
    application_data = {
        "amount": 500,
        "purpose": "Test with guarantors",
        "requested_duration_months": 6,
        "description": "Testing guarantor system",
        "guarantors": [guarantor_a_id, guarantor_c_id]
    }
    
    print("User B creating application with guarantors...")
    response = requests.post(f"{API_URL}/api/finance-applications", json=application_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Create application with guarantors failed: {response.status_code} - {response.text}")
        return False
    
    application = response.json()
    application_id = application["id"]
    print(f"✅ Application created with ID: {application_id}")
    
    # Check guarantors in application
    if len(application["guarantors"]) != 2:
        print(f"❌ Expected 2 guarantors, got {len(application['guarantors'])}")
        return False
    
    guarantor_user_ids = [g["guarantor_user_id"] for g in application["guarantors"]]
    if guarantor_a_id not in guarantor_user_ids or guarantor_c_id not in guarantor_user_ids:
        print(f"❌ Guarantors not correctly assigned to application")
        return False
    
    print("✅ Guarantors correctly assigned to application")
    
    # Check guarantor requests
    headers = {"Authorization": f"Bearer {guarantor_a_token}"}
    
    print("Checking Guarantor A's requests...")
    response = requests.get(f"{API_URL}/api/guarantor-requests", headers=headers)
    if response.status_code != 200:
        print(f"❌ Get guarantor requests failed: {response.status_code} - {response.text}")
        return False
    
    guarantor_a_requests = response.json()
    if len(guarantor_a_requests) != 1:
        print(f"❌ Expected 1 guarantor request for Guarantor A, got {len(guarantor_a_requests)}")
        return False
    
    guarantor_a_request_id = guarantor_a_requests[0]["id"]
    print(f"✅ Guarantor A has 1 request with ID: {guarantor_a_request_id}")
    
    # Guarantor A accepts request
    print("Guarantor A accepting request...")
    response = requests.put(
        f"{API_URL}/api/guarantor-requests/{guarantor_a_request_id}/respond",
        json={"status": "accepted"},
        headers=headers
    )
    if response.status_code != 200:
        print(f"❌ Guarantor A accept request failed: {response.status_code} - {response.text}")
        return False
    
    print("✅ Guarantor A accepted request")
    
    # Check Guarantor C's requests
    headers = {"Authorization": f"Bearer {guarantor_c_token}"}
    
    print("Checking Guarantor C's requests...")
    response = requests.get(f"{API_URL}/api/guarantor-requests", headers=headers)
    if response.status_code != 200:
        print(f"❌ Get guarantor requests failed: {response.status_code} - {response.text}")
        return False
    
    guarantor_c_requests = response.json()
    if len(guarantor_c_requests) != 1:
        print(f"❌ Expected 1 guarantor request for Guarantor C, got {len(guarantor_c_requests)}")
        return False
    
    guarantor_c_request_id = guarantor_c_requests[0]["id"]
    print(f"✅ Guarantor C has 1 request with ID: {guarantor_c_request_id}")
    
    # Guarantor C declines request
    print("Guarantor C declining request...")
    response = requests.put(
        f"{API_URL}/api/guarantor-requests/{guarantor_c_request_id}/respond",
        json={"status": "declined"},
        headers=headers
    )
    if response.status_code != 200:
        print(f"❌ Guarantor C decline request failed: {response.status_code} - {response.text}")
        return False
    
    print("✅ Guarantor C declined request")
    
    # Check application status after guarantor responses
    headers = {"Authorization": f"Bearer {user_b_token}"}
    
    print("Checking application status after guarantor responses...")
    response = requests.get(f"{API_URL}/api/finance-applications", headers=headers)
    if response.status_code != 200:
        print(f"❌ Get applications failed: {response.status_code} - {response.text}")
        return False
    
    applications = response.json()
    updated_app = next((app for app in applications if app["id"] == application_id), None)
    if not updated_app:
        print(f"❌ Application not found after guarantor responses")
        return False
    
    # Check guarantor statuses
    guarantor_statuses = {g["guarantor_user_id"]: g["status"] for g in updated_app["guarantors"]}
    
    if guarantor_statuses.get(guarantor_a_id) != "accepted":
        print(f"❌ Guarantor A status should be 'accepted', got '{guarantor_statuses.get(guarantor_a_id)}'")
        return False
    
    if guarantor_statuses.get(guarantor_c_id) != "declined":
        print(f"❌ Guarantor C status should be 'declined', got '{guarantor_statuses.get(guarantor_c_id)}'")
        return False
    
    print("✅ Guarantor statuses correctly updated in application")
    return True

def test_invalid_guarantor():
    """Test creating application with invalid guarantor"""
    print("\n=== Testing Invalid Guarantor ===")
    
    # Create test users
    user = {
        "email": f"user_{uuid.uuid4()}@example.com",
        "password": "Test123!",
        "full_name": "Test User",
        "country": "Test Country",
        "phone": "1234567890"
    }
    
    ineligible_guarantor = {
        "email": f"ineligible_{uuid.uuid4()}@example.com",
        "password": "Test123!",
        "full_name": "Ineligible Guarantor",
        "country": "Test Country",
        "phone": "1234567890"
    }
    
    # Register User
    print(f"Registering User: {user['email']}")
    response = requests.post(f"{API_URL}/api/auth/register", json=user)
    if response.status_code != 200:
        print(f"❌ User registration failed: {response.status_code} - {response.text}")
        return False
    
    user_data = response.json()
    user_token = user_data["access_token"]
    user_id = user_data["user"]["id"]
    print(f"✅ User registered with ID: {user_id}")
    
    # Register Ineligible Guarantor
    print(f"Registering Ineligible Guarantor: {ineligible_guarantor['email']}")
    response = requests.post(f"{API_URL}/api/auth/register", json=ineligible_guarantor)
    if response.status_code != 200:
        print(f"❌ Ineligible Guarantor registration failed: {response.status_code} - {response.text}")
        return False
    
    ineligible_guarantor_data = response.json()
    ineligible_guarantor_token = ineligible_guarantor_data["access_token"]
    ineligible_guarantor_id = ineligible_guarantor_data["user"]["id"]
    print(f"✅ Ineligible Guarantor registered with ID: {ineligible_guarantor_id}")
    
    # Add small deposit to ineligible guarantor (below $500)
    headers = {"Authorization": f"Bearer {ineligible_guarantor_token}"}
    deposit_data = {"amount": 300, "description": "Small deposit"}
    
    print("Adding $300 deposit for Ineligible Guarantor...")
    response = requests.post(f"{API_URL}/api/deposits", json=deposit_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Ineligible Guarantor deposit failed: {response.status_code} - {response.text}")
        return False
    
    print("✅ Ineligible Guarantor deposit successful")
    
    # User tries to create application with ineligible guarantor
    headers = {"Authorization": f"Bearer {user_token}"}
    application_data = {
        "amount": 500,
        "purpose": "Test with ineligible guarantor",
        "requested_duration_months": 6,
        "description": "Testing guarantor eligibility",
        "guarantors": [ineligible_guarantor_id]
    }
    
    print("User creating application with ineligible guarantor...")
    response = requests.post(f"{API_URL}/api/finance-applications", json=application_data, headers=headers)
    
    # This should fail with 400 Bad Request
    if response.status_code != 400:
        print(f"❌ Expected 400 error for ineligible guarantor, got {response.status_code}")
        return False
    
    error_detail = response.json().get("detail", "")
    if "not eligible" not in error_detail.lower():
        print(f"❌ Expected 'not eligible' in error message, got: {error_detail}")
        return False
    
    print(f"✅ Application with ineligible guarantor correctly rejected: {error_detail}")
    return True

if __name__ == "__main__":
    print("Starting Fund Management System Tests")
    print("Testing Priority System and Guarantor Functionality")
    print("=" * 50)
    
    priority_result = test_priority_system()
    guarantor_result = test_guarantor_system()
    invalid_guarantor_result = test_invalid_guarantor()
    
    print("\n=== TEST SUMMARY ===")
    print(f"Priority System: {'✅ PASSED' if priority_result else '❌ FAILED'}")
    print(f"Guarantor System: {'✅ PASSED' if guarantor_result else '❌ FAILED'}")
    print(f"Invalid Guarantor: {'✅ PASSED' if invalid_guarantor_result else '❌ FAILED'}")
    
    if priority_result and guarantor_result and invalid_guarantor_result:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")