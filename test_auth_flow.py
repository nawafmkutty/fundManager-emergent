#!/usr/bin/env python3

import requests
import json

API_URL = "https://63acd9f0-ae1e-442e-a051-257150880f67.preview.emergentagent.com"

def test_auth_flow():
    print("=== TESTING AUTH FLOW STEP BY STEP ===")
    
    # Step 1: Register a new user
    print("\n1. REGISTERING NEW USER")
    test_user = {
        "email": "authtest@example.com",
        "password": "Test123!",
        "full_name": "Auth Test User",
        "country": "Test Country",
        "phone": "1234567890"
    }
    
    response = requests.post(f"{API_URL}/api/auth/register", json=test_user)
    print(f"Registration Status: {response.status_code}")
    
    if response.status_code == 200:
        reg_data = response.json()
        print(f"✅ Registration successful")
        print(f"User ID: {reg_data['user']['id']}")
        print(f"Email: {reg_data['user']['email']}")
        print(f"Token received: {len(reg_data['access_token'])} chars")
        
        # Step 2: Test login with same credentials
        print("\n2. TESTING LOGIN WITH SAME CREDENTIALS")
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        
        login_response = requests.post(f"{API_URL}/api/auth/login", json=login_data)
        print(f"Login Status: {login_response.status_code}")
        print(f"Login Response: {login_response.text}")
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            print(f"✅ Login successful")
            token = login_data["access_token"]
            
            # Step 3: Test authenticated endpoint
            print("\n3. TESTING AUTHENTICATED ENDPOINT")
            headers = {"Authorization": f"Bearer {token}"}
            profile_response = requests.get(f"{API_URL}/api/auth/me", headers=headers)
            print(f"Profile Status: {profile_response.status_code}")
            
            if profile_response.status_code == 200:
                print("✅ Authenticated request successful")
                profile_data = profile_response.json()
                print(f"Profile: {profile_data['full_name']}")
            else:
                print(f"❌ Authenticated request failed: {profile_response.text}")
        else:
            print(f"❌ Login failed")
            print(f"Response body: {login_response.text}")
    else:
        print(f"❌ Registration failed: {response.text}")

if __name__ == "__main__":
    test_auth_flow()