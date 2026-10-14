from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SiteDashboardResponse(BaseModel):
    site_id: int
    site_name: str
    compliance_score: float
    total_guards: int
    scheduled_guards: int
    checked_in_guards: int
    missing_guards: int
    late_guards: int
    completed_guards: int
    violations: List[Dict[str, Any]] = []
    open_exceptions: int


class AnalyticsResponse(BaseModel):
    overall_compliance_score: float
    total_sites: int
    total_guards: int
    total_assignments: int
    open_exceptions_count: int
    resolved_exceptions_count: int
    exception_resolution_rate: float
    late_arrivals_count: int
    missed_shifts_count: int
    overtime_count: int
    gps_violations_count: int
    compliance_trend: List[Dict[str, Any]]
    attendance_trend: List[Dict[str, Any]]
    violation_trend: List[Dict[str, Any]]
    site_scores: List[Dict[str, Any]]
