"""Pydantic schemas for employee CSV/Excel import.

Column mapping is configurable — do not assume any specific column name.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# ── Column mapping ────────────────────────────────────────────────────────────

# Canonical field names match EmployeeBase fields from schemas/employee.py.
CANONICAL_FIELDS: list[str] = [
    "name",
    "email",
    "role",
    "department",
    "seniority",
    "years_of_experience",
    "domain_expertise",
    "is_available",
    "availability_percentage",
    "performance_rating",
    "work_preferences",
    "location",
    "timezone",
]

REQUIRED_CANONICAL_FIELDS: list[str] = ["name", "email", "role", "department", "seniority"]

# Common aliases for auto-detection (canonical → list of known aliases, lowercased)
FIELD_ALIASES: dict[str, list[str]] = {
    "name": ["name", "employee name", "full name", "staff name", "employee_name", "fullname"],
    "email": ["email", "email address", "e-mail", "work email", "employee email"],
    "role": ["role", "job title", "title", "position", "job_title", "job role"],
    "department": ["department", "dept", "team", "division", "business unit"],
    "seniority": ["seniority", "level", "grade", "seniority level", "career level"],
    "years_of_experience": [
        "years of experience",
        "years_of_experience",
        "experience",
        "years_experience",
        "years exp",
        "years",
        "total experience",
    ],
    "domain_expertise": [
        "domain expertise",
        "domain",
        "specialization",
        "expertise",
        "domain_expertise",
    ],
    "is_available": ["available", "is available", "is_available", "availability status"],
    "availability_percentage": [
        "availability_percentage",
        "availability",
        "availability %",
        "availability percentage",
        "available %",
        "capacity",
    ],
    "performance_rating": [
        "performance_rating",
        "performance rating",
        "rating",
        "performance",
        "performance score",
        "perf rating",
    ],
    "work_preferences": ["work preferences", "work style", "preferences", "work_preferences"],
    "location": ["location", "city", "office", "office location"],
    "timezone": ["timezone", "time zone", "tz"],
}


def auto_detect_mapping(source_columns: list[str]) -> dict[str, str]:
    """Return a best-effort mapping of canonical → source_column based on aliases.

    Only maps columns that can be confidently matched.
    """
    mapping: dict[str, str] = {}
    lower_cols = {col.lower().strip(): col for col in source_columns}

    for canonical, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias in lower_cols:
                mapping[canonical] = lower_cols[alias]
                break  # first match wins

    return mapping


# ── Import configuration ──────────────────────────────────────────────────────


class ImportConfig(BaseModel):
    """Configuration for a single import run.

    column_mapping: maps canonical field names → actual column names in the file.
    skip_duplicates: if True, existing employees (matched by email) are skipped.
    max_rows: reject files with more rows than this limit (DoS protection).
    """

    column_mapping: dict[str, str] = Field(
        default_factory=dict,
        description="Maps canonical field names to source column names",
    )
    skip_duplicates: bool = Field(default=True)
    max_rows: int = Field(default=5000, ge=1, le=50_000)
    max_file_bytes: int = Field(default=10 * 1024 * 1024)  # 10 MB


# ── Per-row validation results ────────────────────────────────────────────────


class RowError(BaseModel):
    row_number: int
    field: str
    problem: str


class ImportedEmployee(BaseModel):
    """Normalised employee data after mapping and validation."""

    name: str
    email: str
    role: str
    department: str
    seniority: str
    years_of_experience: float = 0.0
    domain_expertise: str = ""
    is_available: bool = True
    availability_percentage: int = 100
    performance_rating: float | None = None
    work_preferences: str = ""
    location: str = ""
    timezone: str = "UTC"


# ── Import report ─────────────────────────────────────────────────────────────


class ImportReport(BaseModel):
    """Summary returned after an import attempt."""

    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    duplicate_rows: int = 0
    imported_rows: int = 0
    skipped_rows: int = 0
    errors: list[RowError] = Field(default_factory=list)
    messages: list[str] = Field(default_factory=list)
