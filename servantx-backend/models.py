import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class DocumentRole(str, enum.Enum):
    LEGACY = "LEGACY"
    FILE = "FILE"
    CLAIM = "CLAIM"


class LocalityOverrideEntityType(str, enum.Enum):
    BILLING_NPI = "BILLING_NPI"
    RENDERING_NPI = "RENDERING_NPI"
    FACILITY_NPI = "FACILITY_NPI"
    TAX_ID = "TAX_ID"


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    users = relationship("User", back_populates="hospital")
    contracts = relationship("Contract", back_populates="hospital")
    receipts = relationship("Receipt", back_populates="hospital")
    batch_runs = relationship("BatchRun", back_populates="hospital")
    projects = relationship("Project", back_populates="hospital")


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("hospital_id", "slug", name="uq_projects_hospital_slug"),)

    id = Column(String, primary_key=True, default=generate_uuid)
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="active")
    payer_scope = Column(String, nullable=True)
    workspace_duckdb_path = Column(String, nullable=True)
    storage_prefix = Column(String, nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    hospital = relationship("Hospital", back_populates="projects")
    creator = relationship("User", foreign_keys=[created_by], overlaps="created_projects")
    contracts = relationship("Contract", back_populates="project")
    receipts = relationship("Receipt", back_populates="project")
    batch_runs = relationship("BatchRun", back_populates="project")
    documents = relationship("Document", back_populates="project")
    artifacts = relationship("ProjectArtifact", back_populates="project")
    verification_runs = relationship("TruthVerificationRun", back_populates="project")
    audit_runs = relationship("FormalAuditRun", back_populates="project")


class ProjectArtifact(Base):
    __tablename__ = "project_artifacts"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True, index=True)
    artifact_type = Column(String, nullable=False, index=True)
    storage_key = Column(String, nullable=False)
    original_file_name = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    byte_size = Column(Integer, nullable=True)
    sha256 = Column(String, nullable=True, index=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship("Project", back_populates="artifacts")
    hospital = relationship("Hospital")
    document = relationship("Document")


class TruthVerificationRun(Base):
    __tablename__ = "truth_verification_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False, index=True)
    batch_run_id = Column(String, ForeignKey("batch_runs.id"), nullable=True, index=True)
    status = Column(String, nullable=False, default="pending")
    verification_summary = Column(JSON, nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="verification_runs")
    hospital = relationship("Hospital")
    batch_run = relationship("BatchRun")


class FormalAuditRun(Base):
    __tablename__ = "formal_audit_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False, index=True)
    batch_run_id = Column(String, ForeignKey("batch_runs.id"), nullable=True, index=True)
    verification_run_id = Column(String, ForeignKey("truth_verification_runs.id"), nullable=True, index=True)
    status = Column(String, nullable=False, default="draft")
    audit_standard = Column(String, nullable=False, default="MEDICAL_AUDIT_V1")
    report_json = Column(JSON, nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="audit_runs")
    hospital = relationship("Hospital")
    batch_run = relationship("BatchRun")
    verification_run = relationship("TruthVerificationRun")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    password = Column(String, nullable=True)
    username = Column(String, nullable=True)
    name = Column(String, nullable=False)
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False)
    role = Column(String, default="user", nullable=False)
    has_contract = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    reset_password_code = Column(String, nullable=True)
    reset_password_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    hospital = relationship("Hospital", back_populates="users")
    oauth_tokens = relationship("OAuthToken", back_populates="user")
    created_projects = relationship("Project", foreign_keys=[Project.created_by], overlaps="creator")


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String, primary_key=True, default=generate_uuid)
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)
    name = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    file_url = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String, default="processing", nullable=False)
    rules_extracted = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    rule_library = Column(JSON, nullable=True)

    hospital = relationship("Hospital", back_populates="contracts")
    project = relationship("Project", back_populates="contracts")


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(String, primary_key=True, default=generate_uuid)
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)
    has_difference = Column(Boolean, default=False, nullable=False)
    amount = Column(Float, default=0.0, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    document_id = Column(String, nullable=True)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    file_url = Column(String, nullable=True)
    status = Column(String, default="pending", nullable=False)

    hospital = relationship("Hospital", back_populates="receipts")
    project = relationship("Project", back_populates="receipts")
    documents = relationship("Document", back_populates="receipt")


class BatchRun(Base):
    __tablename__ = "batch_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)
    status = Column(String, nullable=False, default="queued")
    payer_scope = Column(String, nullable=False, default="MEDICARE_TX_MEDICAID_FFS")
    source_file_count = Column(Integer, nullable=False, default=0)
    claim_document_count = Column(Integer, nullable=False, default=0)
    processed_claim_count = Column(Integer, nullable=False, default=0)
    failed_claim_count = Column(Integer, nullable=False, default=0)
    executive_summary = Column(Text, nullable=True)
    reconciliation_json = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    hospital = relationship("Hospital", back_populates="batch_runs")
    project = relationship("Project", back_populates="batch_runs")
    documents = relationship("Document", back_populates="batch_run")
    parsed_data_entries = relationship("ParsedData", back_populates="batch_run")
    findings = relationship("AuditFinding", back_populates="batch_run")
    notes = relationship("AuditNote", back_populates="batch_run")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    receipt_id = Column(String, ForeignKey("receipts.id"), nullable=True, index=True)
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)
    batch_run_id = Column(String, ForeignKey("batch_runs.id"), nullable=True, index=True)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=True)
    document_role = Column(SAEnum(DocumentRole, name="document_role_enum"), nullable=False, default=DocumentRole.LEGACY, index=True)
    parent_document_id = Column(String, ForeignKey("documents.id"), nullable=True, index=True)
    payer_key = Column(String, nullable=True, index=True)
    dos_start = Column(Date, nullable=True)
    dos_end = Column(Date, nullable=True)
    billing_npi = Column(String, nullable=True)
    rendering_npi = Column(String, nullable=True)
    facility_npi = Column(String, nullable=True)
    source_file_name = Column(String, nullable=True)
    source_file_path = Column(String, nullable=True)
    name = Column(String, nullable=True)
    status = Column(String, default="not_submitted", nullable=False)
    amount = Column(Float, default=0.0, nullable=False)
    receipt_amount = Column(Float, default=0.0, nullable=False)
    contract_amount = Column(Float, default=0.0, nullable=False)
    underpayment_amount = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    rules_applied = Column(Text, nullable=True)
    is_bulk_downloaded = Column(Boolean, default=False, nullable=False)

    receipt = relationship("Receipt", back_populates="documents")
    hospital = relationship("Hospital")
    project = relationship("Project", back_populates="documents")
    contract = relationship("Contract")
    batch_run = relationship("BatchRun", back_populates="documents")
    parent_document = relationship(
        "Document",
        remote_side=[id],
        back_populates="child_documents",
        foreign_keys=[parent_document_id],
    )
    child_documents = relationship(
        "Document",
        back_populates="parent_document",
        foreign_keys=[parent_document_id],
    )
    parsed_data = relationship("ParsedData", back_populates="document", uselist=False)
    findings = relationship("AuditFinding", back_populates="document")
    audit_notes = relationship("AuditNote", back_populates="document")


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    access_token = Column(String, unique=True, nullable=False, index=True)
    refresh_token = Column(String, nullable=True, unique=True, index=True)
    token_type = Column(String, default="bearer", nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="oauth_tokens")


class ParsedData(Base):
    __tablename__ = "parsed_data"

    id = Column(String, primary_key=True, default=generate_uuid)
    batch_id = Column(String, ForeignKey("batch_runs.id"), nullable=False, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True, unique=True)
    schema_version = Column(String, nullable=False, default="claim_835_v1")
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    batch_run = relationship("BatchRun", back_populates="parsed_data_entries")
    document = relationship("Document", back_populates="parsed_data")


class AuditFinding(Base):
    __tablename__ = "audit_findings"

    id = Column(String, primary_key=True, default=generate_uuid)
    batch_id = Column(String, ForeignKey("batch_runs.id"), nullable=False, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    finding_code = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False, index=True)
    confidence_score = Column(Float, nullable=True)
    variance_amount = Column(Numeric(12, 2), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    batch_run = relationship("BatchRun", back_populates="findings")
    document = relationship("Document", back_populates="findings")


class AuditNote(Base):
    __tablename__ = "audit_notes"

    id = Column(String, primary_key=True, default=generate_uuid)
    batch_id = Column(String, ForeignKey("batch_runs.id"), nullable=True, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True, index=True)
    note_type = Column(String, nullable=False, default="general")
    note = Column(Text, nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    batch_run = relationship("BatchRun", back_populates="notes")
    document = relationship("Document", back_populates="audit_notes")


class RateVersion(Base):
    __tablename__ = "rate_versions"

    id = Column(String, primary_key=True, default=generate_uuid)
    payer_key = Column(String, nullable=False, index=True)
    version_label = Column(String, nullable=False)
    effective_start = Column(Date, nullable=True)
    effective_end = Column(Date, nullable=True)
    source_url = Column(Text, nullable=False)
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    row_count = Column(Integer, nullable=False, default=0)
    sha256 = Column(String, nullable=False)


class MedicareRvuRate(Base):
    __tablename__ = "medicare_rvu_rates"

    id = Column(String, primary_key=True, default=generate_uuid)
    year = Column(Integer, nullable=False, index=True)
    cpt_hcpcs = Column(String, nullable=False, index=True)
    work_rvu = Column(Numeric(12, 4), nullable=False)
    pe_rvu_facility = Column(Numeric(12, 4), nullable=False)
    pe_rvu_nonfacility = Column(Numeric(12, 4), nullable=False)
    mp_rvu = Column(Numeric(12, 4), nullable=False)
    status_indicator = Column(String, nullable=True)
    global_days = Column(String, nullable=True)


class MedicareGpci(Base):
    __tablename__ = "medicare_gpci"

    id = Column(String, primary_key=True, default=generate_uuid)
    year = Column(Integer, nullable=False, index=True)
    locality_code = Column(String, nullable=False, index=True)
    locality_name = Column(String, nullable=False)
    work_gpci = Column(Numeric(12, 4), nullable=False)
    pe_gpci = Column(Numeric(12, 4), nullable=False)
    mp_gpci = Column(Numeric(12, 4), nullable=False)


class MedicareConversionFactor(Base):
    __tablename__ = "medicare_conversion_factor"

    id = Column(String, primary_key=True, default=generate_uuid)
    year = Column(Integer, nullable=False, unique=True, index=True)
    conversion_factor = Column(Numeric(12, 4), nullable=False)


class MedicareZipLocality(Base):
    __tablename__ = "medicare_zip_locality"

    id = Column(String, primary_key=True, default=generate_uuid)
    zip_code = Column(String, nullable=False, index=True)
    locality_code = Column(String, nullable=False, index=True)


class LocalityOverride(Base):
    __tablename__ = "locality_overrides"

    id = Column(String, primary_key=True, default=generate_uuid)
    entity_type = Column(SAEnum(LocalityOverrideEntityType, name="entity_type_enum"), nullable=False, index=True)
    entity_id = Column(String, nullable=False, index=True)
    zip_code = Column(String, nullable=True)
    locality_code = Column(String, nullable=False)
    effective_start = Column(Date, nullable=True)
    effective_end = Column(Date, nullable=True)
    confidence = Column(Integer, nullable=False, default=100)
    note = Column(Text, nullable=True)


class TxMedicaidFfsFeeSchedule(Base):
    __tablename__ = "tx_medicaid_ffs_fee_schedule"

    id = Column(String, primary_key=True, default=generate_uuid)
    effective_start = Column(Date, nullable=False, index=True)
    effective_end = Column(Date, nullable=True, index=True)
    cpt_hcpcs = Column(String, nullable=False, index=True)
    modifier = Column(String, nullable=True, index=True)
    pricing_context = Column(String, nullable=False, default="STANDARD", index=True)
    source_code = Column(String, nullable=True, index=True)
    allowed_amount = Column(Numeric(12, 2), nullable=False)


class PhiTokenMap(Base):
    """
    HIPAA PHI De-identification Token Map.

    Stores mappings from deterministic PHI tokens (sent to LLMs) back to the
    original PHI values (stored locally only). Scoped per hospital with TTL.

    Tokens are deterministic: same (hospital_id, phi_field, phi_value) always
    produces the same token, so repeated encounters of the same PHI don't create
    duplicate rows — they reuse the existing token.
    """

    __tablename__ = "phi_token_map"
    __table_args__ = (
        UniqueConstraint("hospital_id", "token", name="uq_phi_token_map_hospital_token"),
    )

    id = Column(String, primary_key=True, default=generate_uuid)
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True, index=True)
    token = Column(String, nullable=False, index=True)
    phi_field = Column(String, nullable=False)
    phi_value = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    hospital = relationship("Hospital")
