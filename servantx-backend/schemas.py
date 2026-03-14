from typing import Any, Dict, List, Optional
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = None
    name: Optional[str] = None
    role: str = "user"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    expires_at: Optional[datetime] = None


class ContactRequest(BaseModel):
    orgName: str = Field(..., min_length=2)
    state: str = Field(..., min_length=2)
    contactName: str = Field(..., min_length=2)
    role: str = Field(...)
    email: EmailStr
    phone: Optional[str] = None
    revenue: str = Field(...)
    hospitalType: Optional[List[str]] = None
    interestAreas: List[str] = Field(..., min_length=1)
    payers: Optional[str] = None
    timeframe: str = Field(...)
    approval: str = Field(...)
    nextStep: str = Field(...)
    additionalInfo: Optional[str] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        valid_roles = ["CFO", "VP Finance", "Revenue Integrity Director", "Revenue Cycle Leader", "Compliance", "Other"]
        if v not in valid_roles:
            raise ValueError(f"role must be one of: {', '.join(valid_roles)}")
        return v

    @field_validator("revenue")
    @classmethod
    def validate_revenue(cls, v):
        valid_revenues = ["Under $20M", "$20M–$40M", "$40M–$75M", "$75M+"]
        if v not in valid_revenues:
            raise ValueError(f"revenue must be one of: {', '.join(valid_revenues)}")
        return v

    @field_validator("hospitalType")
    @classmethod
    def validate_hospital_type(cls, v):
        if v is not None:
            valid_types = ["Rural", "Critical Access", "Community Hospital", "Regional Health System"]
            invalid = [t for t in v if t not in valid_types]
            if invalid:
                raise ValueError(f"hospitalType contains invalid values: {', '.join(invalid)}")
        return v

    @field_validator("interestAreas")
    @classmethod
    def validate_interest_areas(cls, v):
        valid_areas = [
            "Outpatient facility claims",
            "Modifier-related underpayments",
            "Contract misapplication",
            "Not sure (seeking assessment)"
        ]
        invalid = [a for a in v if a not in valid_areas]
        if invalid:
            raise ValueError(f"interestAreas contains invalid values: {', '.join(invalid)}")
        return v

    @field_validator("timeframe")
    @classmethod
    def validate_timeframe(cls, v):
        valid_timeframes = ["Last 90 days", "Last 180 days", "Open to recommendation"]
        if v not in valid_timeframes:
            raise ValueError(f"timeframe must be one of: {', '.join(valid_timeframes)}")
        return v

    @field_validator("approval")
    @classmethod
    def validate_approval(cls, v):
        valid_approvals = ["Yes", "Not yet", "In progress"]
        if v not in valid_approvals:
            raise ValueError(f"approval must be one of: {', '.join(valid_approvals)}")
        return v

    @field_validator("nextStep")
    @classmethod
    def validate_next_step(cls, v):
        valid_steps = ["Introductory conversation", "Technical overview", "Written pilot outline"]
        if v not in valid_steps:
            raise ValueError(f"nextStep must be one of: {', '.join(valid_steps)}")
        return v


class GeneralContactRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    subject: str = Field(..., min_length=2)
    message: str = Field(..., min_length=10)


# Contract Schemas
class Contract(BaseModel):
    id: str
    hospitalId: str
    name: str
    fileName: str
    fileSize: Optional[int] = None
    fileUrl: Optional[str] = None
    uploadedAt: datetime
    status: str  # "pending" | "processing" | "processed" | "error"
    rulesExtracted: Optional[int] = None
    notes: Optional[str] = None
    ruleLibrary: Optional[dict] = None  # Exhaustive payment rule library (JSON)

    class Config:
        from_attributes = True


class ContractUploadResponse(BaseModel):
    contract: Contract
    message: Optional[str] = None


class ContractChatMessage(BaseModel):
    role: str  # user | assistant
    content: str


class ContractChatRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=5000)
    includeWeb: bool = False
    history: Optional[List[ContractChatMessage]] = None


class ContractChatSource(BaseModel):
    sourceType: str  # contract | web
    title: str
    url: Optional[str] = None
    snippet: str


class ContractChatResponse(BaseModel):
    contractId: str
    contractName: str
    answer: str
    usedWeb: bool = False
    sources: List[ContractChatSource] = []
    disclaimer: str


# Receipt Schemas
class Receipt(BaseModel):
    id: str
    hospitalId: str
    hasDifference: bool
    amount: float
    uploadedAt: datetime
    documentId: Optional[str] = None
    fileName: str
    fileSize: Optional[int] = None
    fileUrl: Optional[str] = None
    status: Optional[str] = None  # "pending" | "processing" | "processed" | "error"

    class Config:
        from_attributes = True


class ReceiptUploadResponse(BaseModel):
    receipt: Receipt
    document: Optional[dict] = None


class PaginatedReceiptsResponse(BaseModel):
    items: List[Receipt]
    total: int
    limit: int
    offset: int
    hasMore: bool


# Auth Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    hospital_name: str
    phone: str
    password: str
    confirm_password: str

    @field_validator("email", mode="before")
    @classmethod
    def validate_email_before(cls, v):
        """Convert email to string before EmailStr validation"""
        if v is None:
            raise ValueError("Email is required")
        # Convert to string if it's not already
        if not isinstance(v, str):
            v = str(v)
        # Strip whitespace
        v = v.strip() if isinstance(v, str) else v
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not isinstance(v, str):
            raise ValueError(f"Password must be a string, got {type(v).__name__}")
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        # Bcrypt has a 72-byte limit, warn if password is very long
        if len(v.encode('utf-8')) > 72:
            raise ValueError("Password cannot exceed 72 bytes (approximately 72 characters for ASCII)")
        return v

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords don't match")
        return self


class User(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    hospital_id: str
    hospital_name: Optional[str] = None
    role: Optional[str] = "user"
    has_contract: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    user: User
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    message: Optional[str] = None


class UpdateHasContractRequest(BaseModel):
    has_contract: bool


# Document Schemas
class Document(BaseModel):
    id: str
    receiptId: Optional[str] = None
    hospitalId: str
    projectId: Optional[str] = None
    contractId: Optional[str] = None
    batchRunId: Optional[str] = None
    documentRole: Optional[str] = None
    parentDocumentId: Optional[str] = None
    payerKey: Optional[str] = None
    dosStart: Optional[date] = None
    dosEnd: Optional[date] = None
    billingNpi: Optional[str] = None
    renderingNpi: Optional[str] = None
    facilityNpi: Optional[str] = None
    sourceFileName: Optional[str] = None
    sourceFilePath: Optional[str] = None
    name: Optional[str] = None
    status: str  # "not_submitted" | "in_progress" | "succeeded" | "failed"
    amount: float
    receiptAmount: float = 0.0
    contractAmount: float = 0.0
    underpaymentAmount: float = 0.0
    createdAt: datetime
    updatedAt: datetime
    submittedAt: Optional[datetime] = None
    notes: Optional[str] = None
    rulesApplied: Optional[List[str]] = None
    isBulkDownloaded: bool = False
    parsedData: Optional[Dict[str, Any]] = None
    findings: Optional[List[Dict[str, Any]]] = None
    repricingSummary: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class DocumentCreateResponse(BaseModel):
    document: Document
    message: str


class PaginatedDocumentsResponse(BaseModel):
    items: List[Document]
    total: int
    limit: int
    offset: int
    hasMore: bool


class BatchRun(BaseModel):
    id: str
    hospitalId: str
    projectId: Optional[str] = None
    status: str
    payerScope: str
    sourceFileCount: int
    claimDocumentCount: int
    processedClaimCount: int
    failedClaimCount: int
    executiveSummary: Optional[str] = None
    reconciliationJson: Optional[Dict[str, Any]] = None
    startedAt: Optional[datetime] = None
    finishedAt: Optional[datetime] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class BatchUploadResponse(BaseModel):
    batch: BatchRun
    filesQueued: int
    message: str


class ParsedDataRecord(BaseModel):
    id: str
    batchId: str
    documentId: str
    schemaVersion: str
    payload: Dict[str, Any]
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class AuditFinding(BaseModel):
    id: str
    batchId: str
    documentId: str
    findingCode: str
    severity: str
    confidenceScore: Optional[float] = None
    varianceAmount: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    createdAt: datetime

    class Config:
        from_attributes = True


class AuditNote(BaseModel):
    id: str
    batchId: Optional[str] = None
    documentId: Optional[str] = None
    noteType: str
    note: str
    createdBy: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class PatternRow(BaseModel):
    payerKey: Optional[str] = None
    cptHcpcs: Optional[str] = None
    modifier: Optional[str] = None
    placeOfService: Optional[str] = None
    localityCode: Optional[str] = None
    claimCount: int = 0
    totalVariance: float = 0.0
    confidence: float = 0.0


class AnalysisSummaryResponse(BaseModel):
    totalClaims: int
    totalServiceLines: int
    totalPaid: float
    totalExpected: float
    totalVariance: float
    claimsFlagged: int
    topCpts: List[PatternRow]
    topProviders: List[Dict[str, Any]]
    topPatterns: List[PatternRow]


class AppealBuildRequest(BaseModel):
    batchId: str
    payerKey: Optional[str] = None
    minimumVariance: Optional[float] = None


class AppealBuildResponse(BaseModel):
    batchId: str
    packet: Dict[str, Any]
    message: str


class RateImportResponse(BaseModel):
    payerKey: str
    versionLabel: str
    rowsImported: int
    rowCountTotal: int
    sha256: str
    message: str


class RateStatusResponse(BaseModel):
    versions: List[Dict[str, Any]]
    coverage: Dict[str, Any]



class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: Optional[str] = None
    payerScope: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    hospitalId: str
    name: str
    slug: str
    description: Optional[str] = None
    status: str
    payerScope: Optional[str] = None
    workspaceDuckdbPath: Optional[str] = None
    storagePrefix: Optional[str] = None
    workspaceSummary: Optional[Dict[str, Any]] = None
    createdAt: datetime
    updatedAt: datetime


class StoragePresignRequest(BaseModel):
    operation: str = "download"
    storageKey: Optional[str] = None
    prefix: Optional[str] = None
    fileName: Optional[str] = None


class StoragePresignResponse(BaseModel):
    storageKey: str
    operation: str
    expiresAt: int
    token: Optional[str] = None
    url: str
    backend: Optional[str] = None
    bucket: Optional[str] = None


class TruthVerificationRequest(BaseModel):
    batchRunId: Optional[str] = None


class TruthVerificationResponse(BaseModel):
    id: str
    projectId: str
    batchRunId: Optional[str] = None
    status: str
    verificationSummary: Dict[str, Any]
    createdAt: datetime
    completedAt: Optional[datetime] = None


class FormalAuditRunCreateRequest(BaseModel):
    batchRunId: Optional[str] = None
    verificationRunId: Optional[str] = None


class FormalAuditRunResponse(BaseModel):
    id: str
    projectId: str
    batchRunId: Optional[str] = None
    verificationRunId: Optional[str] = None
    status: str
    auditStandard: str
    report: Dict[str, Any]
    createdAt: datetime
    completedAt: Optional[datetime] = None
