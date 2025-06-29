import requests
import unittest
import uuid
import time
from datetime import datetime

# Use the public endpoint for testing
API_URL = "https://dd4fe74c-a1b4-4455-a2ed-10242ff6684b.preview.emergentagent.com"

class FundManagementAPITest(unittest.TestCase):
    def setUp(self):
        self.api_url = API_URL
        self.test_user = {
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "Test123!",
            "full_name": "Test User",
            "country": "Test Country",
            "phone": "1234567890"
        }
        # Create additional users for guarantor testing
        self.guarantor_user_a = {
            "email": f"guarantor_a_{uuid.uuid4()}@example.com",
            "password": "Test123!",
            "full_name": "Guarantor A",
            "country": "Test Country",
            "phone": "1234567890"
        }
        self.guarantor_user_b = {
            "email": f"guarantor_b_{uuid.uuid4()}@example.com",
            "password": "Test123!",
            "full_name": "Guarantor B",
            "country": "Test Country",
            "phone": "1234567890"
        }
        self.guarantor_user_c = {
            "email": f"guarantor_c_{uuid.uuid4()}@example.com",
            "password": "Test123!",
            "full_name": "Guarantor C",
            "country": "Test Country",
            "phone": "1234567890"
        }
        self.token = None
        self.user_id = None
        self.guarantor_a_token = None
        self.guarantor_a_id = None
        self.guarantor_b_token = None
        self.guarantor_b_id = None
        self.guarantor_c_token = None
        self.guarantor_c_id = None
        self.admin_token = None

    def test_01_health_check(self):
        """Test the health check endpoint"""
        response = requests.get(f"{self.api_url}/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)
        print("✅ Health check endpoint is working")

    def test_02_user_registration(self):
        """Test user registration"""
        response = requests.post(
            f"{self.api_url}/api/auth/register",
            json=self.test_user
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], self.test_user["email"])
        self.assertEqual(data["user"]["full_name"], self.test_user["full_name"])
        self.assertEqual(data["user"]["role"], "member")
        
        # Save token and user_id for subsequent tests
        self.token = data["access_token"]
        self.user_id = data["user"]["id"]
        print(f"✅ User registration successful: {self.test_user['email']}")
        
        # Print token for debugging
        print(f"Token: {self.token[:10]}...")
        print(f"User ID: {self.user_id}")

    def test_03_admin_login(self):
        """Test admin login"""
        response = requests.post(
            f"{self.api_url}/api/auth/login",
            json={
                "email": "admin@fundmanager.com",
                "password": "FundAdmin2024!"
            }
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], "admin@fundmanager.com")
        self.assertEqual(data["user"]["role"], "general_admin")
        
        # Save admin token for later tests
        self.admin_token = data["access_token"]
        print("✅ Admin login successful")

    def test_04_user_login(self):
        """Test user login"""
        response = requests.post(
            f"{self.api_url}/api/auth/login",
            json={
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            }
        )
        print(f"Login response status: {response.status_code}")
        print(f"Login response body: {response.text}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], self.test_user["email"])
        
        # Update token
        self.token = data["access_token"]
        print("✅ User login successful")

    def test_05_setup_guarantor_users(self):
        """Register and setup guarantor users"""
        # Register guarantor A
        response = requests.post(
            f"{self.api_url}/api/auth/register",
            json=self.guarantor_user_a
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.guarantor_a_token = data["access_token"]
        self.guarantor_a_id = data["user"]["id"]
        print(f"✅ Guarantor A registered: {self.guarantor_user_a['email']}")
        
        # Register guarantor B
        response = requests.post(
            f"{self.api_url}/api/auth/register",
            json=self.guarantor_user_b
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.guarantor_b_token = data["access_token"]
        self.guarantor_b_id = data["user"]["id"]
        print(f"✅ Guarantor B registered: {self.guarantor_user_b['email']}")
        
        # Register guarantor C
        response = requests.post(
            f"{self.api_url}/api/auth/register",
            json=self.guarantor_user_c
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.guarantor_c_token = data["access_token"]
        self.guarantor_c_id = data["user"]["id"]
        print(f"✅ Guarantor C registered: {self.guarantor_user_c['email']}")
        
        # Add deposits to make guarantors eligible/ineligible
        # Guarantor A: $600 (eligible)
        headers = {"Authorization": f"Bearer {self.guarantor_a_token}"}
        deposit_data = {"amount": 600, "description": "Initial deposit"}
        response = requests.post(
            f"{self.api_url}/api/deposits",
            json=deposit_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        print("✅ Guarantor A deposit ($600) successful")
        
        # Guarantor B: $300 (not eligible)
        headers = {"Authorization": f"Bearer {self.guarantor_b_token}"}
        deposit_data = {"amount": 300, "description": "Initial deposit"}
        response = requests.post(
            f"{self.api_url}/api/deposits",
            json=deposit_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        print("✅ Guarantor B deposit ($300) successful")
        
        # Guarantor C: $1000 (eligible)
        headers = {"Authorization": f"Bearer {self.guarantor_c_token}"}
        deposit_data = {"amount": 1000, "description": "Initial deposit"}
        response = requests.post(
            f"{self.api_url}/api/deposits",
            json=deposit_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        print("✅ Guarantor C deposit ($1000) successful")

    def test_06_get_user_profile(self):
        """Test getting user profile"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.api_url}/api/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], self.test_user["email"])
        self.assertEqual(data["full_name"], self.test_user["full_name"])
        print("✅ Get user profile successful")

    def test_07_create_deposit(self):
        """Test creating a deposit"""
        headers = {"Authorization": f"Bearer {self.token}"}
        deposit_data = {
            "amount": 100.50,
            "description": "Test deposit"
        }
        response = requests.post(
            f"{self.api_url}/api/deposits",
            json=deposit_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["amount"], deposit_data["amount"])
        self.assertEqual(data["description"], deposit_data["description"])
        self.assertEqual(data["status"], "completed")
        print("✅ Create deposit successful")

    def test_08_get_deposits(self):
        """Test getting user deposits"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.api_url}/api/deposits", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if len(data) > 0:
            self.assertEqual(data[0]["user_id"], self.user_id)
        print("✅ Get deposits successful")

    def test_09_get_eligible_guarantors(self):
        """Test getting eligible guarantors"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.api_url}/api/guarantors/eligible", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        
        # Check if guarantors with sufficient deposits are in the list
        guarantor_ids = [g["id"] for g in data]
        self.assertIn(self.guarantor_a_id, guarantor_ids, "Guarantor A should be eligible")
        self.assertIn(self.guarantor_c_id, guarantor_ids, "Guarantor C should be eligible")
        self.assertNotIn(self.guarantor_b_id, guarantor_ids, "Guarantor B should not be eligible")
        
        print("✅ Get eligible guarantors successful")

    def test_10_create_finance_application_with_guarantors(self):
        """Test creating a finance application with guarantors"""
        headers = {"Authorization": f"Bearer {self.token}"}
        application_data = {
            "amount": 500.75,
            "purpose": "Test purpose with guarantors",
            "requested_duration_months": 6,
            "description": "Test application with guarantors",
            "guarantors": [self.guarantor_a_id, self.guarantor_c_id]
        }
        response = requests.post(
            f"{self.api_url}/api/finance-applications",
            json=application_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["amount"], application_data["amount"])
        self.assertEqual(data["purpose"], application_data["purpose"])
        self.assertEqual(data["status"], "pending")
        
        # Check priority score for first application (should be 100)
        self.assertEqual(data["priority_score"], 100, "First application should have priority score of 100")
        self.assertEqual(data["previous_finances_count"], 0, "First application should have 0 previous finances")
        
        # Check guarantors
        self.assertEqual(len(data["guarantors"]), 2, "Application should have 2 guarantors")
        guarantor_ids = [g["guarantor_user_id"] for g in data["guarantors"]]
        self.assertIn(self.guarantor_a_id, guarantor_ids)
        self.assertIn(self.guarantor_c_id, guarantor_ids)
        
        # Save application ID for later tests
        self.application_id = data["id"]
        print("✅ Create finance application with guarantors successful")

    def test_11_create_second_finance_application(self):
        """Test creating a second finance application to check priority"""
        headers = {"Authorization": f"Bearer {self.token}"}
        application_data = {
            "amount": 300.50,
            "purpose": "Second application",
            "requested_duration_months": 3,
            "description": "Testing priority system"
        }
        response = requests.post(
            f"{self.api_url}/api/finance-applications",
            json=application_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check priority score for second application (should be 90)
        self.assertEqual(data["priority_score"], 90, "Second application should have priority score of 90")
        self.assertEqual(data["previous_finances_count"], 1, "Second application should have 1 previous finance")
        
        print("✅ Create second finance application successful")

    def test_12_create_third_finance_application(self):
        """Test creating a third finance application to check priority"""
        headers = {"Authorization": f"Bearer {self.token}"}
        application_data = {
            "amount": 200.25,
            "purpose": "Third application",
            "requested_duration_months": 2,
            "description": "Testing priority system further"
        }
        response = requests.post(
            f"{self.api_url}/api/finance-applications",
            json=application_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check priority score for third application (should be 80)
        self.assertEqual(data["priority_score"], 80, "Third application should have priority score of 80")
        self.assertEqual(data["previous_finances_count"], 2, "Third application should have 2 previous finances")
        
        print("✅ Create third finance application successful")

    def test_13_get_finance_applications(self):
        """Test getting user finance applications"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.api_url}/api/finance-applications", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3, "Should have 3 applications")
        
        # Applications should be sorted by created_at (newest first)
        self.assertEqual(data[0]["priority_score"], 80, "Most recent application should have priority 80")
        self.assertEqual(data[1]["priority_score"], 90, "Second application should have priority 90")
        self.assertEqual(data[2]["priority_score"], 100, "First application should have priority 100")
        
        print("✅ Get finance applications successful")

    def test_14_check_guarantor_requests(self):
        """Test checking guarantor requests"""
        # Check guarantor A's requests
        headers = {"Authorization": f"Bearer {self.guarantor_a_token}"}
        response = requests.get(f"{self.api_url}/api/guarantor-requests", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1, "Guarantor A should have 1 request")
        self.assertEqual(data[0]["status"], "pending", "Request should be pending")
        self.guarantor_a_request_id = data[0]["id"]
        
        # Check guarantor C's requests
        headers = {"Authorization": f"Bearer {self.guarantor_c_token}"}
        response = requests.get(f"{self.api_url}/api/guarantor-requests", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1, "Guarantor C should have 1 request")
        self.assertEqual(data[0]["status"], "pending", "Request should be pending")
        self.guarantor_c_request_id = data[0]["id"]
        
        print("✅ Check guarantor requests successful")

    def test_15_respond_to_guarantor_requests(self):
        """Test responding to guarantor requests"""
        # Guarantor A accepts
        headers = {"Authorization": f"Bearer {self.guarantor_a_token}"}
        response = requests.put(
            f"{self.api_url}/api/guarantor-requests/{self.guarantor_a_request_id}/respond",
            json={"status": "accepted"},
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        
        # Guarantor C declines
        headers = {"Authorization": f"Bearer {self.guarantor_c_token}"}
        response = requests.put(
            f"{self.api_url}/api/guarantor-requests/{self.guarantor_c_request_id}/respond",
            json={"status": "declined"},
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify guarantor A's request status
        headers = {"Authorization": f"Bearer {self.guarantor_a_token}"}
        response = requests.get(f"{self.api_url}/api/guarantor-requests", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data[0]["status"], "accepted", "Guarantor A's request should be accepted")
        
        # Verify guarantor C's request status
        headers = {"Authorization": f"Bearer {self.guarantor_c_token}"}
        response = requests.get(f"{self.api_url}/api/guarantor-requests", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data[0]["status"], "declined", "Guarantor C's request should be declined")
        
        print("✅ Respond to guarantor requests successful")

    def test_16_check_admin_applications(self):
        """Test checking admin applications view for priority sorting"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(f"{self.api_url}/api/admin/applications", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        
        # Admin view should sort by priority (highest first)
        priorities = [app["priority_score"] for app in data if app["user_id"] == self.user_id]
        self.assertEqual(priorities, sorted(priorities, reverse=True), "Applications should be sorted by priority (highest first)")
        
        print("✅ Check admin applications view successful")

    def test_17_get_repayments(self):
        """Test getting user repayments"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.api_url}/api/repayments", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        # New users shouldn't have repayments yet
        print("✅ Get repayments successful")

    def test_18_get_dashboard(self):
        """Test getting dashboard data"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.api_url}/api/dashboard", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_deposits", data)
        self.assertIn("total_applications", data)
        self.assertIn("pending_repayments", data)
        self.assertIn("recent_deposits", data)
        self.assertIn("recent_applications", data)
        
        # Check guarantor eligibility
        self.assertIn("is_eligible_guarantor", data)
        self.assertIn("minimum_deposit_for_guarantor", data)
        
        print("✅ Get dashboard successful")

    def test_19_test_invalid_guarantor(self):
        """Test creating application with invalid guarantor"""
        headers = {"Authorization": f"Bearer {self.token}"}
        application_data = {
            "amount": 200.00,
            "purpose": "Test invalid guarantor",
            "requested_duration_months": 3,
            "description": "Should fail with ineligible guarantor",
            "guarantors": [self.guarantor_b_id]  # Guarantor B has insufficient deposits
        }
        response = requests.post(
            f"{self.api_url}/api/finance-applications",
            json=application_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("not eligible", data["detail"].lower())
        
        print("✅ Test invalid guarantor successful")

if __name__ == "__main__":
    # Run tests in order
    test_suite = unittest.TestSuite()
    test_suite.addTest(FundManagementAPITest('test_01_health_check'))
    test_suite.addTest(FundManagementAPITest('test_02_user_registration'))
    test_suite.addTest(FundManagementAPITest('test_03_admin_login'))
    test_suite.addTest(FundManagementAPITest('test_04_user_login'))
    test_suite.addTest(FundManagementAPITest('test_05_setup_guarantor_users'))
    test_suite.addTest(FundManagementAPITest('test_06_get_user_profile'))
    test_suite.addTest(FundManagementAPITest('test_07_create_deposit'))
    test_suite.addTest(FundManagementAPITest('test_08_get_deposits'))
    test_suite.addTest(FundManagementAPITest('test_09_get_eligible_guarantors'))
    test_suite.addTest(FundManagementAPITest('test_10_create_finance_application_with_guarantors'))
    test_suite.addTest(FundManagementAPITest('test_11_create_second_finance_application'))
    test_suite.addTest(FundManagementAPITest('test_12_create_third_finance_application'))
    test_suite.addTest(FundManagementAPITest('test_13_get_finance_applications'))
    test_suite.addTest(FundManagementAPITest('test_14_check_guarantor_requests'))
    test_suite.addTest(FundManagementAPITest('test_15_respond_to_guarantor_requests'))
    test_suite.addTest(FundManagementAPITest('test_16_check_admin_applications'))
    test_suite.addTest(FundManagementAPITest('test_17_get_repayments'))
    test_suite.addTest(FundManagementAPITest('test_18_get_dashboard'))
    test_suite.addTest(FundManagementAPITest('test_19_test_invalid_guarantor'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n=== TEST SUMMARY ===")
    print(f"Total tests: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n=== FAILURES ===")
        for test, error in result.failures:
            print(f"\n{test}")
            print(error)
    
    if result.errors:
        print("\n=== ERRORS ===")
        for test, error in result.errors:
            print(f"\n{test}")
            print(error)