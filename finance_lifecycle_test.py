import requests
import unittest
import uuid
import time
from datetime import datetime

# Use the public endpoint for testing
API_URL = "https://63acd9f0-ae1e-442e-a051-257150880f67.preview.emergentagent.com"

class FinanceLifecycleTest(unittest.TestCase):
    def setUp(self):
        self.api_url = API_URL
        # Create test users
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
        
        # Initialize tokens and IDs
        self.admin_token = None
        self.user_token = None
        self.user_id = None
        self.guarantor_token = None
        self.guarantor_id = None
        self.application_id = None
        self.disbursement_id = None
        
    def test_01_setup_users(self):
        """Setup admin, regular user, and guarantor"""
        # Admin login
        response = requests.post(
            f"{self.api_url}/api/auth/login",
            json=self.admin_credentials
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.admin_token = data["access_token"]
        print(f"✅ Admin login successful: {self.admin_token[:10]}...")
        
        # Register test user
        response = requests.post(
            f"{self.api_url}/api/auth/register",
            json=self.test_user
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.user_token = data["access_token"]
        self.user_id = data["user"]["id"]
        print(f"✅ Test user registered: {self.test_user['email']}")
        print(f"User token: {self.user_token[:10]}...")
        
        # Register guarantor
        response = requests.post(
            f"{self.api_url}/api/auth/register",
            json=self.guarantor_user
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.guarantor_token = data["access_token"]
        self.guarantor_id = data["user"]["id"]
        print(f"✅ Guarantor registered: {self.guarantor_user['email']}")
        print(f"Guarantor token: {self.guarantor_token[:10]}...")
        
        # Make guarantor eligible by adding deposit
        headers = {"Authorization": f"Bearer {self.guarantor_token}"}
        deposit_data = {"amount": 1000, "description": "Initial deposit"}
        response = requests.post(
            f"{self.api_url}/api/deposits",
            json=deposit_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        print("✅ Guarantor deposit ($1000) successful")
        
    def test_02_fund_pool_initialization(self):
        """Test fund pool initialization and GET endpoint"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Check initial fund pool
        response = requests.get(
            f"{self.api_url}/api/admin/fund-pool",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify fund pool structure
        self.assertIn("total_deposits", data)
        self.assertIn("total_disbursed", data)
        self.assertIn("total_repaid", data)
        self.assertIn("available_balance", data)
        self.assertIn("total_receivables", data)
        
        # Store initial values for later comparison
        self.initial_fund_pool = data
        print("✅ Fund pool initialization verified")
        
    def test_03_create_deposit(self):
        """Create deposit to fund the pool"""
        headers = {"Authorization": f"Bearer {self.user_token}"}
        deposit_data = {
            "amount": 2000,
            "description": "Funding for loan application"
        }
        response = requests.post(
            f"{self.api_url}/api/deposits",
            json=deposit_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["amount"], deposit_data["amount"])
        print("✅ User deposit ($2000) successful")
        
        # Verify fund pool was updated
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(
            f"{self.api_url}/api/admin/fund-pool",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Fund pool should reflect the new deposit
        self.assertGreaterEqual(data["total_deposits"], self.initial_fund_pool["total_deposits"] + 2000)
        self.assertGreaterEqual(data["available_balance"], self.initial_fund_pool["available_balance"] + 2000)
        print("✅ Fund pool updated after deposit")
        
    def test_04_create_finance_application(self):
        """Create finance application with guarantor"""
        headers = {"Authorization": f"Bearer {self.user_token}"}
        application_data = {
            "amount": 1500,
            "purpose": "Test finance lifecycle",
            "requested_duration_months": 6,
            "description": "Testing complete finance lifecycle",
            "guarantors": [self.guarantor_id]
        }
        response = requests.post(
            f"{self.api_url}/api/finance-applications",
            json=application_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.application_id = data["id"]
        print(f"✅ Finance application created: {self.application_id}")
        
    def test_05_guarantor_accepts(self):
        """Guarantor accepts the application"""
        # Get guarantor request ID
        headers = {"Authorization": f"Bearer {self.guarantor_token}"}
        response = requests.get(
            f"{self.api_url}/api/guarantor-requests",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data), 0, "Guarantor should have at least one request")
        guarantor_request_id = data[0]["id"]
        
        # Accept the request
        response = requests.put(
            f"{self.api_url}/api/guarantor-requests/{guarantor_request_id}/respond",
            json={"status": "accepted"},
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        print("✅ Guarantor accepted the application")
        
    def test_06_admin_approves_application(self):
        """Admin approves the finance application"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        approval_data = {
            "action": "approve",
            "review_notes": "Approved for testing",
            "conditions": "None",
            "recommended_amount": 1500
        }
        response = requests.put(
            f"{self.api_url}/api/admin/applications/{self.application_id}/approve",
            json=approval_data,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "approved")
        print("✅ Admin approved the application")
        
    def test_07_check_ready_for_disbursement(self):
        """Check applications ready for disbursement"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(
            f"{self.api_url}/api/admin/ready-for-disbursement",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Find our application in the list
        application = next((app for app in data if app["id"] == self.application_id), None)
        self.assertIsNotNone(application, "Application should be ready for disbursement")
        self.assertTrue(application["ready_for_disbursement"], "Application should be ready for disbursement")
        print("✅ Application is ready for disbursement")
        
    def test_08_disburse_funds(self):
        """Disburse funds for the approved application"""
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
        
        # Verify disbursement data
        self.assertIn("disbursement", data)
        self.assertIn("payment_schedules", data)
        self.assertIn("fund_pool", data)
        
        # Store disbursement ID for later
        self.disbursement_id = data["disbursement"]["id"]
        
        # Verify payment schedules were created
        self.assertEqual(len(data["payment_schedules"]), 6)  # 6 months duration
        
        # Verify fund pool was updated
        self.assertEqual(data["fund_pool"]["total_disbursed"], 
                        self.initial_fund_pool["total_disbursed"] + 1500)
        
        print("✅ Funds disbursed successfully")
        
    def test_09_check_disbursements(self):
        """Check disbursements list"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.get(
            f"{self.api_url}/api/admin/disbursements",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Find our disbursement in the list
        disbursement = next((d for d in data if d["id"] == self.disbursement_id), None)
        self.assertIsNotNone(disbursement, "Disbursement should be in the list")
        self.assertEqual(disbursement["status"], "disbursed")
        self.assertEqual(disbursement["disbursed_amount"], 1500)
        print("✅ Disbursement verified in list")
        
    def test_10_check_payment_schedules(self):
        """Check payment schedules for the user"""
        headers = {"Authorization": f"Bearer {self.user_token}"}
        response = requests.get(
            f"{self.api_url}/api/payment-schedules",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify payment schedules for our application
        schedules = [s for s in data if s["application_id"] == self.application_id]
        self.assertEqual(len(schedules), 6)  # 6 months duration
        
        # Verify schedule details
        for schedule in schedules:
            self.assertIn("principal_amount", schedule)
            self.assertIn("interest_amount", schedule)
            self.assertIn("due_date", schedule)
            self.assertEqual(schedule["status"], "scheduled")
            
        print("✅ Payment schedules verified")
        
    def test_11_recalculate_fund_pool(self):
        """Test fund pool recalculation"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        response = requests.post(
            f"{self.api_url}/api/admin/fund-pool/recalculate",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify recalculated fund pool
        self.assertGreaterEqual(data["total_deposits"], 3000)  # 2000 (user) + 1000 (guarantor)
        self.assertGreaterEqual(data["total_disbursed"], 1500)
        self.assertEqual(data["total_repaid"], 0)  # No repayments yet
        self.assertGreaterEqual(data["available_balance"], 1500)  # 3000 - 1500
        self.assertEqual(data["total_receivables"], 1500)  # 1500 disbursed, 0 repaid
        
        print("✅ Fund pool recalculation verified")
        
    def test_12_verify_application_status(self):
        """Verify application status after disbursement"""
        headers = {"Authorization": f"Bearer {self.user_token}"}
        response = requests.get(
            f"{self.api_url}/api/finance-applications",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Find our application
        application = next((app for app in data if app["id"] == self.application_id), None)
        self.assertIsNotNone(application, "Application should be in the list")
        self.assertEqual(application["status"], "disbursed")
        
        print("✅ Application status updated to disbursed")

if __name__ == "__main__":
    # Run tests in order
    test_suite = unittest.TestSuite()
    test_suite.addTest(FinanceLifecycleTest('test_01_setup_users'))
    test_suite.addTest(FinanceLifecycleTest('test_02_fund_pool_initialization'))
    test_suite.addTest(FinanceLifecycleTest('test_03_create_deposit'))
    test_suite.addTest(FinanceLifecycleTest('test_04_create_finance_application'))
    test_suite.addTest(FinanceLifecycleTest('test_05_guarantor_accepts'))
    test_suite.addTest(FinanceLifecycleTest('test_06_admin_approves_application'))
    test_suite.addTest(FinanceLifecycleTest('test_07_check_ready_for_disbursement'))
    test_suite.addTest(FinanceLifecycleTest('test_08_disburse_funds'))
    test_suite.addTest(FinanceLifecycleTest('test_09_check_disbursements'))
    test_suite.addTest(FinanceLifecycleTest('test_10_check_payment_schedules'))
    test_suite.addTest(FinanceLifecycleTest('test_11_recalculate_fund_pool'))
    test_suite.addTest(FinanceLifecycleTest('test_12_verify_application_status'))
    
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