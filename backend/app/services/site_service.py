from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.site import Site
from app.schemas.site import SiteCreate, SiteUpdate
from app.repositories.site_repo import SiteRepository
from app.utils.qr import generate_secure_qr_token, generate_qr_code_base64
from app.services.audit_service import AuditService
from app.services.compliance_engine import ComplianceEngine


class SiteService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SiteRepository(db)
        self.audit = AuditService(db)
        self.compliance_engine = ComplianceEngine(db)

    def get_site(self, site_id: int) -> Optional[Site]:
        return self.repo.get_by_id(site_id)

    def list_sites(self, search: Optional[str] = None) -> List[Site]:
        sites = self.repo.list_sites(search=search)
        # Update dynamic compliance score on read
        for s in sites:
            score = self.compliance_engine.calculate_site_compliance_score(s.id)
            if s.compliance_score != score:
                s.compliance_score = score
                self.repo.update(s)
        return sites

    def create_site(self, payload: SiteCreate, performed_by: str) -> Site:
        qr_token = generate_secure_qr_token()
        site = Site(
            name=payload.name,
            location_name=payload.location_name,
            latitude=payload.latitude,
            longitude=payload.longitude,
            radius_meters=payload.radius_meters,
            qr_token=qr_token,
            compliance_rules=payload.compliance_rules or {
                "max_daily_hours": 12,
                "minimum_rest_hours": 8,
                "max_weekly_hours": 60,
                "allow_overtime": False,
                "require_qr": True,
                "require_gps": True,
                "late_threshold_minutes": 10
            },
            compliance_score=100.0
        )
        saved = self.repo.create(site)

        self.audit.log_event(
            entity_type="SITE",
            entity_id=str(saved.id),
            action="SITE_CREATED",
            performed_by=performed_by,
            metadata={
                "name": saved.name,
                "location": saved.location_name,
                "radius_meters": saved.radius_meters
            }
        )
        return saved

    def update_site(self, site_id: int, payload: SiteUpdate, performed_by: str) -> Site:
        site = self.repo.get_by_id(site_id)
        if not site:
            raise ValueError("Site not found")

        if payload.name is not None:
            site.name = payload.name
        if payload.location_name is not None:
            site.location_name = payload.location_name
        if payload.latitude is not None:
            site.latitude = payload.latitude
        if payload.longitude is not None:
            site.longitude = payload.longitude
        if payload.radius_meters is not None:
            site.radius_meters = payload.radius_meters
        if payload.compliance_rules is not None:
            site.compliance_rules = payload.compliance_rules

        # Recalculate compliance score
        site.compliance_score = self.compliance_engine.calculate_site_compliance_score(site.id)
        updated = self.repo.update(site)

        self.audit.log_event(
            entity_type="SITE",
            entity_id=str(updated.id),
            action="SITE_UPDATED",
            performed_by=performed_by,
            metadata={"name": updated.name}
        )
        return updated

    def get_site_qr(self, site_id: int) -> Dict[str, Any]:
        site = self.repo.get_by_id(site_id)
        if not site:
            raise ValueError("Site not found")

        qr_b64 = generate_qr_code_base64(site.qr_token)
        return {
            "site_id": site.id,
            "site_name": site.name,
            "qr_token": site.qr_token,
            "qr_code_base64": qr_b64
        }

    def get_compliance_score(self, site_id: int) -> Dict[str, Any]:
        site = self.repo.get_by_id(site_id)
        if not site:
            raise ValueError("Site not found")
        score = self.compliance_engine.calculate_site_compliance_score(site.id)
        site.compliance_score = score
        self.repo.update(site)
        return {
            "site_id": site.id,
            "site_name": site.name,
            "compliance_score": score,
            "status": "EXCELLENT" if score >= 90 else ("GOOD" if score >= 75 else ("WARNING" if score >= 60 else "CRITICAL"))
        }
