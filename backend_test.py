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
        self.token = None
        self.user_id = None

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

    def test_03_user_login(self):
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

    def test_04_get_user_profile(self):
        """Test getting user profile"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.api_url}/api/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], self.test_user["email"])
        self.assertEqual(data["full_name"], self.test_user["full_name"])
        print("✅ Get user profile successful")

    def test_05_create_deposit(self):
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

    def test_06_get_deposits(self):
        """Test getting user deposits"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.api_url}/api/deposits", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if len(data) > 0:
            self.assertEqual(data[0]["user_id"], self.user_id)
        print("✅ Get deposits successful")

    def test_07_create_finance_application(self):
        """Test creating a finance application"""
        headers = {"Authorization": f"Bearer {self.token}"}
        application_data = {
            "amount": 500.75,
            "purpose": "Test purpose",
            "requested_duration_months": 6,
            "description": "Test application description"
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
        self.assertEqual(data["requested_duration_months"], application_data["requested_duration_months"])
        self.assertEqual(data["status"], "pending")
        print("✅ Create finance application successful")

    def test_08_get_finance_applications(self):
        """Test getting user finance applications"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.api_url}/api/finance-applications", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if len(data) > 0:
            self.assertEqual(data[0]["user_id"], self.user_id)
        print("✅ Get finance applications successful")

    def test_09_get_repayments(self):
        """Test getting user repayments"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.api_url}/api/repayments", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        # New users shouldn't have repayments yet
        print("✅ Get repayments successful")

    def test_10_get_dashboard(self):
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
        print("✅ Get dashboard successful")

if __name__ == "__main__":
    # Run tests in order
    test_suite = unittest.TestSuite()
    test_suite.addTest(FundManagementAPITest('test_01_health_check'))
    test_suite.addTest(FundManagementAPITest('test_02_user_registration'))
    test_suite.addTest(FundManagementAPITest('test_03_user_login'))
    test_suite.addTest(FundManagementAPITest('test_04_get_user_profile'))
    test_suite.addTest(FundManagementAPITest('test_05_create_deposit'))
    test_suite.addTest(FundManagementAPITest('test_06_get_deposits'))
    test_suite.addTest(FundManagementAPITest('test_07_create_finance_application'))
    test_suite.addTest(FundManagementAPITest('test_08_get_finance_applications'))
    test_suite.addTest(FundManagementAPITest('test_09_get_repayments'))
    test_suite.addTest(FundManagementAPITest('test_10_get_dashboard'))
    
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