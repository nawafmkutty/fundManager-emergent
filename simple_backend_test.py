import requests
import uuid
import time
from datetime import datetime

# Use the public endpoint for testing
API_URL = "https://63acd9f0-ae1e-442e-a051-257150880f67.preview.emergentagent.com"

def print_separator():
    print("\n" + "="*50 + "\n")

def test_priority_system():
    print_separator()
    print("TESTING PRIORITY SYSTEM")
    print_separator()
    
    # Create a test user
    test_user = {
        "email": f"test_{uuid.uuid4()}@example.com",
        "password": "Test123!",
        "full_name": "Test User",
        "country": "Test Country",
        "phone": "1234567890"
    }
    
    print(f"Registering test user: {test_user['email']}")
    response = requests.post(f"{API_URL}/api/auth/register", json=test_user)
    
    if response.status_code != 200:
        print(f"❌ User registration failed: {response.status_code}")
        print(response.text)
        return False
    
    user_data = response.json()
    token = user_data["access_token"]
    user_id = user_data["user"]["id"]
    print(f"✅ User registered successfully with ID: {user_id}")
    
    # Create a deposit to ensure the user can apply for finance
    headers = {"Authorization": f"Bearer {token}"}
    deposit_data = {"amount": 200, "description": "Initial deposit"}
    
    print("Creating initial deposit")
    response = requests.post(f"{API_URL}/api/deposits", json=deposit_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Deposit creation failed: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ Deposit created successfully")
    
    # Create first application
    app1_data = {
        "amount": 100,
        "purpose": "First application",
        "requested_duration_months": 3,
        "description": "Testing priority system"
    }
    
    print("Creating first finance application")
    response = requests.post(f"{API_URL}/api/finance-applications", json=app1_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ First application creation failed: {response.status_code}")
        print(response.text)
        return False
    
    app1 = response.json()
    print(f"✅ First application created with priority score: {app1['priority_score']}")
    
    # Create second application
    app2_data = {
        "amount": 150,
        "purpose": "Second application",
        "requested_duration_months": 4,
        "description": "Testing priority system"
    }
    
    print("Creating second finance application")
    response = requests.post(f"{API_URL}/api/finance-applications", json=app2_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Second application creation failed: {response.status_code}")
        print(response.text)
        return False
    
    app2 = response.json()
    print(f"✅ Second application created with priority score: {app2['priority_score']}")
    
    # Create third application
    app3_data = {
        "amount": 200,
        "purpose": "Third application",
        "requested_duration_months": 5,
        "description": "Testing priority system"
    }
    
    print("Creating third finance application")
    response = requests.post(f"{API_URL}/api/finance-applications", json=app3_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Third application creation failed: {response.status_code}")
        print(response.text)
        return False
    
    app3 = response.json()
    print(f"✅ Third application created with priority score: {app3['priority_score']}")
    
    # Verify priority scores
    print("\nVerifying priority scores:")
    print(f"First application: {app1['priority_score']} (expected: 100)")
    print(f"Second application: {app2['priority_score']} (expected: 90)")
    print(f"Third application: {app3['priority_score']} (expected: 80)")
    
    priority_correct = (
        app1['priority_score'] == 100 and
        app2['priority_score'] == 90 and
        app3['priority_score'] == 80
    )
    
    if priority_correct:
        print("✅ Priority system is working correctly!")
    else:
        print("❌ Priority system is not working as expected")
    
    # Check admin view for priority sorting
    print("\nLogging in as admin to check priority sorting")
    admin_login = {
        "email": "admin@fundmanager.com",
        "password": "FundAdmin2024!"
    }
    
    response = requests.post(f"{API_URL}/api/auth/login", json=admin_login)
    
    if response.status_code != 200:
        print(f"❌ Admin login failed: {response.status_code}")
        print(response.text)
        return False
    
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    print("Getting admin applications view")
    response = requests.get(f"{API_URL}/api/admin/applications", headers=admin_headers)
    
    if response.status_code != 200:
        print(f"❌ Admin applications view failed: {response.status_code}")
        print(response.text)
        return False
    
    admin_apps = response.json()
    
    # Filter applications for our test user
    user_apps = [app for app in admin_apps if app["user_id"] == user_id]
    
    if len(user_apps) != 3:
        print(f"❌ Expected 3 applications for test user, found {len(user_apps)}")
        return False
    
    # Check if applications are sorted by priority (highest first)
    priorities = [app["priority_score"] for app in user_apps]
    print(f"Application priorities in admin view: {priorities}")
    
    if priorities == sorted(priorities, reverse=True):
        print("✅ Admin applications are correctly sorted by priority (highest first)")
    else:
        print("❌ Admin applications are not sorted by priority")
    
    return priority_correct

def test_guarantor_system():
    print_separator()
    print("TESTING GUARANTOR SYSTEM")
    print_separator()
    
    # Create users
    user_d = {
        "email": f"user_d_{uuid.uuid4()}@example.com",
        "password": "Test123!",
        "full_name": "User D",
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
    
    guarantor_b = {
        "email": f"guarantor_b_{uuid.uuid4()}@example.com",
        "password": "Test123!",
        "full_name": "Guarantor B",
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
    
    # Register User D
    print(f"Registering User D: {user_d['email']}")
    response = requests.post(f"{API_URL}/api/auth/register", json=user_d)
    
    if response.status_code != 200:
        print(f"❌ User D registration failed: {response.status_code}")
        print(response.text)
        return False
    
    user_d_data = response.json()
    user_d_token = user_d_data["access_token"]
    user_d_id = user_d_data["user"]["id"]
    print(f"✅ User D registered successfully with ID: {user_d_id}")
    
    # Register Guarantor A
    print(f"Registering Guarantor A: {guarantor_a['email']}")
    response = requests.post(f"{API_URL}/api/auth/register", json=guarantor_a)
    
    if response.status_code != 200:
        print(f"❌ Guarantor A registration failed: {response.status_code}")
        print(response.text)
        return False
    
    guarantor_a_data = response.json()
    guarantor_a_token = guarantor_a_data["access_token"]
    guarantor_a_id = guarantor_a_data["user"]["id"]
    print(f"✅ Guarantor A registered successfully with ID: {guarantor_a_id}")
    
    # Register Guarantor B
    print(f"Registering Guarantor B: {guarantor_b['email']}")
    response = requests.post(f"{API_URL}/api/auth/register", json=guarantor_b)
    
    if response.status_code != 200:
        print(f"❌ Guarantor B registration failed: {response.status_code}")
        print(response.text)
        return False
    
    guarantor_b_data = response.json()
    guarantor_b_token = guarantor_b_data["access_token"]
    guarantor_b_id = guarantor_b_data["user"]["id"]
    print(f"✅ Guarantor B registered successfully with ID: {guarantor_b_id}")
    
    # Register Guarantor C
    print(f"Registering Guarantor C: {guarantor_c['email']}")
    response = requests.post(f"{API_URL}/api/auth/register", json=guarantor_c)
    
    if response.status_code != 200:
        print(f"❌ Guarantor C registration failed: {response.status_code}")
        print(response.text)
        return False
    
    guarantor_c_data = response.json()
    guarantor_c_token = guarantor_c_data["access_token"]
    guarantor_c_id = guarantor_c_data["user"]["id"]
    print(f"✅ Guarantor C registered successfully with ID: {guarantor_c_id}")
    
    # Add deposits to make guarantors eligible/ineligible
    # Guarantor A: $600 (eligible)
    headers_a = {"Authorization": f"Bearer {guarantor_a_token}"}
    deposit_data = {"amount": 600, "description": "Initial deposit"}
    
    print("Adding $600 deposit for Guarantor A")
    response = requests.post(f"{API_URL}/api/deposits", json=deposit_data, headers=headers_a)
    
    if response.status_code != 200:
        print(f"❌ Guarantor A deposit failed: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ Guarantor A deposit successful")
    
    # Guarantor B: $300 (not eligible)
    headers_b = {"Authorization": f"Bearer {guarantor_b_token}"}
    deposit_data = {"amount": 300, "description": "Initial deposit"}
    
    print("Adding $300 deposit for Guarantor B")
    response = requests.post(f"{API_URL}/api/deposits", json=deposit_data, headers=headers_b)
    
    if response.status_code != 200:
        print(f"❌ Guarantor B deposit failed: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ Guarantor B deposit successful")
    
    # Guarantor C: $1000 (eligible)
    headers_c = {"Authorization": f"Bearer {guarantor_c_token}"}
    deposit_data = {"amount": 1000, "description": "Initial deposit"}
    
    print("Adding $1000 deposit for Guarantor C")
    response = requests.post(f"{API_URL}/api/deposits", json=deposit_data, headers=headers_c)
    
    if response.status_code != 200:
        print(f"❌ Guarantor C deposit failed: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ Guarantor C deposit successful")
    
    # User D checks eligible guarantors
    headers_d = {"Authorization": f"Bearer {user_d_token}"}
    
    print("User D checking eligible guarantors")
    response = requests.get(f"{API_URL}/api/guarantors/eligible", headers=headers_d)
    
    if response.status_code != 200:
        print(f"❌ Get eligible guarantors failed: {response.status_code}")
        print(response.text)
        return False
    
    eligible_guarantors = response.json()
    eligible_ids = [g["id"] for g in eligible_guarantors]
    
    print(f"Eligible guarantors: {len(eligible_guarantors)}")
    print(f"Guarantor A eligible: {guarantor_a_id in eligible_ids}")
    print(f"Guarantor B eligible: {guarantor_b_id in eligible_ids}")
    print(f"Guarantor C eligible: {guarantor_c_id in eligible_ids}")
    
    if guarantor_a_id in eligible_ids and guarantor_c_id in eligible_ids and guarantor_b_id not in eligible_ids:
        print("✅ Guarantor eligibility check passed")
    else:
        print("❌ Guarantor eligibility check failed")
        return False
    
    # User D creates application with guarantors A and C
    application_data = {
        "amount": 1000,
        "purpose": "Test with guarantors",
        "requested_duration_months": 12,
        "description": "Testing guarantor system",
        "guarantors": [guarantor_a_id, guarantor_c_id]
    }
    
    print("User D creating finance application with guarantors A and C")
    response = requests.post(f"{API_URL}/api/finance-applications", json=application_data, headers=headers_d)
    
    if response.status_code != 200:
        print(f"❌ Finance application creation failed: {response.status_code}")
        print(response.text)
        return False
    
    application = response.json()
    application_id = application["id"]
    print(f"✅ Finance application created with ID: {application_id}")
    
    # Check guarantor requests
    print("Checking guarantor requests for Guarantor A")
    response = requests.get(f"{API_URL}/api/guarantor-requests", headers=headers_a)
    
    if response.status_code != 200:
        print(f"❌ Get guarantor requests for A failed: {response.status_code}")
        print(response.text)
        return False
    
    guarantor_a_requests = response.json()
    
    if len(guarantor_a_requests) == 0:
        print("❌ No guarantor requests found for Guarantor A")
        return False
    
    guarantor_a_request_id = guarantor_a_requests[0]["id"]
    print(f"✅ Guarantor A has {len(guarantor_a_requests)} request(s)")
    
    print("Checking guarantor requests for Guarantor C")
    response = requests.get(f"{API_URL}/api/guarantor-requests", headers=headers_c)
    
    if response.status_code != 200:
        print(f"❌ Get guarantor requests for C failed: {response.status_code}")
        print(response.text)
        return False
    
    guarantor_c_requests = response.json()
    
    if len(guarantor_c_requests) == 0:
        print("❌ No guarantor requests found for Guarantor C")
        return False
    
    guarantor_c_request_id = guarantor_c_requests[0]["id"]
    print(f"✅ Guarantor C has {len(guarantor_c_requests)} request(s)")
    
    # Guarantor A accepts
    print("Guarantor A accepting request")
    response = requests.put(
        f"{API_URL}/api/guarantor-requests/{guarantor_a_request_id}/respond",
        json={"status": "accepted"},
        headers=headers_a
    )
    
    if response.status_code != 200:
        print(f"❌ Guarantor A accept failed: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ Guarantor A accepted request")
    
    # Guarantor C declines
    print("Guarantor C declining request")
    response = requests.put(
        f"{API_URL}/api/guarantor-requests/{guarantor_c_request_id}/respond",
        json={"status": "declined"},
        headers=headers_c
    )
    
    if response.status_code != 200:
        print(f"❌ Guarantor C decline failed: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ Guarantor C declined request")
    
    # Check application status
    print("Checking application status after guarantor responses")
    response = requests.get(f"{API_URL}/api/finance-applications", headers=headers_d)
    
    if response.status_code != 200:
        print(f"❌ Get applications failed: {response.status_code}")
        print(response.text)
        return False
    
    applications = response.json()
    target_app = next((app for app in applications if app["id"] == application_id), None)
    
    if not target_app:
        print("❌ Could not find the application")
        return False
    
    guarantors = target_app["guarantors"]
    guarantor_a_status = next((g["status"] for g in guarantors if g["guarantor_user_id"] == guarantor_a_id), None)
    guarantor_c_status = next((g["status"] for g in guarantors if g["guarantor_user_id"] == guarantor_c_id), None)
    
    print(f"Guarantor A status: {guarantor_a_status}")
    print(f"Guarantor C status: {guarantor_c_status}")
    
    if guarantor_a_status == "accepted" and guarantor_c_status == "declined":
        print("✅ Guarantor statuses updated correctly")
        return True
    else:
        print("❌ Guarantor statuses not updated correctly")
        return False

def test_admin_interface():
    print_separator()
    print("TESTING ADMIN INTERFACE")
    print_separator()
    
    # Login as admin
    admin_login = {
        "email": "admin@fundmanager.com",
        "password": "FundAdmin2024!"
    }
    
    print("Logging in as admin")
    response = requests.post(f"{API_URL}/api/auth/login", json=admin_login)
    
    if response.status_code != 200:
        print(f"❌ Admin login failed: {response.status_code}")
        print(response.text)
        return False
    
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Check admin dashboard
    print("Getting admin dashboard")
    response = requests.get(f"{API_URL}/api/dashboard", headers=admin_headers)
    
    if response.status_code != 200:
        print(f"❌ Admin dashboard failed: {response.status_code}")
        print(response.text)
        return False
    
    dashboard = response.json()
    
    # Check for priority statistics
    if "priority_stats" in dashboard:
        print("✅ Admin dashboard includes priority statistics")
        print(f"Average priority: {dashboard['priority_stats'].get('avg_priority')}")
        print(f"Max priority: {dashboard['priority_stats'].get('max_priority')}")
        print(f"Min priority: {dashboard['priority_stats'].get('min_priority')}")
    else:
        print("❌ Admin dashboard missing priority statistics")
    
    # Check for guarantor statistics
    if "guarantor_stats" in dashboard:
        print("✅ Admin dashboard includes guarantor statistics")
        for stat in dashboard["guarantor_stats"]:
            print(f"{stat['_id']}: {stat['count']}")
    else:
        print("❌ Admin dashboard missing guarantor statistics")
    
    # Check for role distribution
    if "role_distribution" in dashboard:
        print("✅ Admin dashboard includes role distribution")
        for role in dashboard["role_distribution"]:
            print(f"{role['_id']}: {role['count']}")
    else:
        print("❌ Admin dashboard missing role distribution")
    
    # Check applications management
    print("\nChecking applications management")
    response = requests.get(f"{API_URL}/api/admin/applications", headers=admin_headers)
    
    if response.status_code != 200:
        print(f"❌ Admin applications view failed: {response.status_code}")
        print(response.text)
        return False
    
    applications = response.json()
    
    if len(applications) > 0:
        # Check if applications are sorted by priority
        priorities = [app["priority_score"] for app in applications]
        is_sorted = all(priorities[i] >= priorities[i+1] for i in range(len(priorities)-1))
        
        if is_sorted:
            print("✅ Applications are sorted by priority (highest first)")
        else:
            print("❌ Applications are not sorted by priority")
            print(f"Priorities: {priorities}")
    else:
        print("No applications found to check sorting")
    
    # Check user management
    print("\nChecking user management")
    response = requests.get(f"{API_URL}/api/admin/users", headers=admin_headers)
    
    if response.status_code != 200:
        print(f"❌ Admin users view failed: {response.status_code}")
        print(response.text)
        return False
    
    users = response.json()
    
    # Check if guarantor eligibility is shown
    if len(users) > 0 and "is_eligible_guarantor" in users[0]:
        print("✅ User management shows guarantor eligibility")
    else:
        print("❌ User management missing guarantor eligibility")
    
    return True

def main():
    print("Starting Fund Management System Tests")
    
    priority_result = test_priority_system()
    guarantor_result = test_guarantor_system()
    admin_result = test_admin_interface()
    
    print_separator()
    print("TEST SUMMARY")
    print_separator()
    print(f"Priority System: {'✅ PASSED' if priority_result else '❌ FAILED'}")
    print(f"Guarantor System: {'✅ PASSED' if guarantor_result else '❌ FAILED'}")
    print(f"Admin Interface: {'✅ PASSED' if admin_result else '❌ FAILED'}")
    
    if priority_result and guarantor_result and admin_result:
        print("\n✅ ALL TESTS PASSED")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    main()