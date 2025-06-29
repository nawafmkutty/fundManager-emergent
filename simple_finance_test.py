import requests
import json
import time
import uuid

# Use the public endpoint for testing
API_URL = "https://63acd9f0-ae1e-442e-a051-257150880f67.preview.emergentagent.com"

def print_response(response, message):
    """Print formatted response information"""
    print(f"\n--- {message} ---")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ Success")
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)[:500]}...")
        except:
            print(f"Response: {response.text[:500]}...")
    else:
        print("❌ Failed")
        try:
            print(f"Error: {response.json()}")
        except:
            print(f"Error: {response.text}")

def test_finance_lifecycle():
    """Test the complete finance application lifecycle"""
    print("\n=== TESTING FINANCE APPLICATION LIFECYCLE ===\n")
    
    # Step 1: Admin Login
    print("\n--- Step 1: Admin Login ---")
    admin_credentials = {
        "email": "admin@fundmanager.com",
        "password": "FundAdmin2024!"
    }
    response = requests.post(f"{API_URL}/api/auth/login", json=admin_credentials)
    if response.status_code != 200:
        print(f"❌ Admin login failed: {response.text}")
        return
    admin_data = response.json()
    admin_token = admin_data["access_token"]
    print(f"✅ Admin login successful. Token: {admin_token[:15]}...")
    
    # Step 2: Create Test User
    print("\n--- Step 2: Create Test User ---")
    test_user = {
        "email": f"test_{uuid.uuid4()}@example.com",
        "password": "Test123!",
        "full_name": "Test User",
        "country": "Test Country",
        "phone": "1234567890"
    }
    response = requests.post(f"{API_URL}/api/auth/register", json=test_user)
    if response.status_code != 200:
        print(f"❌ User registration failed: {response.text}")
        return
    user_data = response.json()
    user_token = user_data["access_token"]
    user_id = user_data["user"]["id"]
    print(f"✅ User registered: {test_user['email']}")
    print(f"User token: {user_token[:15]}...")
    
    # Step 3: Create Guarantor
    print("\n--- Step 3: Create Guarantor ---")
    guarantor_user = {
        "email": f"guarantor_{uuid.uuid4()}@example.com",
        "password": "Test123!",
        "full_name": "Guarantor User",
        "country": "Test Country",
        "phone": "1234567890"
    }
    response = requests.post(f"{API_URL}/api/auth/register", json=guarantor_user)
    if response.status_code != 200:
        print(f"❌ Guarantor registration failed: {response.text}")
        return
    guarantor_data = response.json()
    guarantor_token = guarantor_data["access_token"]
    guarantor_id = guarantor_data["user"]["id"]
    print(f"✅ Guarantor registered: {guarantor_user['email']}")
    
    # Step 4: Fund the Pool - Create Deposits
    print("\n--- Step 4: Fund the Pool ---")
    # Guarantor deposit
    headers = {"Authorization": f"Bearer {guarantor_token}"}
    deposit_data = {"amount": 1000, "description": "Guarantor deposit"}
    response = requests.post(f"{API_URL}/api/deposits", json=deposit_data, headers=headers)
    print_response(response, "Guarantor Deposit")
    
    # User deposit
    headers = {"Authorization": f"Bearer {user_token}"}
    deposit_data = {"amount": 2000, "description": "User deposit"}
    response = requests.post(f"{API_URL}/api/deposits", json=deposit_data, headers=headers)
    print_response(response, "User Deposit")
    
    # Step 5: Check Fund Pool
    print("\n--- Step 5: Check Fund Pool ---")
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{API_URL}/api/admin/fund-pool", headers=headers)
    print_response(response, "Fund Pool Status")
    
    # Step 6: Create Finance Application
    print("\n--- Step 6: Create Finance Application ---")
    headers = {"Authorization": f"Bearer {user_token}"}
    application_data = {
        "amount": 1500,
        "purpose": "Test finance lifecycle",
        "requested_duration_months": 6,
        "description": "Testing complete finance lifecycle",
        "guarantors": [guarantor_id]
    }
    response = requests.post(f"{API_URL}/api/finance-applications", json=application_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Finance application creation failed: {response.text}")
        return
    application_data = response.json()
    application_id = application_data["id"]
    print(f"✅ Finance application created: {application_id}")
    
    # Step 7: Guarantor Accepts
    print("\n--- Step 7: Guarantor Accepts ---")
    headers = {"Authorization": f"Bearer {guarantor_token}"}
    response = requests.get(f"{API_URL}/api/guarantor-requests", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get guarantor requests: {response.text}")
        return
    guarantor_requests = response.json()
    if not guarantor_requests:
        print("❌ No guarantor requests found")
        return
    guarantor_request_id = guarantor_requests[0]["id"]
    
    response = requests.put(
        f"{API_URL}/api/guarantor-requests/{guarantor_request_id}/respond",
        json={"status": "accepted"},
        headers=headers
    )
    print_response(response, "Guarantor Acceptance")
    
    # Step 8: Admin Approves Application
    print("\n--- Step 8: Admin Approves Application ---")
    headers = {"Authorization": f"Bearer {admin_token}"}
    approval_data = {
        "action": "approve",
        "review_notes": "Approved for testing",
        "conditions": "None",
        "recommended_amount": 1500
    }
    response = requests.put(
        f"{API_URL}/api/admin/applications/{application_id}/approve",
        json=approval_data,
        headers=headers
    )
    print_response(response, "Admin Approval")
    
    # Step 9: Check Ready for Disbursement
    print("\n--- Step 9: Check Ready for Disbursement ---")
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{API_URL}/api/admin/ready-for-disbursement", headers=headers)
    print_response(response, "Ready for Disbursement")
    
    # Step 10: Disburse Funds
    print("\n--- Step 10: Disburse Funds ---")
    headers = {"Authorization": f"Bearer {admin_token}"}
    disbursement_data = {
        "notes": "Test disbursement",
        "reference_number": f"TEST-{uuid.uuid4().hex[:8].upper()}",
        "disbursement_method": "bank_transfer"
    }
    response = requests.post(
        f"{API_URL}/api/admin/applications/{application_id}/disburse",
        json=disbursement_data,
        headers=headers
    )
    if response.status_code != 200:
        print(f"❌ Disbursement failed: {response.text}")
        return
    disbursement_data = response.json()
    disbursement_id = disbursement_data["disbursement"]["id"]
    print(f"✅ Funds disbursed. Disbursement ID: {disbursement_id}")
    
    # Step 11: Check Disbursements
    print("\n--- Step 11: Check Disbursements ---")
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{API_URL}/api/admin/disbursements", headers=headers)
    print_response(response, "Disbursements List")
    
    # Step 12: Check Payment Schedules
    print("\n--- Step 12: Check Payment Schedules ---")
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{API_URL}/api/payment-schedules", headers=headers)
    print_response(response, "Payment Schedules")
    
    # Step 13: Recalculate Fund Pool
    print("\n--- Step 13: Recalculate Fund Pool ---")
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.post(f"{API_URL}/api/admin/fund-pool/recalculate", headers=headers)
    print_response(response, "Fund Pool Recalculation")
    
    # Step 14: Verify Application Status
    print("\n--- Step 14: Verify Application Status ---")
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{API_URL}/api/finance-applications", headers=headers)
    print_response(response, "Application Status")
    
    print("\n=== FINANCE APPLICATION LIFECYCLE TEST COMPLETED ===\n")

if __name__ == "__main__":
    test_finance_lifecycle()