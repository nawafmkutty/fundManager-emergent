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

class Repayment(BaseModel):
    id: str
    user_id: str
    application_id: str
    amount: float
    due_date: datetime
    paid_date: Optional[datetime]
    status: RepaymentStatus
    installment_number: int

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
        "reviewed_by": None
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
        "total_deposits": total_deposits,
        "total_applications": total_applications,
        "pending_repayments": pending_repayments,
        "recent_deposits": [Deposit(**dep) for dep in recent_deposits],
        "recent_applications": [FinanceApplication(**app) for app in recent_applications]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)