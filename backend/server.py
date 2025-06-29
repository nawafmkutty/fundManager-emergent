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

# Business Rules Configuration
MINIMUM_DEPOSIT_FOR_GUARANTOR = 500.0  # Minimum deposit amount to be eligible as guarantor
PRIORITY_WEIGHT = 100  # Base priority score, higher = more priority

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

class GuarantorStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"

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

class GuarantorRequest(BaseModel):
    guarantor_user_id: str
    
class FinanceApplicationCreate(BaseModel):
    amount: float = Field(gt=0)
    purpose: str
    requested_duration_months: int = Field(gt=0)
    description: Optional[str] = None
    guarantors: List[str] = Field(default=[])  # List of guarantor user IDs

class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    review_notes: Optional[str] = None

class UserRoleUpdate(BaseModel):
    user_id: str
    new_role: UserRole

class GuarantorResponse(BaseModel):
    id: str
    application_id: str
    guarantor_user_id: str
    guarantor_name: str
    guarantor_email: str
    status: GuarantorStatus
    guaranteed_amount: float
    created_at: datetime
    responded_at: Optional[datetime]

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
    priority_score: Optional[float] = Field(default=0)
    previous_finances_count: Optional[int] = Field(default=0)
    created_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    review_notes: Optional[str] = Field(default=None)
    guarantors: List[GuarantorResponse] = Field(default=[])

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

def calculate_priority_score(user_id: str) -> tuple[float, int]:
    """
    Calculate priority score based on previous finances.
    New applicants have highest priority, lower number of previous finances = higher priority.
    Returns (priority_score, previous_finances_count)
    """
    # Count previous finance applications for this user
    previous_finances_count = db.finance_applications.count_documents({"user_id": user_id})
    
    # Calculate priority score: higher score = higher priority
    # New applicants (0 previous) get max priority
    if previous_finances_count == 0:
        priority_score = PRIORITY_WEIGHT
    else:
        # Decreasing priority with more previous finances
        priority_score = max(1, PRIORITY_WEIGHT - (previous_finances_count * 10))
    
    return priority_score, previous_finances_count

def check_guarantor_eligibility(user_id: str) -> tuple[bool, float]:
    """
    Check if user is eligible to be a guarantor.
    Returns (is_eligible, total_deposits)
    """
    # Calculate total deposits for the user
    total_deposits_result = db.deposits.aggregate([
        {"$match": {"user_id": user_id, "status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    total_deposits_list = list(total_deposits_result)
    total_deposits = total_deposits_list[0]["total"] if total_deposits_list else 0
    
    is_eligible = total_deposits >= MINIMUM_DEPOSIT_FOR_GUARANTOR
    return is_eligible, total_deposits

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

def migrate_existing_applications():
    """Migrate existing applications to include priority and guarantor fields"""
    print("🔄 Migrating existing finance applications...")
    
    # Update applications missing priority_score
    applications_without_priority = db.finance_applications.find({
        "$or": [
            {"priority_score": {"$exists": False}},
            {"previous_finances_count": {"$exists": False}},
            {"review_notes": {"$exists": False}}
        ]
    })
    
    for app in applications_without_priority:
        # Calculate priority for existing applications
        priority_score, previous_finances_count = calculate_priority_score(app["user_id"])
        
        update_data = {}
        if "priority_score" not in app or app.get("priority_score") is None:
            update_data["priority_score"] = priority_score
        if "previous_finances_count" not in app:
            update_data["previous_finances_count"] = previous_finances_count
        if "review_notes" not in app:
            update_data["review_notes"] = None
        
        if update_data:
            db.finance_applications.update_one(
                {"id": app["id"]},
                {"$set": update_data}
            )
    
    print("✅ Migration completed for finance applications")

# Create admin user on startup
create_admin_user()
migrate_existing_applications()

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

@app.get("/api/guarantors/eligible")
async def get_eligible_guarantors(current_user = Depends(get_current_user)):
    """Get list of users eligible to be guarantors"""
    # Get all members with sufficient deposits
    eligible_guarantors = []
    all_members = list(db.users.find({"role": "member", "is_active": True}, {"password_hash": 0}))
    
    for member in all_members:
        if member["id"] == current_user["id"]:  # Can't guarantee for yourself
            continue
            
        is_eligible, total_deposits = check_guarantor_eligibility(member["id"])
        if is_eligible:
            eligible_guarantors.append({
                "id": member["id"],
                "full_name": member["full_name"],
                "email": member["email"],
                "country": member["country"],
                "total_deposits": total_deposits
            })
    
    return eligible_guarantors

@app.post("/api/finance-applications")
async def create_finance_application(application: FinanceApplicationCreate, current_user = Depends(get_current_user)):
    app_id = str(uuid.uuid4())
    
    # Calculate priority score
    priority_score, previous_finances_count = calculate_priority_score(current_user["id"])
    
    # Validate guarantors
    guarantor_records = []
    for guarantor_user_id in application.guarantors:
        # Check if guarantor exists and is eligible
        guarantor = db.users.find_one({"id": guarantor_user_id, "is_active": True})
        if not guarantor:
            raise HTTPException(status_code=400, detail=f"Guarantor user not found: {guarantor_user_id}")
        
        is_eligible, total_deposits = check_guarantor_eligibility(guarantor_user_id)
        if not is_eligible:
            raise HTTPException(
                status_code=400, 
                detail=f"User {guarantor['full_name']} is not eligible to be a guarantor. Minimum deposit required: ${MINIMUM_DEPOSIT_FOR_GUARANTOR}"
            )
        
        # Create guarantor record
        guarantor_id = str(uuid.uuid4())
        guarantor_doc = {
            "id": guarantor_id,
            "application_id": app_id,
            "guarantor_user_id": guarantor_user_id,
            "guarantor_name": guarantor["full_name"],
            "guarantor_email": guarantor["email"],
            "status": GuarantorStatus.PENDING.value,
            "guaranteed_amount": application.amount / len(application.guarantors),  # Split amount among guarantors
            "created_at": datetime.utcnow(),
            "responded_at": None
        }
        
        db.guarantors.insert_one(guarantor_doc)
        guarantor_records.append(GuarantorResponse(**guarantor_doc))
    
    app_doc = {
        "id": app_id,
        "user_id": current_user["id"],
        "amount": application.amount,
        "purpose": application.purpose,
        "requested_duration_months": application.requested_duration_months,
        "description": application.description,
        "status": ApplicationStatus.PENDING.value,
        "priority_score": priority_score,
        "previous_finances_count": previous_finances_count,
        "created_at": datetime.utcnow(),
        "reviewed_at": None,
        "reviewed_by": None,
        "review_notes": None
    }
    
    db.finance_applications.insert_one(app_doc)
    
    # Return application with guarantors
    app_response = FinanceApplication(**app_doc)
    app_response.guarantors = guarantor_records
    
    return app_response

@app.get("/api/finance-applications")
async def get_user_applications(current_user = Depends(get_current_user)):
    applications = list(db.finance_applications.find({"user_id": current_user["id"]}).sort("created_at", -1))
    
    # Add guarantors to each application
    for app in applications:
        guarantors = list(db.guarantors.find({"application_id": app["id"]}))
        app["guarantors"] = [GuarantorResponse(**g) for g in guarantors]
    
    return [FinanceApplication(**app) for app in applications]

@app.get("/api/guarantor-requests")
async def get_guarantor_requests(current_user = Depends(get_current_user)):
    """Get guarantor requests for current user"""
    guarantor_requests = list(db.guarantors.find({"guarantor_user_id": current_user["id"]}).sort("created_at", -1))
    
    # Add application details to each request
    for request in guarantor_requests:
        application = db.finance_applications.find_one({"id": request["application_id"]})
        if application:
            applicant = db.users.find_one({"id": application["user_id"]}, {"password_hash": 0})
            request["application_details"] = {
                "id": application["id"],
                "amount": application["amount"],
                "purpose": application["purpose"],
                "requested_duration_months": application["requested_duration_months"],
                "description": application["description"],
                "applicant_name": applicant["full_name"] if applicant else "Unknown",
                "applicant_email": applicant["email"] if applicant else "Unknown"
            }
    
    return guarantor_requests

@app.put("/api/guarantor-requests/{guarantor_id}/respond")
async def respond_to_guarantor_request(
    guarantor_id: str, 
    response: dict,
    current_user = Depends(get_current_user)
):
    """Respond to a guarantor request (accept/decline)"""
    # Validate response
    if "status" not in response or response["status"] not in ["accepted", "declined"]:
        raise HTTPException(status_code=400, detail="Invalid response. Must be 'accepted' or 'declined'")
    
    # Find guarantor request
    guarantor_request = db.guarantors.find_one({
        "id": guarantor_id,
        "guarantor_user_id": current_user["id"]
    })
    
    if not guarantor_request:
        raise HTTPException(status_code=404, detail="Guarantor request not found")
    
    if guarantor_request["status"] != "pending":
        raise HTTPException(status_code=400, detail="Guarantor request already responded to")
    
    # Update guarantor status
    db.guarantors.update_one(
        {"id": guarantor_id},
        {
            "$set": {
                "status": response["status"],
                "responded_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": f"Guarantor request {response['status']} successfully"}

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
    
    # Check guarantor eligibility
    is_eligible_guarantor, _ = check_guarantor_eligibility(current_user["id"])
    
    # Total applications
    total_applications = db.finance_applications.count_documents({"user_id": current_user["id"]})
    
    # Pending guarantor requests
    pending_guarantor_requests = db.guarantors.count_documents({
        "guarantor_user_id": current_user["id"],
        "status": "pending"
    })
    
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
        "is_eligible_guarantor": is_eligible_guarantor,
        "minimum_deposit_for_guarantor": MINIMUM_DEPOSIT_FOR_GUARANTOR,
        "pending_guarantor_requests": pending_guarantor_requests,
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
    
    # Recent applications for review (sorted by priority)
    recent_applications = list(db.finance_applications.aggregate([
        {"$lookup": {"from": "users", "localField": "user_id", "foreignField": "id", "as": "user"}},
        {"$match": {"user.country": country, "status": {"$in": ["pending", "under_review"]}}},
        {"$addFields": {
            "priority_score": {"$ifNull": ["$priority_score", 0]},
            "previous_finances_count": {"$ifNull": ["$previous_finances_count", 0]},
            "review_notes": {"$ifNull": ["$review_notes", None]}
        }},
        {"$sort": {"priority_score": -1, "created_at": 1}},  # Higher priority first, then older first
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
    
    # High-priority applications needing approval (sorted by priority score)
    high_priority_applications = list(db.finance_applications.find({
        "status": {"$in": ["pending", "under_review"]}
    }).sort([("priority_score", -1), ("created_at", 1)]).limit(10))
    
    # Add guarantor info to applications and ensure all fields exist
    for app in high_priority_applications:
        # Ensure all required fields exist
        if "priority_score" not in app or app["priority_score"] is None:
            app["priority_score"] = 0
        if "previous_finances_count" not in app:
            app["previous_finances_count"] = 0
        if "review_notes" not in app:
            app["review_notes"] = None
            
        guarantors = list(db.guarantors.find({"application_id": app["id"]}))
        app["guarantors"] = [GuarantorResponse(**g) for g in guarantors]
    
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
        "high_priority_applications": [FinanceApplication(**app) for app in high_priority_applications]
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
    
    # Priority system statistics
    priority_stats = list(db.finance_applications.aggregate([
        {"$group": {
            "_id": None,
            "avg_priority": {"$avg": "$priority_score"},
            "max_priority": {"$max": "$priority_score"},
            "min_priority": {"$min": "$priority_score"}
        }}
    ]))
    
    # Guarantor statistics
    guarantor_stats = list(db.guarantors.aggregate([
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]))
    
    # Recent system activity
    recent_users = list(db.users.find({}, {"password_hash": 0}).sort("created_at", -1).limit(5))
    recent_applications = list(db.finance_applications.find({}).sort([("priority_score", -1), ("created_at", -1)]).limit(5))
    
    # Ensure all fields exist in recent applications
    for app in recent_applications:
        if "priority_score" not in app or app["priority_score"] is None:
            app["priority_score"] = 0
        if "previous_finances_count" not in app:
            app["previous_finances_count"] = 0
        if "review_notes" not in app:
            app["review_notes"] = None
    
    return {
        "role": "general_admin",
        "total_users": total_users,
        "role_distribution": role_distribution,
        "country_distribution": country_distribution,
        "total_deposits": total_deposits,
        "application_stats": application_stats,
        "priority_stats": priority_stats[0] if priority_stats else {"avg_priority": 0, "max_priority": 0, "min_priority": 0},
        "guarantor_stats": guarantor_stats,
        "recent_users": [User(**{k: v for k, v in user.items() if k != "password_hash"}) for user in recent_users],
        "recent_applications": [FinanceApplication(**app) for app in recent_applications]
    }

# Admin endpoints
@app.get("/api/admin/users")
async def get_all_users(current_user = Depends(require_role([UserRole.GENERAL_ADMIN, UserRole.FUND_ADMIN]))):
    users = list(db.users.find({}, {"password_hash": 0}).sort("created_at", -1))
    
    # Add guarantor eligibility to each user
    for user in users:
        is_eligible, total_deposits = check_guarantor_eligibility(user["id"])
        user["is_eligible_guarantor"] = is_eligible
        user["total_deposits"] = total_deposits
    
    return [User(**{**user, "is_eligible_guarantor": user["is_eligible_guarantor"], "total_deposits": user["total_deposits"]}) for user in users]

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
        # Only applications from same country, sorted by priority
        country_users = [user["id"] for user in db.users.find({"country": current_user["country"]})]
        applications = list(db.finance_applications.find({"user_id": {"$in": country_users}}).sort([("priority_score", -1), ("created_at", 1)]))
    else:
        # Fund admins and general admins see all applications, sorted by priority
        applications = list(db.finance_applications.find({}).sort([("priority_score", -1), ("created_at", 1)]))
    
    # Add guarantors to each application
    for app in applications:
        guarantors = list(db.guarantors.find({"application_id": app["id"]}))
        app["guarantors"] = [GuarantorResponse(**g) for g in guarantors]
        
        # Add applicant info
        applicant = db.users.find_one({"id": app["user_id"]}, {"password_hash": 0})
        if applicant:
            app["applicant_name"] = applicant["full_name"]
            app["applicant_email"] = applicant["email"]
            app["applicant_country"] = applicant["country"]
    
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
    
    # Add guarantors
    guarantors = list(db.guarantors.find({"application_id": application_id}))
    updated_application["guarantors"] = [GuarantorResponse(**g) for g in guarantors]
    
    return FinanceApplication(**updated_application)

@app.get("/api/admin/deposits")
async def get_all_deposits(current_user = Depends(require_role([UserRole.FUND_ADMIN, UserRole.GENERAL_ADMIN]))):
    deposits = list(db.deposits.find({}).sort("created_at", -1))
    
    # Add user info to deposits
    for deposit in deposits:
        user = db.users.find_one({"id": deposit["user_id"]}, {"password_hash": 0})
        if user:
            deposit["user_name"] = user["full_name"]
            deposit["user_email"] = user["email"]
    
    return [Deposit(**deposit) for deposit in deposits]

@app.get("/api/admin/guarantors")
async def get_all_guarantors(current_user = Depends(require_role([UserRole.FUND_ADMIN, UserRole.GENERAL_ADMIN]))):
    """Get all guarantor relationships"""
    guarantors = list(db.guarantors.find({}).sort("created_at", -1))
    
    # Add application details
    for guarantor in guarantors:
        application = db.finance_applications.find_one({"id": guarantor["application_id"]})
        if application:
            guarantor["application_amount"] = application["amount"]
            guarantor["application_purpose"] = application["purpose"]
    
    return [GuarantorResponse(**guarantor) for guarantor in guarantors]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)