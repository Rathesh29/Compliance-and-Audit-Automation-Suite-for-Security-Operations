import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime, timezone

from app.database.session import Base, get_db
from app.main import app
from app.models.user import User
from app.models.site import Site
from app.models.shift import Shift
from app.models.assignment import Assignment
from app.models.enums import UserRole, UserStatus, AssignmentStatus
from app.core.security import get_password_hash, create_access_token

# Use isolated test sqlite database in memory
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_security_compliance.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seed_test_data(db_session):
    # Create test users
    admin = db_session.query(User).filter(User.email == "test_admin@ops.com").first()
    if not admin:
        pwd = get_password_hash("TestPass123!")
        admin = User(name="Test Admin", email="test_admin@ops.com", password_hash=pwd, role="ADMIN", status="ACTIVE")
        supervisor = User(name="Test Supervisor", email="test_sup@ops.com", password_hash=pwd, role="SUPERVISOR", status="ACTIVE")
        auditor = User(name="Test Auditor", email="test_aud@ops.com", password_hash=pwd, role="AUDITOR", status="ACTIVE")
        guard = User(name="Test Guard", email="test_guard@ops.com", password_hash=pwd, role="GUARD", status="ACTIVE")
        other_guard = User(name="Other Guard", email="other_guard@ops.com", password_hash=pwd, role="GUARD", status="ACTIVE")
        db_session.add_all([admin, supervisor, auditor, guard, other_guard])
        db_session.commit()

        # Create test site
        site = Site(
            name="Alpha Facility",
            location_name="Alpha Gate",
            latitude=37.7749,
            longitude=-122.4194,
            radius_meters=100.0,
            qr_token="TEST-QR-ALPHA",
            compliance_rules={
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
        db_session.add(site)

        # Create test shift
        shift = Shift(name="Morning Patrol", start_time="08:00", end_time="16:00", grace_period_minutes=15)
        overnight = Shift(name="Night Watch", start_time="22:00", end_time="06:00", grace_period_minutes=10)
        db_session.add_all([shift, overnight])
        db_session.commit()


@pytest.fixture
def admin_headers(seed_test_data, db_session):
    u = db_session.query(User).filter(User.email == "test_admin@ops.com").first()
    token = create_access_token({"user_id": u.id, "email": u.email, "role": u.role, "name": u.name})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def supervisor_headers(seed_test_data, db_session):
    u = db_session.query(User).filter(User.email == "test_sup@ops.com").first()
    token = create_access_token({"user_id": u.id, "email": u.email, "role": u.role, "name": u.name})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auditor_headers(seed_test_data, db_session):
    u = db_session.query(User).filter(User.email == "test_aud@ops.com").first()
    token = create_access_token({"user_id": u.id, "email": u.email, "role": u.role, "name": u.name})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def guard_headers(seed_test_data, db_session):
    u = db_session.query(User).filter(User.email == "test_guard@ops.com").first()
    token = create_access_token({"user_id": u.id, "email": u.email, "role": u.role, "name": u.name})
    return {"Authorization": f"Bearer {token}"}
