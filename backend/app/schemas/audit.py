from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: str
    action: str
    performed_by: str
    timestamp: str
    metadata: Dict[str, Any] = {}
    previous_hash: str
    record_hash: str

    class Config:
        from_attributes = True


class AuditIntegrityResponse(BaseModel):
    valid: bool
    records_checked: int
    tampered_records: List[int] = []
    genesis_valid: bool = True
    chain_head: Optional[str] = None
