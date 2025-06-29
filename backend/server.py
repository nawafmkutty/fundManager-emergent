from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, List
import uuid
from enum import Enum

# Environment setup
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'fund_management')
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# MongoDB setup
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# FastAPI app
app = FastAPI(title="Fund Management System API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Enums
class UserRole(str, Enum):
    MEMBER = "member"
    COUNTRY_COORDINATOR = "country_coordinator"
    FUND_ADMIN = "fund_admin"
    GENERAL_ADMIN = "general_admin"

class ApplicationStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISBURSED = "disbursed"

class RepaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"

# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str
    country: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class DepositCreate(BaseModel):
    amount: float = Field(gt=0)
    description: Optional[str] = None

class FinanceApplicationCreate(BaseModel):
    amount: float = Field(gt=0)
    purpose: str
    requested_duration_months: int = Field(gt=0)
    description: Optional[str] = None

class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    review_notes: Optional[str] = None

class UserRoleUpdate(BaseModel):
    user_id: str
    new_role: UserRole

class User(BaseModel):
    id: str
    email: str
    full_name: str
    country: str
    phone: Optional[str]
    role: UserRole
    created_at: datetime
    is_active: bool

class Deposit(BaseModel):
    id: str
    user_id: str
    amount: float
    description: Optional[str]
    created_at: datetime
    status: str

class FinanceApplication(BaseModel):
    id: str
    user_id: str
    amount: float
    purpose: str
    requested_duration_months: int
    description: Optional[str]
    status: ApplicationStatus
    priority_score: Optional[float]
    created_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    review_notes: Optional[str]

class Repayment(BaseModel):
    id: str
    user_id: str
    application_id: str
    amount: float
    due_date: datetime
    paid_date: Optional[datetime]
    status: RepaymentStatus
    installment_number: int

# Role permissions
ROLE_PERMISSIONS = {
    UserRole.MEMBER: ["view_own_data", "create_deposits", "create_applications"],
    UserRole.COUNTRY_COORDINATOR: ["view_own_data", "create_deposits", "create_applications", "view_country_data", "review_applications"],
    UserRole.FUND_ADMIN: ["view_own_data", "create_deposits", "create_applications", "view_all_data", "review_applications", "manage_disbursals"],
    UserRole.GENERAL_ADMIN: ["all_permissions", "manage_users", "assign_roles", "system_config"]
}

# Utility functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(user_id: str = Depends(verify_token)):
    user = db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def require_role(required_roles: List[UserRole]):
    def role_checker(current_user = Depends(get_current_user)):
        user_role = UserRole(current_user["role"])
        if user_role not in required_roles:
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied. Required roles: {[role.value for role in required_roles]}"
            )
        return current_user
    return role_checker

def create_admin_user():
    """Create default admin user if not exists"""
    admin_email = "admin@fundmanager.com"
    admin_user = db.users.find_one({"email": admin_email})
    
    if not admin_user:
        admin_id = str(uuid.uuid4())
        admin_password = "FundAdmin2024!"
        hashed_password = generate_password_hash(admin_password)
        
        admin_doc = {
            "id": admin_id,
            "email": admin_email,
            "password_hash": hashed_password,
            "full_name": "System Administrator",
            "country": "Global",
            "phone": "+1-555-0123",
            "role": UserRole.GENERAL_ADMIN.value,
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        db.users.insert_one(admin_doc)
        print(f"✅ Admin user created:")
        print(f"   Email: {admin_email}")
        print(f"   Password: {admin_password}")
        print(f"   Role: {UserRole.GENERAL_ADMIN.value}")

# Create admin user on startup
create_admin_user()

# API Routes

@app.get("/api/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/api/auth/register")
async def register(user: UserRegister):
    # Check if user exists
    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = str(uuid.uuid4())
    hashed_password = generate_password_hash(user.password)
    
    user_doc = {
        "id": user_id,
        "email": user.email,
        "password_hash": hashed_password,
        "full_name": user.full_name,
        "country": user.country,
        "phone": user.phone,
        "role": UserRole.MEMBER.value,
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    db.users.insert_one(user_doc)
    
    # Create access token
    access_token = create_access_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(**{k: v for k, v in user_doc.items() if k != "password_hash"})
    }

@app.post("/api/auth/login")
async def login(user: UserLogin):
    # Find user
    user_doc = db.users.find_one({"email": user.email})
    if not user_doc or not check_password_hash(user_doc["password_hash"], user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user_doc["is_active"]:
        raise HTTPException(status_code=401, detail="Account is deactivated")
    
    # Create access token
    access_token = create_access_token(data={"sub": user_doc["id"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": User(**{k: v for k, v in user_doc.items() if k != "password_hash"})
    }

@app.get("/api/auth/me")
async def get_current_user_profile(current_user = Depends(get_current_user)):
    return User(**{k: v for k, v in current_user.items() if k != "password_hash"})

# Member endpoints (original functionality)
@app.post("/api/deposits")
async def create_deposit(deposit: DepositCreate, current_user = Depends(get_current_user)):
    deposit_id = str(uuid.uuid4())
    deposit_doc = {
        "id": deposit_id,
        "user_id": current_user["id"],
        "amount": deposit.amount,
        "description": deposit.description,
        "status": "completed",
        "created_at": datetime.utcnow()
    }
    
    db.deposits.insert_one(deposit_doc)
    return Deposit(**deposit_doc)

@app.get("/api/deposits")
async def get_user_deposits(current_user = Depends(get_current_user)):
    deposits = list(db.deposits.find({"user_id": current_user["id"]}).sort("created_at", -1))
    return [Deposit(**deposit) for deposit in deposits]

@app.post("/api/finance-applications")
async def create_finance_application(application: FinanceApplicationCreate, current_user = Depends(get_current_user)):
    app_id = str(uuid.uuid4())
    app_doc = {
        "id": app_id,
        "user_id": current_user["id"],
        "amount": application.amount,
        "purpose": application.purpose,
        "requested_duration_months": application.requested_duration_months,
        "description": application.description,
        "status": ApplicationStatus.PENDING.value,
        "priority_score": None,
        "created_at": datetime.utcnow(),
        "reviewed_at": None,
        "reviewed_by": None,
        "review_notes": None
    }
    
    db.finance_applications.insert_one(app_doc)
    return FinanceApplication(**app_doc)

@app.get("/api/finance-applications")
async def get_user_applications(current_user = Depends(get_current_user)):
    applications = list(db.finance_applications.find({"user_id": current_user["id"]}).sort("created_at", -1))
    return [FinanceApplication(**app) for app in applications]

@app.get("/api/repayments")
async def get_user_repayments(current_user = Depends(get_current_user)):
    repayments = list(db.repayments.find({"user_id": current_user["id"]}).sort("due_date", 1))
    return [Repayment(**repayment) for repayment in repayments]

@app.get("/api/dashboard")
async def get_user_dashboard(current_user = Depends(get_current_user)):
    user_role = UserRole(current_user["role"])
    
    if user_role == UserRole.MEMBER:
        return await get_member_dashboard(current_user)
    elif user_role == UserRole.COUNTRY_COORDINATOR:
        return await get_country_coordinator_dashboard(current_user)
    elif user_role == UserRole.FUND_ADMIN:
        return await get_fund_admin_dashboard(current_user)
    elif user_role == UserRole.GENERAL_ADMIN:
        return await get_general_admin_dashboard(current_user)

async def get_member_dashboard(current_user):
    # Calculate dashboard metrics
    total_deposits = db.deposits.aggregate([
        {"$match": {"user_id": current_user["id"]}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    total_deposits = list(total_deposits)
    total_deposits = total_deposits[0]["total"] if total_deposits else 0
    
    # Total applications
    total_applications = db.finance_applications.count_documents({"user_id": current_user["id"]})
    
    # Pending repayments
    pending_repayments = db.repayments.aggregate([
        {"$match": {"user_id": current_user["id"], "status": "pending"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    pending_repayments = list(pending_repayments)
    pending_repayments = pending_repayments[0]["total"] if pending_repayments else 0
    
    # Recent activity
    recent_deposits = list(db.deposits.find({"user_id": current_user["id"]}).sort("created_at", -1).limit(3))
    recent_applications = list(db.finance_applications.find({"user_id": current_user["id"]}).sort("created_at", -1).limit(3))
    
    return {
        "role": "member",
        "total_deposits": total_deposits,
        "total_applications": total_applications,
        "pending_repayments": pending_repayments,
        "recent_deposits": [Deposit(**dep) for dep in recent_deposits],
        "recent_applications": [FinanceApplication(**app) for app in recent_applications]
    }

async def get_country_coordinator_dashboard(current_user):
    country = current_user["country"]
    
    # Country statistics
    country_members = db.users.count_documents({"country": country, "role": "member"})
    pending_applications = db.finance_applications.count_documents({
        "status": "pending",
        "user_id": {"$in": [user["id"] for user in db.users.find({"country": country})]}
    })
    
    total_deposits_in_country = db.deposits.aggregate([
        {"$lookup": {"from": "users", "localField": "user_id", "foreignField": "id", "as": "user"}},
        {"$match": {"user.country": country}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    total_deposits_in_country = list(total_deposits_in_country)
    total_deposits_in_country = total_deposits_in_country[0]["total"] if total_deposits_in_country else 0
    
    # Recent applications for review
    recent_applications = list(db.finance_applications.aggregate([
        {"$lookup": {"from": "users", "localField": "user_id", "foreignField": "id", "as": "user"}},
        {"$match": {"user.country": country, "status": {"$in": ["pending", "under_review"]}}},
        {"$sort": {"created_at": -1}},
        {"$limit": 5}
    ]))
    
    return {
        "role": "country_coordinator",
        "country": country,
        "country_members": country_members,
        "pending_applications": pending_applications,
        "total_deposits_in_country": total_deposits_in_country,
        "recent_applications": recent_applications
    }

async def get_fund_admin_dashboard(current_user):
    # System-wide statistics
    total_members = db.users.count_documents({"role": "member"})
    total_applications = db.finance_applications.count_documents({})
    approved_applications = db.finance_applications.count_documents({"status": "approved"})
    total_fund_value = db.deposits.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    total_fund_value = list(total_fund_value)
    total_fund_value = total_fund_value[0]["total"] if total_fund_value else 0
    
    # High-value applications needing approval
    high_value_applications = list(db.finance_applications.find({
        "status": {"$in": ["pending", "under_review"]},
        "amount": {"$gte": 1000}
    }).sort("amount", -1).limit(10))
    
    # Disbursement statistics
    disbursed_amount = db.finance_applications.aggregate([
        {"$match": {"status": "disbursed"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    disbursed_amount = list(disbursed_amount)
    disbursed_amount = disbursed_amount[0]["total"] if disbursed_amount else 0
    
    return {
        "role": "fund_admin",
        "total_members": total_members,
        "total_applications": total_applications,
        "approved_applications": approved_applications,
        "total_fund_value": total_fund_value,
        "disbursed_amount": disbursed_amount,
        "high_value_applications": [FinanceApplication(**app) for app in high_value_applications]
    }

async def get_general_admin_dashboard(current_user):
    # Complete system overview
    total_users = db.users.count_documents({})
    role_distribution = list(db.users.aggregate([
        {"$group": {"_id": "$role", "count": {"$sum": 1}}}
    ]))
    
    country_distribution = list(db.users.aggregate([
        {"$group": {"_id": "$country", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]))
    
    # Financial overview
    total_deposits = db.deposits.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    total_deposits = list(total_deposits)
    total_deposits = total_deposits[0]["total"] if total_deposits else 0
    
    # Application status overview
    application_stats = list(db.finance_applications.aggregate([
        {"$group": {"_id": "$status", "count": {"$sum": 1}, "total_amount": {"$sum": "$amount"}}}
    ]))
    
    # Recent system activity
    recent_users = list(db.users.find({}, {"password_hash": 0}).sort("created_at", -1).limit(5))
    recent_applications = list(db.finance_applications.find({}).sort("created_at", -1).limit(5))
    
    return {
        "role": "general_admin",
        "total_users": total_users,
        "role_distribution": role_distribution,
        "country_distribution": country_distribution,
        "total_deposits": total_deposits,
        "application_stats": application_stats,
        "recent_users": [User(**{k: v for k, v in user.items() if k != "password_hash"}) for user in recent_users],
        "recent_applications": [FinanceApplication(**app) for app in recent_applications]
    }

# Admin endpoints
@app.get("/api/admin/users")
async def get_all_users(current_user = Depends(require_role([UserRole.GENERAL_ADMIN, UserRole.FUND_ADMIN]))):
    users = list(db.users.find({}, {"password_hash": 0}).sort("created_at", -1))
    return [User(**user) for user in users]

@app.put("/api/admin/users/role")
async def update_user_role(role_update: UserRoleUpdate, current_user = Depends(require_role([UserRole.GENERAL_ADMIN]))):
    # Check if target user exists
    target_user = db.users.find_one({"id": role_update.user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user role
    db.users.update_one(
        {"id": role_update.user_id},
        {"$set": {"role": role_update.new_role.value}}
    )
    
    # Return updated user
    updated_user = db.users.find_one({"id": role_update.user_id}, {"password_hash": 0})
    return User(**updated_user)

@app.get("/api/admin/applications")
async def get_all_applications(current_user = Depends(require_role([UserRole.COUNTRY_COORDINATOR, UserRole.FUND_ADMIN, UserRole.GENERAL_ADMIN]))):
    user_role = UserRole(current_user["role"])
    
    if user_role == UserRole.COUNTRY_COORDINATOR:
        # Only applications from same country
        country_users = [user["id"] for user in db.users.find({"country": current_user["country"]})]
        applications = list(db.finance_applications.find({"user_id": {"$in": country_users}}).sort("created_at", -1))
    else:
        # Fund admins and general admins see all applications
        applications = list(db.finance_applications.find({}).sort("created_at", -1))
    
    return [FinanceApplication(**app) for app in applications]

@app.put("/api/admin/applications/{application_id}/status")
async def update_application_status(
    application_id: str, 
    status_update: ApplicationStatusUpdate,
    current_user = Depends(require_role([UserRole.COUNTRY_COORDINATOR, UserRole.FUND_ADMIN, UserRole.GENERAL_ADMIN]))
):
    # Check if application exists
    application = db.finance_applications.find_one({"id": application_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Update application
    update_data = {
        "status": status_update.status.value,
        "reviewed_at": datetime.utcnow(),
        "reviewed_by": current_user["id"]
    }
    
    if status_update.review_notes:
        update_data["review_notes"] = status_update.review_notes
    
    db.finance_applications.update_one(
        {"id": application_id},
        {"$set": update_data}
    )
    
    # Return updated application
    updated_application = db.finance_applications.find_one({"id": application_id})
    return FinanceApplication(**updated_application)

@app.get("/api/admin/deposits")
async def get_all_deposits(current_user = Depends(require_role([UserRole.FUND_ADMIN, UserRole.GENERAL_ADMIN]))):
    deposits = list(db.deposits.find({}).sort("created_at", -1))
    return [Deposit(**deposit) for deposit in deposits]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)