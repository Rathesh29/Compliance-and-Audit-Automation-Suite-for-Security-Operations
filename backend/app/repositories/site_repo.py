from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.site import Site


class SiteRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, site_id: int) -> Optional[Site]:
        return self.db.query(Site).filter(Site.id == site_id).first()

    def get_by_qr_token(self, qr_token: str) -> Optional[Site]:
        return self.db.query(Site).filter(Site.qr_token == qr_token).first()

    def list_sites(self, search: Optional[str] = None) -> List[Site]:
        query = self.db.query(Site)
        if search:
            s = f"%{search}%"
            query = query.filter((Site.name.ilike(s)) | (Site.location_name.ilike(s)))
        return query.order_by(Site.id.asc()).all()

    def create(self, site: Site) -> Site:
        self.db.add(site)
        self.db.commit()
        self.db.refresh(site)
        return site

    def update(self, site: Site) -> Site:
        self.db.commit()
        self.db.refresh(site)
        return site
