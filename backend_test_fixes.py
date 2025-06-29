import requests
import unittest
import uuid
import time
import json
from datetime import datetime

# Use the public endpoint for testing
API_URL = "https://63acd9f0-ae1e-442e-a051-257150880f67.preview.emergentagent.com"

# Enable debug mode to print detailed request/response info
DEBUG = True

def debug_print(message):
    if DEBUG:
        print(f"DEBUG: {message}")

class FundManagementFixesTest(unittest.TestCase):
    def setUp(self):
        self.api_url = API_URL
        self.admin_credentials = {
            "email": "admin@fundmanager.com",
            "password": "FundAdmin2024!"
        }
        self.test_user = {
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "Test123!",
            "full_name": "Test User",
            "country": "Test Country",
            "phone": "1234567890"
        }
        self.guarantor_user = {
            "email": f"guarantor_{uuid.uuid4()}@example.com",
            "password": "Test123!",
            "full_name": "Guarantor User",
            "country": "Test Country",
            "phone": "1234567890"
        }
        self.admin_token = None
        self.user_token = None
        self.user_id = None
        self.guarantor_token = None
        self.guarantor_id = None
        self.application_id = None
        self.guarantor_request_id = None

    def test_01_admin_login(self):
        """Test admin login"""
        print("\n🔍 Testing admin login...")
        response = requests.post(
            f"{self.api_url}/api/auth/login",
            json=self.admin_credentials
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], self.admin_credentials["email"])
        self.assertEqual(data["user"]["role"], "general_admin")
        
        # Save admin token for later tests
        self.admin_token = data["access_token"]
        print("✅ Admin login successful")

    def test_02_user_registration(self):
        """Test user registration"""
        print("\n🔍 Testing user registration...")
        response = requests.post(
            f"{self.api_url}/api/auth/register",
            json=self.test_user
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], self.test_user["email"])
        
        # Save token and user_id for subsequent tests
        self.user_token = data["access_token"]
        self.user_id = data["user"]["id"]
        print(f"✅ User registration successful: {self.test_user['email']}")

    def test_03_guarantor_registration(self):
        """Test guarantor registration"""
        print("\n🔍 Testing guarantor registration...")
        response = requests.post(
            f"{self.api_url}/api/auth/register",
            json=self.guarantor_user
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], self.guarantor_user["email"])
        
        # Save token and user_id for subsequent tests
        self.guarantor_token = data["access_token"]
        self.guarantor_id = data["user"]["id"]
        print(f"✅ Guarantor registration successful: {self.guarantor_user['email']}")

    def test_04_create_guarantor_deposit(self):
        """Test creating a deposit for guarantor"""
        print("\n🔍 Testing guarantor deposit creation...")
        if not self.guarantor_token:
            self.skipTest("Guarantor token not found")
            
        headers = {"Authorization": f"Bearer {self.guarantor_token}"}
        debug_print(f"Using guarantor token: {self.guarantor_token[:20]}...")
        
        deposit_data = {
            "amount": 1000.00,
            "description": "Initial deposit for guarantor eligibility"
        }
        debug_print(f"Deposit data: {deposit_data}")
        
        response = requests.post(
            f"{self.api_url}/api/deposits",
            json=deposit_data,
            headers=headers
        )
        debug_print(f"Response status: {response.status_code}")
        debug_print(f"Response body: {response.text}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["amount"], deposit_data["amount"])
        self.assertEqual(data["status"], "completed")
        print("✅ Guarantor deposit successful")

    def test_05_get_deposits_endpoint(self):
        """Test GET /api/deposits endpoint (previously had ObjectId serialization issues)"""
        print("\n🔍 Testing GET /api/deposits endpoint...")
        headers = {"Authorization": f"Bearer {self.guarantor_token}"}
        response = requests.get(f"{self.api_url}/api/deposits", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if len(data) > 0:
            self.assertEqual(data[0]["user_id"], self.guarantor_id)
            # Check that the id field is properly serialized
            self.assertIsInstance(data[0]["id"], str)
        print("✅ GET /api/deposits endpoint working correctly")

    def test_06_create_finance_application(self):
        """Test creating a finance application with guarantor"""
        print("\n🔍 Testing finance application creation...")
        headers = {"Authorization": f"Bearer {self.user_token}"}
        application_data = {
            "amount": 500.00,
            "purpose": "Test application with guarantor",
            "requested_duration_months": 6,
            "description": "Testing ObjectId serialization fixes",
            "guarantors": [self.guarantor_id]
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
        
        # Save application ID for later tests
        self.application_id = data["id"]
        print("✅ Finance application created successfully")

    def test_07_get_finance_applications_endpoint(self):
        """Test GET /api/finance-applications endpoint (previously had ObjectId serialization issues)"""
        print("\n🔍 Testing GET /api/finance-applications endpoint...")
        headers = {"Authorization": f"Bearer {self.user_token}"}
        response = requests.get(f"{self.api_url}/api/finance-applications", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if len(data) > 0:
            # Check that the id field is properly serialized
            self.assertIsInstance(data[0]["id"], str)
            # Check that guarantors are properly serialized
            if data[0]["guarantors"]:
                self.assertIsInstance(data[0]["guarantors"][0]["id"], str)
        print("✅ GET /api/finance-applications endpoint working correctly")

    def test_08_get_guarantor_requests_endpoint(self):
        """Test GET /api/guarantor-requests endpoint (previously had ObjectId serialization issues)"""
        print("\n🔍 Testing GET /api/guarantor-requests endpoint...")
        headers = {"Authorization": f"Bearer {self.guarantor_token}"}
        response = requests.get(f"{self.api_url}/api/guarantor-requests", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if len(data) > 0:
            # Check that the id field is properly serialized
            self.assertIsInstance(data[0]["id"], str)
            # Save guarantor request ID for later tests
            self.guarantor_request_id = data[0]["id"]
            # Check that application_details are properly serialized
            if "application_details" in data[0]:
                self.assertIsInstance(data[0]["application_details"]["id"], str)
        print("✅ GET /api/guarantor-requests endpoint working correctly")

    def test_09_respond_to_guarantor_request(self):
        """Test responding to guarantor request"""
        print("\n🔍 Testing guarantor request response...")
        if not self.guarantor_request_id:
            self.skipTest("Guarantor request ID not found")
            
        headers = {"Authorization": f"Bearer {self.guarantor_token}"}
        response = requests.put(
            f"{self.api_url}/api/guarantor-requests/{self.guarantor_request_id}/respond",
            json={"status": "accepted"},
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        print("✅ Guarantor request accepted successfully")

    def test_10_approve_application(self):
        """Test approving the finance application as admin"""
        print("\n🔍 Testing application approval...")
        if not self.application_id:
            self.skipTest("Application ID not found")
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        approval_data = {
            "action": "approve",
            "review_notes": "Approved for testing",
            "conditions": "None",
            "recommended_amount": 500.00
        }
        response = requests.put(
            f"{self.api_url}/api/admin/applications/{self.application_id}/approve",
            json=approval_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "approved")
        print("✅ Application approved successfully")

    def test_11_disburse_application(self):
        """Test disbursing the approved application"""
        print("\n🔍 Testing application disbursement...")
        if not self.application_id:
            self.skipTest("Application ID not found")
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        disbursement_data = {
            "notes": "Test disbursement",
            "reference_number": f"TEST-{uuid.uuid4().hex[:8].upper()}",
            "disbursement_method": "bank_transfer"
        }
        response = requests.post(
            f"{self.api_url}/api/admin/applications/{self.application_id}/disburse",
            json=disbursement_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("disbursement", data)
        self.assertIn("payment_schedules", data)
        print("✅ Application disbursed successfully")

    def test_12_get_payment_schedules_endpoint(self):
        """Test GET /api/payment-schedules endpoint (previously had ObjectId serialization issues)"""
        print("\n🔍 Testing GET /api/payment-schedules endpoint...")
        headers = {"Authorization": f"Bearer {self.user_token}"}
        response = requests.get(f"{self.api_url}/api/payment-schedules", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if len(data) > 0:
            # Check that the id field is properly serialized
            self.assertIsInstance(data[0]["id"], str)
            # Check that application_id is properly serialized
            self.assertIsInstance(data[0]["application_id"], str)
            # Check that disbursement_id is properly serialized
            self.assertIsInstance(data[0]["disbursement_id"], str)
        print("✅ GET /api/payment-schedules endpoint working correctly")

    def test_13_get_admin_disbursements_endpoint(self):
        """Test GET /api/admin/disbursements endpoint (previously had ObjectId serialization issues)"""
        print("\n🔍 Testing GET /api/admin/disbursements endpoint...")
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(f"{self.api_url}/api/admin/disbursements", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if len(data) > 0:
            # Check that the id field is properly serialized
            self.assertIsInstance(data[0]["id"], str)
            # Check that application_id is properly serialized
            self.assertIsInstance(data[0]["application_id"], str)
            # Check that application_details are properly serialized if present
            if "application_details" in data[0]:
                self.assertIsInstance(data[0]["application_details"], dict)
        print("✅ GET /api/admin/disbursements endpoint working correctly")

if __name__ == "__main__":
    # Run tests in order
    test_suite = unittest.TestSuite()
    test_suite.addTest(FundManagementFixesTest('test_01_admin_login'))
    test_suite.addTest(FundManagementFixesTest('test_02_user_registration'))
    test_suite.addTest(FundManagementFixesTest('test_03_guarantor_registration'))
    test_suite.addTest(FundManagementFixesTest('test_04_create_guarantor_deposit'))
    test_suite.addTest(FundManagementFixesTest('test_05_get_deposits_endpoint'))
    test_suite.addTest(FundManagementFixesTest('test_06_create_finance_application'))
    test_suite.addTest(FundManagementFixesTest('test_07_get_finance_applications_endpoint'))
    test_suite.addTest(FundManagementFixesTest('test_08_get_guarantor_requests_endpoint'))
    test_suite.addTest(FundManagementFixesTest('test_09_respond_to_guarantor_request'))
    test_suite.addTest(FundManagementFixesTest('test_10_approve_application'))
    test_suite.addTest(FundManagementFixesTest('test_11_disburse_application'))
    test_suite.addTest(FundManagementFixesTest('test_12_get_payment_schedules_endpoint'))
    test_suite.addTest(FundManagementFixesTest('test_13_get_admin_disbursements_endpoint'))
    
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