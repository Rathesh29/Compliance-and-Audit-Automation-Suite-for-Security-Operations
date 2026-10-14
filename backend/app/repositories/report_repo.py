from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.report import Report


class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, report_id: int) -> Optional[Report]:
        return self.db.query(Report).filter(Report.id == report_id).first()

    def create(self, report: Report) -> Report:
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def list_reports(self, site_id: Optional[int] = None, report_type: Optional[str] = None, limit: int = 50) -> List[Report]:
        query = self.db.query(Report)
        if site_id:
            query = query.filter(Report.site_id == site_id)
        if report_type:
            query = query.filter(Report.report_type == report_type)
        return query.order_by(Report.id.desc()).limit(limit).all()
