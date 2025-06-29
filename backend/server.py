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

# Default Business Rules Configuration
DEFAULT_MINIMUM_DEPOSIT_FOR_GUARANTOR = 500.0
PRIORITY_WEIGHT = 100

# Approval Limits by Role
APPROVAL_LIMITS = {
    "country_coordinator": 1000.0,  # Can approve up to $1000
    "fund_admin": 10000.0,          # Can approve up to $10000
    "general_admin": float('inf')    # Can approve any amount
}

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
    REQUIRES_HIGHER_APPROVAL = "requires_higher_approval"

class ApprovalAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_MORE_INFO = "request_more_info"
    ESCALATE = "escalate"

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
    guarantors: List[str] = Field(default=[])

class ApplicationApprovalRequest(BaseModel):
    action: ApprovalAction
    review_notes: Optional[str] = None
    conditions: Optional[str] = None  # Any conditions for approval
    recommended_amount: Optional[float] = None  # If different from requested

class UserRoleUpdate(BaseModel):
    user_id: str
    new_role: UserRole

class SystemConfigUpdate(BaseModel):
    minimum_deposit_for_guarantor: Optional[float] = Field(None, gt=0)
    priority_weight: Optional[float] = Field(None, gt=0)
    max_loan_amount: Optional[float] = Field(None, gt=0)
    max_loan_duration_months: Optional[int] = Field(None, gt=0)
    country_coordinator_limit: Optional[float] = Field(None, gt=0)
    fund_admin_limit: Optional[float] = Field(None, gt=0)

class SystemConfig(BaseModel):
    id: str = Field(default="system_config")
    minimum_deposit_for_guarantor: float = Field(default=DEFAULT_MINIMUM_DEPOSIT_FOR_GUARANTOR)
    priority_weight: float = Field(default=PRIORITY_WEIGHT)
    max_loan_amount: Optional[float] = Field(default=None)
    max_loan_duration_months: Optional[int] = Field(default=None)
    country_coordinator_limit: float = Field(default=1000.0)
    fund_admin_limit: float = Field(default=10000.0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = Field(default=None)

class ApprovalHistory(BaseModel):
    id: str
    application_id: str
    approver_id: str
    approver_name: str
    approver_role: str
    action: ApprovalAction
    review_notes: Optional[str]
    conditions: Optional[str]
    recommended_amount: Optional[float]
    previous_status: ApplicationStatus
    new_status: ApplicationStatus
    created_at: datetime

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
    conditions: Optional[str] = Field(default=None)
    approved_amount: Optional[float] = Field(default=None)
    requires_higher_approval: bool = Field(default=False)
    guarantors: List[GuarantorResponse] = Field(default=[])
    approval_history: List[ApprovalHistory] = Field(default=[])

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
    UserRole.COUNTRY_COORDINATOR: ["view_own_data", "create_deposits", "create_applications", "view_country_data", "review_applications", "approve_small_loans"],
    UserRole.FUND_ADMIN: ["view_own_data", "create_deposits", "create_applications", "view_all_data", "review_applications", "approve_large_loans", "manage_disbursals"],
    UserRole.GENERAL_ADMIN: ["all_permissions", "manage_users", "assign_roles", "system_config", "approve_any_loan"]
}

# Utility functions
def get_system_config():
    """Get current system configuration"""
    config = db.system_config.find_one({"id": "system_config"})
    if not config:
        # Create default configuration
        default_config = {
            "id": "system_config",
            "minimum_deposit_for_guarantor": DEFAULT_MINIMUM_DEPOSIT_FOR_GUARANTOR,
            "priority_weight": PRIORITY_WEIGHT,
            "max_loan_amount": None,
            "max_loan_duration_months": None,
            "country_coordinator_limit": 1000.0,
            "fund_admin_limit": 10000.0,
            "updated_at": datetime.utcnow(),
            "updated_by": None
        }
        db.system_config.insert_one(default_config)
        config = default_config
    
    return SystemConfig(**config)

def get_approval_limit(user_role: str) -> float:
    """Get approval limit for a specific role"""
    config = get_system_config()
    
    if user_role == "country_coordinator":
        return config.country_coordinator_limit
    elif user_role == "fund_admin":
        return config.fund_admin_limit
    elif user_role == "general_admin":
        return float('inf')
    else:
        return 0.0

def determine_required_approval_level(amount: float, user_country: str = None) -> str:
    """Determine what level of approval is required for an amount"""
    config = get_system_config()
    
    if amount <= config.country_coordinator_limit:
        return "country_coordinator"
    elif amount <= config.fund_admin_limit:
        return "fund_admin"
    else:
        return "general_admin"

def can_approve_application(approver_role: str, amount: float, applicant_country: str, approver_country: str) -> tuple[bool, str]:
    """Check if user can approve an application"""
    approval_limit = get_approval_limit(approver_role)
    
    # Check amount limit
    if amount > approval_limit:
        return False, f"Amount exceeds approval limit of ${approval_limit:,.2f}"
    
    # Country coordinators can only approve applications from their country
    if approver_role == "country_coordinator" and applicant_country != approver_country:
        return False, "Country coordinators can only approve applications from their country"
    
    return True, "Approved"

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
    """Calculate priority score based on previous finances"""
    previous_finances_count = db.finance_applications.count_documents({"user_id": user_id})
    config = get_system_config()
    priority_weight = config.priority_weight
    
    if previous_finances_count == 0:
        priority_score = priority_weight
    else:
        priority_score = max(1, priority_weight - (previous_finances_count * 10))
    
    return priority_score, previous_finances_count

def check_guarantor_eligibility(user_id: str) -> tuple[bool, float]:
    """Check if user is eligible to be a guarantor"""
    config = get_system_config()
    minimum_deposit_for_guarantor = config.minimum_deposit_for_guarantor
    
    total_deposits_result = db.deposits.aggregate([
        {"$match": {"user_id": user_id, "status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    total_deposits_list = list(total_deposits_result)
    total_deposits = total_deposits_list[0]["total"] if total_deposits_list else 0
    
    is_eligible = total_deposits >= minimum_deposit_for_guarantor
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
    """Migrate existing applications to include new approval workflow fields"""
    print("🔄 Migrating existing finance applications...")
    
    applications = db.finance_applications.find({
        "$or": [
            {"priority_score": {"$exists": False}},
            {"previous_finances_count": {"$exists": False}},
            {"review_notes": {"$exists": False}},
            {"requires_higher_approval": {"$exists": False}},
            {"approved_amount": {"$exists": False}},
            {"conditions": {"$exists": False}}
        ]
    })
    
    for app in applications:
        priority_score, previous_finances_count = calculate_priority_score(app["user_id"])
        
        update_data = {}
        if "priority_score" not in app or app.get("priority_score") is None:
            update_data["priority_score"] = priority_score
        if "previous_finances_count" not in app:
            update_data["previous_finances_count"] = previous_finances_count
        if "review_notes" not in app:
            update_data["review_notes"] = None
        if "requires_higher_approval" not in app:
            update_data["requires_higher_approval"] = False
        if "approved_amount" not in app:
            update_data["approved_amount"] = None
        if "conditions" not in app:
            update_data["conditions"] = None
        
        if update_data:
            db.finance_applications.update_one(
                {"id": app["id"]},
                {"$set": update_data}
            )
    
    print("✅ Migration completed for finance applications")

# Create admin user and system config on startup
create_admin_user()
migrate_existing_applications()

# Initialize system configuration
get_system_config()

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

# System Configuration endpoints
@app.get("/api/admin/system-config")
async def get_system_configuration(current_user = Depends(require_role([UserRole.GENERAL_ADMIN]))):
    """Get current system configuration"""
    config = get_system_config()
    return config

@app.put("/api/admin/system-config")
async def update_system_configuration(
    config_update: SystemConfigUpdate, 
    current_user = Depends(require_role([UserRole.GENERAL_ADMIN]))
):
    """Update system configuration"""
    current_config = get_system_config()
    
    # Prepare update data
    update_data = {
        "updated_at": datetime.utcnow(),
        "updated_by": current_user["id"]
    }
    
    # Update only provided fields
    if config_update.minimum_deposit_for_guarantor is not None:
        update_data["minimum_deposit_for_guarantor"] = config_update.minimum_deposit_for_guarantor
        
    if config_update.priority_weight is not None:
        update_data["priority_weight"] = config_update.priority_weight
        
    if config_update.max_loan_amount is not None:
        update_data["max_loan_amount"] = config_update.max_loan_amount
        
    if config_update.max_loan_duration_months is not None:
        update_data["max_loan_duration_months"] = config_update.max_loan_duration_months
    
    if config_update.country_coordinator_limit is not None:
        update_data["country_coordinator_limit"] = config_update.country_coordinator_limit
        
    if config_update.fund_admin_limit is not None:
        update_data["fund_admin_limit"] = config_update.fund_admin_limit
    
    # Update configuration
    db.system_config.update_one(
        {"id": "system_config"},
        {"$set": update_data},
        upsert=True
    )
    
    # Return updated configuration
    updated_config = get_system_config()
    return updated_config

# Member endpoints
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
    
    # Get current system configuration
    config = get_system_config()
    
    # Validate loan amount and duration against system limits
    if config.max_loan_amount and application.amount > config.max_loan_amount:
        raise HTTPException(
            status_code=400, 
            detail=f"Requested amount exceeds maximum loan amount of {config.max_loan_amount}"
        )
    
    if config.max_loan_duration_months and application.requested_duration_months > config.max_loan_duration_months:
        raise HTTPException(
            status_code=400, 
            detail=f"Requested duration exceeds maximum loan duration of {config.max_loan_duration_months} months"
        )
    
    # Calculate priority score
    priority_score, previous_finances_count = calculate_priority_score(current_user["id"])
    
    # Determine if higher approval is required
    required_approval_level = determine_required_approval_level(application.amount, current_user["country"])
    requires_higher_approval = required_approval_level in ["fund_admin", "general_admin"]
    
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
                detail=f"User {guarantor['full_name']} is not eligible to be a guarantor. Minimum deposit required: ${config.minimum_deposit_for_guarantor}"
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
            "guaranteed_amount": application.amount / len(application.guarantors),
            "created_at": datetime.utcnow(),
            "responded_at": None
        }
        
        db.guarantors.insert_one(guarantor_doc)
        guarantor_records.append(GuarantorResponse(**guarantor_doc))
    
    # Set initial status based on approval requirements
    initial_status = ApplicationStatus.PENDING.value
    if requires_higher_approval:
        initial_status = ApplicationStatus.REQUIRES_HIGHER_APPROVAL.value
    
    app_doc = {
        "id": app_id,
        "user_id": current_user["id"],
        "amount": application.amount,
        "purpose": application.purpose,
        "requested_duration_months": application.requested_duration_months,
        "description": application.description,
        "status": initial_status,
        "priority_score": priority_score,
        "previous_finances_count": previous_finances_count,
        "created_at": datetime.utcnow(),
        "reviewed_at": None,
        "reviewed_by": None,
        "review_notes": None,
        "conditions": None,
        "approved_amount": None,
        "requires_higher_approval": requires_higher_approval
    }
    
    db.finance_applications.insert_one(app_doc)
    
    # Return application with guarantors
    app_response = FinanceApplication(**app_doc)
    app_response.guarantors = guarantor_records
    
    return app_response

@app.get("/api/finance-applications")
async def get_user_applications(current_user = Depends(get_current_user)):
    applications = list(db.finance_applications.find({"user_id": current_user["id"]}).sort("created_at", -1))
    
    # Add guarantors and approval history to each application
    for app in applications:
        guarantors = list(db.guarantors.find({"application_id": app["id"]}))
        app["guarantors"] = [GuarantorResponse(**g) for g in guarantors]
        
        approval_history = list(db.approval_history.find({"application_id": app["id"]}).sort("created_at", 1))
        app["approval_history"] = [ApprovalHistory(**h) for h in approval_history]
    
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
                "status": application["status"],
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

# Approval Workflow endpoints
@app.put("/api/admin/applications/{application_id}/approve")
async def approve_application(
    application_id: str, 
    approval_request: ApplicationApprovalRequest,
    current_user = Depends(require_role([UserRole.COUNTRY_COORDINATOR, UserRole.FUND_ADMIN, UserRole.GENERAL_ADMIN]))
):
    """Approve or reject a finance application"""
    
    # Find the application
    application = db.finance_applications.find_one({"id": application_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Get applicant details
    applicant = db.users.find_one({"id": application["user_id"]})
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    
    # Check if user can approve this application
    can_approve, reason = can_approve_application(
        current_user["role"], 
        approval_request.recommended_amount or application["amount"], 
        applicant["country"], 
        current_user["country"]
    )
    
    if not can_approve and approval_request.action == ApprovalAction.APPROVE:
        raise HTTPException(status_code=403, detail=reason)
    
    # Determine new status based on action
    previous_status = ApplicationStatus(application["status"])
    
    if approval_request.action == ApprovalAction.APPROVE:
        # Check if this approval is sufficient or needs escalation
        approval_amount = approval_request.recommended_amount or application["amount"]
        required_level = determine_required_approval_level(approval_amount)
        
        if (current_user["role"] == "country_coordinator" and required_level in ["fund_admin", "general_admin"]) or \
           (current_user["role"] == "fund_admin" and required_level == "general_admin"):
            new_status = ApplicationStatus.REQUIRES_HIGHER_APPROVAL
        else:
            new_status = ApplicationStatus.APPROVED
    elif approval_request.action == ApprovalAction.REJECT:
        new_status = ApplicationStatus.REJECTED
    elif approval_request.action == ApprovalAction.REQUEST_MORE_INFO:
        new_status = ApplicationStatus.UNDER_REVIEW
    elif approval_request.action == ApprovalAction.ESCALATE:
        new_status = ApplicationStatus.REQUIRES_HIGHER_APPROVAL
    
    # Create approval history record
    approval_history_id = str(uuid.uuid4())
    approval_history = {
        "id": approval_history_id,
        "application_id": application_id,
        "approver_id": current_user["id"],
        "approver_name": current_user["full_name"],
        "approver_role": current_user["role"],
        "action": approval_request.action.value,
        "review_notes": approval_request.review_notes,
        "conditions": approval_request.conditions,
        "recommended_amount": approval_request.recommended_amount,
        "previous_status": previous_status.value,
        "new_status": new_status.value,
        "created_at": datetime.utcnow()
    }
    
    db.approval_history.insert_one(approval_history)
    
    # Update application
    update_data = {
        "status": new_status.value,
        "reviewed_at": datetime.utcnow(),
        "reviewed_by": current_user["id"],
        "review_notes": approval_request.review_notes
    }
    
    if approval_request.conditions:
        update_data["conditions"] = approval_request.conditions
    
    if approval_request.recommended_amount:
        update_data["approved_amount"] = approval_request.recommended_amount
    
    db.finance_applications.update_one(
        {"id": application_id},
        {"$set": update_data}
    )
    
    # Return updated application with history
    updated_application = db.finance_applications.find_one({"id": application_id})
    
    # Ensure all fields exist
    if "priority_score" not in updated_application or updated_application["priority_score"] is None:
        updated_application["priority_score"] = 0
    if "previous_finances_count" not in updated_application:
        updated_application["previous_finances_count"] = 0
    if "review_notes" not in updated_application:
        updated_application["review_notes"] = None
    if "conditions" not in updated_application:
        updated_application["conditions"] = None
    if "approved_amount" not in updated_application:
        updated_application["approved_amount"] = None
    if "requires_higher_approval" not in updated_application:
        updated_application["requires_higher_approval"] = False
    
    # Add guarantors and approval history
    guarantors = list(db.guarantors.find({"application_id": application_id}))
    updated_application["guarantors"] = [GuarantorResponse(**g) for g in guarantors]
    
    approval_history_records = list(db.approval_history.find({"application_id": application_id}).sort("created_at", 1))
    updated_application["approval_history"] = [ApprovalHistory(**h) for h in approval_history_records]
    
    return FinanceApplication(**updated_application)

@app.get("/api/admin/approval-queue")
async def get_approval_queue(current_user = Depends(require_role([UserRole.COUNTRY_COORDINATOR, UserRole.FUND_ADMIN, UserRole.GENERAL_ADMIN]))):
    """Get applications pending approval for the current user's role"""
    
    user_role = current_user["role"]
    approval_limit = get_approval_limit(user_role)
    
    # Build query based on role
    if user_role == "country_coordinator":
        # Country coordinators see applications from their country that they can approve
        country_users = [user["id"] for user in db.users.find({"country": current_user["country"]})]
        query = {
            "user_id": {"$in": country_users},
            "status": {"$in": ["pending", "under_review"]},
            "amount": {"$lte": approval_limit}
        }
    elif user_role == "fund_admin":
        # Fund admins see applications requiring their level of approval
        query = {
            "status": {"$in": ["pending", "under_review", "requires_higher_approval"]},
            "amount": {"$lte": approval_limit}
        }
    else:  # general_admin
        # General admins see all applications requiring approval
        query = {
            "status": {"$in": ["pending", "under_review", "requires_higher_approval"]}
        }
    
    applications = list(db.finance_applications.find(query).sort([("priority_score", -1), ("created_at", 1)]))
    
    # Add additional information to each application
    for app in applications:
        # Ensure all fields exist
        if "priority_score" not in app or app["priority_score"] is None:
            app["priority_score"] = 0
        if "previous_finances_count" not in app:
            app["previous_finances_count"] = 0
        if "review_notes" not in app:
            app["review_notes"] = None
        if "conditions" not in app:
            app["conditions"] = None
        if "approved_amount" not in app:
            app["approved_amount"] = None
        if "requires_higher_approval" not in app:
            app["requires_higher_approval"] = False
        
        # Add applicant info
        applicant = db.users.find_one({"id": app["user_id"]}, {"password_hash": 0})
        if applicant:
            app["applicant_name"] = applicant["full_name"]
            app["applicant_email"] = applicant["email"]
            app["applicant_country"] = applicant["country"]
        
        # Add guarantors
        guarantors = list(db.guarantors.find({"application_id": app["id"]}))
        app["guarantors"] = [GuarantorResponse(**g) for g in guarantors]
        
        # Add approval history
        approval_history = list(db.approval_history.find({"application_id": app["id"]}).sort("created_at", 1))
        app["approval_history"] = [ApprovalHistory(**h) for h in approval_history]
        
        # Add required approval level
        app["required_approval_level"] = determine_required_approval_level(app["amount"])
        
        # Check if current user can approve
        can_approve, reason = can_approve_application(
            user_role, 
            app["amount"], 
            applicant["country"] if applicant else "", 
            current_user["country"]
        )
        app["can_approve"] = can_approve
        app["approval_restriction"] = reason if not can_approve else None
    
    return [FinanceApplication(**app) for app in applications]

# Dashboard functions (updated with approval workflow data)
async def get_member_dashboard(current_user):
    config = get_system_config()
    
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
    
    # Applications by status
    pending_applications = db.finance_applications.count_documents({
        "user_id": current_user["id"], 
        "status": {"$in": ["pending", "under_review", "requires_higher_approval"]}
    })
    approved_applications = db.finance_applications.count_documents({
        "user_id": current_user["id"], 
        "status": "approved"
    })
    
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
        "pending_applications": pending_applications,
        "approved_applications": approved_applications,
        "pending_repayments": pending_repayments,
        "is_eligible_guarantor": is_eligible_guarantor,
        "minimum_deposit_for_guarantor": config.minimum_deposit_for_guarantor,
        "pending_guarantor_requests": pending_guarantor_requests,
        "recent_deposits": [Deposit(**dep) for dep in recent_deposits],
        "recent_applications": [FinanceApplication(**app) for app in recent_applications]
    }

async def get_country_coordinator_dashboard(current_user):
    country = current_user["country"]
    config = get_system_config()
    
    # Country statistics
    country_members = db.users.count_documents({"country": country, "role": "member"})
    
    # Applications requiring approval at this level
    country_users = [user["id"] for user in db.users.find({"country": country})]
    pending_approval = db.finance_applications.count_documents({
        "user_id": {"$in": country_users},
        "status": {"$in": ["pending", "under_review"]},
        "amount": {"$lte": config.country_coordinator_limit}
    })
    
    # Applications requiring higher approval
    needs_escalation = db.finance_applications.count_documents({
        "user_id": {"$in": country_users},
        "status": "requires_higher_approval"
    })
    
    total_deposits_in_country = db.deposits.aggregate([
        {"$lookup": {"from": "users", "localField": "user_id", "foreignField": "id", "as": "user"}},
        {"$match": {"user.country": country}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    total_deposits_in_country = list(total_deposits_in_country)
    total_deposits_in_country = total_deposits_in_country[0]["total"] if total_deposits_in_country else 0
    
    return {
        "role": "country_coordinator",
        "country": country,
        "country_members": country_members,
        "pending_approval": pending_approval,
        "needs_escalation": needs_escalation,
        "total_deposits_in_country": total_deposits_in_country,
        "approval_limit": config.country_coordinator_limit
    }

async def get_fund_admin_dashboard(current_user):
    config = get_system_config()
    
    # System-wide statistics
    total_members = db.users.count_documents({"role": "member"})
    total_applications = db.finance_applications.count_documents({})
    
    # Applications requiring fund admin approval
    pending_approval = db.finance_applications.count_documents({
        "status": {"$in": ["pending", "under_review", "requires_higher_approval"]},
        "amount": {"$lte": config.fund_admin_limit}
    })
    
    # High-value applications
    high_value_applications = db.finance_applications.count_documents({
        "status": {"$in": ["pending", "under_review", "requires_higher_approval"]},
        "amount": {"$gt": config.country_coordinator_limit}
    })
    
    # Approved applications ready for disbursement
    ready_for_disbursement = db.finance_applications.count_documents({"status": "approved"})
    
    total_fund_value = db.deposits.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    total_fund_value = list(total_fund_value)
    total_fund_value = total_fund_value[0]["total"] if total_fund_value else 0
    
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
        "pending_approval": pending_approval,
        "high_value_applications": high_value_applications,
        "ready_for_disbursement": ready_for_disbursement,
        "total_fund_value": total_fund_value,
        "disbursed_amount": disbursed_amount,
        "approval_limit": config.fund_admin_limit
    }

async def get_general_admin_dashboard(current_user):
    config = get_system_config()
    
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
    
    # Approval workflow statistics
    approval_stats = list(db.approval_history.aggregate([
        {"$group": {"_id": "$action", "count": {"$sum": 1}}}
    ]))
    
    # Applications requiring general admin approval
    pending_high_value = db.finance_applications.count_documents({
        "status": {"$in": ["requires_higher_approval"]},
        "amount": {"$gt": config.fund_admin_limit}
    })
    
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
        if "conditions" not in app:
            app["conditions"] = None
        if "approved_amount" not in app:
            app["approved_amount"] = None
        if "requires_higher_approval" not in app:
            app["requires_higher_approval"] = False
    
    return {
        "role": "general_admin",
        "total_users": total_users,
        "role_distribution": role_distribution,
        "country_distribution": country_distribution,
        "total_deposits": total_deposits,
        "application_stats": application_stats,
        "approval_stats": approval_stats,
        "pending_high_value": pending_high_value,
        "priority_stats": priority_stats[0] if priority_stats else {"avg_priority": 0, "max_priority": 0, "min_priority": 0},
        "guarantor_stats": guarantor_stats,
        "system_config": config,
        "recent_users": [User(**{k: v for k, v in user.items() if k != "password_hash"}) for user in recent_users],
        "recent_applications": [FinanceApplication(**app) for app in recent_applications]
    }

# Admin endpoints (updated for approval workflow)
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
    
    # Add guarantors, approval history, and other information to each application
    for app in applications:
        # Ensure all required fields exist
        if "priority_score" not in app or app["priority_score"] is None:
            app["priority_score"] = 0
        if "previous_finances_count" not in app:
            app["previous_finances_count"] = 0
        if "review_notes" not in app:
            app["review_notes"] = None
        if "conditions" not in app:
            app["conditions"] = None
        if "approved_amount" not in app:
            app["approved_amount"] = None
        if "requires_higher_approval" not in app:
            app["requires_higher_approval"] = False
            
        guarantors = list(db.guarantors.find({"application_id": app["id"]}))
        app["guarantors"] = [GuarantorResponse(**g) for g in guarantors]
        
        # Add approval history
        approval_history = list(db.approval_history.find({"application_id": app["id"]}).sort("created_at", 1))
        app["approval_history"] = [ApprovalHistory(**h) for h in approval_history]
        
        # Add applicant info
        applicant = db.users.find_one({"id": app["user_id"]}, {"password_hash": 0})
        if applicant:
            app["applicant_name"] = applicant["full_name"]
            app["applicant_email"] = applicant["email"]
            app["applicant_country"] = applicant["country"]
        
        # Add required approval level
        app["required_approval_level"] = determine_required_approval_level(app["amount"])
        
        # Check if current user can approve
        can_approve, reason = can_approve_application(
            current_user["role"], 
            app["amount"], 
            applicant["country"] if applicant else "", 
            current_user["country"]
        )
        app["can_approve"] = can_approve
        app["approval_restriction"] = reason if not can_approve else None
    
    return [FinanceApplication(**app) for app in applications]

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

@app.get("/api/admin/approval-history")
async def get_approval_history(current_user = Depends(require_role([UserRole.FUND_ADMIN, UserRole.GENERAL_ADMIN]))):
    """Get approval history for all applications"""
    history = list(db.approval_history.find({}).sort("created_at", -1).limit(100))
    return [ApprovalHistory(**h) for h in history]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)