#!/usr/bin/env python3

import os
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta

# Environment setup
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'fund_management')
SECRET_KEY = 'your-secret-key-change-in-production'

# MongoDB setup
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

def test_auth_debug():
    print("=== DEBUG AUTH SYSTEM ===")
    
    # Check if we can connect to MongoDB
    try:
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return
    
    # List collections
    collections = db.list_collection_names()
    print(f"📦 Database collections: {collections}")
    
    # Count users
    user_count = db.users.count_documents({})
    print(f"👥 Total users in database: {user_count}")
    
    # Show recent users (without passwords)
    recent_users = list(db.users.find({}, {"password_hash": 0}).sort("created_at", -1).limit(3))
    print(f"📋 Recent users: {len(recent_users)}")
    for user in recent_users:
        print(f"  - {user.get('email')} | Role: {user.get('role')} | Active: {user.get('is_active')}")
    
    # Test password hashing
    test_password = "Test123!"
    hashed = generate_password_hash(test_password)
    is_valid = check_password_hash(hashed, test_password)
    print(f"🔒 Password hashing test: {is_valid}")
    
    # Test JWT token creation
    test_data = {"sub": "test-user-id"}
    token = jwt.encode(test_data, SECRET_KEY, algorithm="HS256")
    decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    print(f"🎫 JWT token test: {decoded == test_data}")
    
    # Test with a real user if exists
    if user_count > 0:
        user_with_pass = db.users.find_one({}, {"email": 1, "password_hash": 1})
        if user_with_pass:
            print(f"\n🔍 Testing with user: {user_with_pass['email']}")
            # Try with a known password pattern
            test_passwords = ["Test123!", "password", "123456"]
            for pwd in test_passwords:
                result = check_password_hash(user_with_pass['password_hash'], pwd)
                print(f"  Password '{pwd}': {result}")

if __name__ == "__main__":
    test_auth_debug()