"""Employee Import Service — CSV/Excel ingestion with configurable column mapping.

Pipeline:
    Bytes Input
        ↓
    File Validation (type, size)
        ↓
    Parse CSV / XLSX
        ↓
    Detect / Apply Column Mapping
        ↓
    Normalise Values
        ↓
    Pydantic Validation (per row)
        ↓
    Duplicate Detection (by email)
        ↓
    ImportReport (preview)
        ↓
    Database Write (only after caller confirms)

Security rules:
- Never execute uploaded content.
- Never deserialise arbitrary objects.
- File-size limit enforced before parsing.
- Only .csv and .xlsx accepted.
- All DB writes use parameterised SQLAlchemy queries.
"""

from __future__ import annotations

import csv
import io
import logging
import re

from sqlalchemy.orm import Session

from models.employee import Employee
from schemas.employee_import import (
    REQUIRED_CANONICAL_FIELDS,
    ImportConfig,
    ImportedEmployee,
    ImportReport,
    RowError,
    auto_detect_mapping,
)

logger = logging.getLogger(__name__)

_VALID_EXTENSIONS = {".csv", ".xlsx"}
_SENIORITY_VALUES = {"junior", "mid", "senior", "lead", "principal", "staff"}
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EmployeeImportService:
    """Parses, validates, and imports employee records from CSV or XLSX files.

    Usage:
        service = EmployeeImportService(session)
        report, valid_rows = service.parse_and_validate(file_bytes, "employees.csv", config)
        if user_confirmed:
            final_report = service.commit_import(valid_rows, report, config)
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Public API ────────────────────────────────────────────────────────────

    def parse_and_validate(
        self,
        file_bytes: bytes,
        filename: str,
        config: ImportConfig,
    ) -> tuple[ImportReport, list[ImportedEmployee]]:
        """Parse the file and return a preview report + list of valid rows.

        Does NOT write to the database.
        Raises ValueError for unsupported file types or size limit violations.
        """
        report = ImportReport()

        ext = self._get_extension(filename)
        if ext not in _VALID_EXTENSIONS:
            msg = f"Unsupported file type '{ext}'. Only .csv and .xlsx are accepted."
            raise ValueError(msg)

        if len(file_bytes) > config.max_file_bytes:
            mb = config.max_file_bytes // (1024 * 1024)
            msg = f"File exceeds {mb} MB limit."
            raise ValueError(msg)

        # Parse to raw rows
        raw_rows = self._parse_file(file_bytes, ext)

        if not raw_rows:
            report.messages.append("File is empty.")
            return report, []

        if len(raw_rows) > config.max_rows:
            msg = f"File has {len(raw_rows)} rows, exceeding the {config.max_rows} row limit."
            raise ValueError(msg)

        # Detect columns
        source_columns = list(raw_rows[0].keys())
        mapping = config.column_mapping or auto_detect_mapping(source_columns)

        # Check required fields are mapped
        missing_required = [f for f in REQUIRED_CANONICAL_FIELDS if f not in mapping]
        if missing_required:
            msg = (
                f"Required fields not mapped: {missing_required}. "
                f"Source columns available: {source_columns}"
            )
            raise ValueError(msg)

        # Validate each row
        valid_employees: list[ImportedEmployee] = []
        report.total_rows = len(raw_rows)

        for i, raw_row in enumerate(raw_rows, start=2):  # row 2 = first data row after header
            emp, errors = self._validate_row(i, raw_row, mapping)
            if errors:
                report.invalid_rows += 1
                report.errors.extend(errors)
            else:
                assert emp is not None  # guaranteed when no errors
                valid_employees.append(emp)

        report.valid_rows = len(valid_employees)

        # Duplicate detection (against existing DB)
        existing_emails = self._get_existing_emails()
        deduplicated: list[ImportedEmployee] = []
        for emp in valid_employees:
            if emp.email.lower() in existing_emails:
                report.duplicate_rows += 1
            else:
                deduplicated.append(emp)

        logger.info(
            "EmployeeImportService: parsed %d rows → %d valid, %d invalid, %d duplicates",
            report.total_rows,
            report.valid_rows,
            report.invalid_rows,
            report.duplicate_rows,
        )

        return report, deduplicated

    def commit_import(
        self,
        employees: list[ImportedEmployee],
        report: ImportReport,
        config: ImportConfig,
    ) -> ImportReport:
        """Write validated, deduplicated employees to the database.

        Must only be called after the user has confirmed the preview.
        """
        for emp in employees:
            db_employee = Employee(
                name=emp.name,
                email=emp.email,
                role=emp.role,
                department=emp.department,
                seniority=emp.seniority,
                years_of_experience=emp.years_of_experience,
                domain_expertise=emp.domain_expertise,
                is_available=emp.is_available,
                availability_percentage=emp.availability_percentage,
                performance_rating=emp.performance_rating,
                work_preferences=emp.work_preferences,
                location=emp.location,
                timezone=emp.timezone,
            )
            self._session.add(db_employee)

        self._session.flush()
        report.imported_rows = len(employees)
        report.skipped_rows = report.duplicate_rows + report.invalid_rows
        report.messages.append(f"Successfully imported {report.imported_rows} employees.")
        logger.info("EmployeeImportService: committed %d employees", report.imported_rows)
        return report

    # ── Column mapping helper ─────────────────────────────────────────────────

    @staticmethod
    def detect_columns(source_columns: list[str]) -> dict[str, str]:
        """Return auto-detected column mapping for a given list of source columns."""
        return auto_detect_mapping(source_columns)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_existing_emails(self) -> set[str]:
        """Return the set of all existing employee emails (lowercased)."""
        rows = self._session.query(Employee.email).all()
        return {row[0].lower() for row in rows}

    @staticmethod
    def _get_extension(filename: str) -> str:
        dot = filename.rfind(".")
        if dot == -1:
            return ""
        return filename[dot:].lower()

    @staticmethod
    def _parse_file(file_bytes: bytes, ext: str) -> list[dict[str, str]]:
        """Parse CSV or XLSX bytes into a list of dicts (one per data row)."""
        if ext == ".csv":
            return EmployeeImportService._parse_csv(file_bytes)
        return EmployeeImportService._parse_xlsx(file_bytes)

    @staticmethod
    def _parse_csv(file_bytes: bytes) -> list[dict[str, str]]:
        """Parse CSV bytes. Tries UTF-8 then latin-1 encoding."""
        for encoding in ("utf-8-sig", "latin-1"):
            try:
                text = file_bytes.decode(encoding)
                reader = csv.DictReader(io.StringIO(text))
                return [dict(row) for row in reader]
            except (UnicodeDecodeError, csv.Error):
                continue
        msg = "Unable to decode CSV file. Please use UTF-8 encoding."
        raise ValueError(msg)

    @staticmethod
    def _parse_xlsx(file_bytes: bytes) -> list[dict[str, str]]:
        """Parse XLSX bytes using openpyxl (read-only, no formula execution)."""
        try:
            import openpyxl
        except ImportError as exc:
            msg = "openpyxl is required for XLSX import. Run: pip install openpyxl"
            raise ImportError(msg) from exc

        wb = openpyxl.load_workbook(
            io.BytesIO(file_bytes),
            read_only=True,
            data_only=True,  # never evaluate formulae
        )
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []

        headers = [str(h).strip() if h is not None else "" for h in rows[0]]
        result: list[dict[str, str]] = []
        for row in rows[1:]:
            row_dict: dict[str, str] = {}
            for header, cell in zip(headers, row, strict=False):
                row_dict[header] = str(cell).strip() if cell is not None else ""
            result.append(row_dict)
        return result

    @staticmethod
    def _validate_row(
        row_num: int,
        raw: dict[str, str],
        mapping: dict[str, str],
    ) -> tuple[ImportedEmployee | None, list[RowError]]:
        """Validate a single raw row using the column mapping.

        Returns (ImportedEmployee, []) on success, or (None, [errors]) on failure.
        """
        errors: list[RowError] = []

        def get(canonical: str, default: str = "") -> str:
            col = mapping.get(canonical)
            if col is None:
                return default
            return raw.get(col, default).strip()

        # Required fields
        name = get("name")
        email = get("email")
        role = get("role")
        department = get("department")
        seniority = get("seniority")

        if not name:
            errors.append(RowError(row_number=row_num, field="name", problem="Name is required"))
        elif len(name) > 200:
            errors.append(
                RowError(row_number=row_num, field="name", problem="Name exceeds 200 characters")
            )

        if not email:
            errors.append(RowError(row_number=row_num, field="email", problem="Email is required"))
        elif not _EMAIL_RE.match(email):
            errors.append(
                RowError(row_number=row_num, field="email", problem=f"Invalid email: {email!r}")
            )

        if not role:
            errors.append(RowError(row_number=row_num, field="role", problem="Role is required"))
        elif len(role) > 120:
            errors.append(
                RowError(row_number=row_num, field="role", problem="Role exceeds 120 characters")
            )

        if not department:
            errors.append(
                RowError(row_number=row_num, field="department", problem="Department is required")
            )
        elif len(department) > 120:
            errors.append(
                RowError(
                    row_number=row_num,
                    field="department",
                    problem="Department exceeds 120 characters",
                )
            )

        seniority_clean = seniority.lower()
        if not seniority:
            errors.append(
                RowError(row_number=row_num, field="seniority", problem="Seniority is required")
            )
        elif seniority_clean not in _SENIORITY_VALUES:
            errors.append(
                RowError(
                    row_number=row_num,
                    field="seniority",
                    problem=f"Invalid seniority '{seniority}'. Must be one of: {sorted(_SENIORITY_VALUES)}",
                )
            )

        if errors:
            return None, errors

        # Optional fields — parse with sensible defaults
        years_exp = _parse_float(raw, mapping, "years_of_experience", 0.0)
        if years_exp < 0 or years_exp > 60:
            errors.append(
                RowError(
                    row_number=row_num,
                    field="years_of_experience",
                    problem=f"years_of_experience must be 0-60, got {years_exp}",
                )
            )

        avail_pct = _parse_int(raw, mapping, "availability_percentage", 100)
        if not (0 <= avail_pct <= 100):
            errors.append(
                RowError(
                    row_number=row_num,
                    field="availability_percentage",
                    problem=f"availability_percentage must be 0-100, got {avail_pct}",
                )
            )

        perf_col = mapping.get("performance_rating")
        perf_raw = raw.get(perf_col, "").strip() if perf_col else ""
        performance_rating: float | None = None
        if perf_raw:
            try:
                pf = float(perf_raw)
                if not (1.0 <= pf <= 5.0):
                    errors.append(
                        RowError(
                            row_number=row_num,
                            field="performance_rating",
                            problem=f"performance_rating must be 1.0-5.0, got {pf}",
                        )
                    )
                else:
                    performance_rating = pf
            except ValueError:
                errors.append(
                    RowError(
                        row_number=row_num,
                        field="performance_rating",
                        problem=f"Invalid number: {perf_raw!r}",
                    )
                )

        is_avail_raw = get("is_available", "true").lower()
        is_available = is_avail_raw not in ("false", "0", "no", "n")

        if errors:
            return None, errors

        return (
            ImportedEmployee(
                name=name,
                email=email.lower(),
                role=role,
                department=department,
                seniority=seniority_clean,
                years_of_experience=max(0.0, years_exp),
                domain_expertise=get("domain_expertise", ""),
                is_available=is_available,
                availability_percentage=min(100, max(0, avail_pct)),
                performance_rating=performance_rating,
                work_preferences=get("work_preferences", ""),
                location=get("location", ""),
                timezone=get("timezone", "UTC") or "UTC",
            ),
            [],
        )


# ── Parsing helpers ───────────────────────────────────────────────────────────


def _parse_float(
    raw: dict[str, str], mapping: dict[str, str], canonical: str, default: float
) -> float:
    col = mapping.get(canonical)
    if col is None:
        return default
    val = raw.get(col, "").strip()
    if not val:
        return default
    try:
        return float(val)
    except ValueError:
        return default


def _parse_int(raw: dict[str, str], mapping: dict[str, str], canonical: str, default: int) -> int:
    col = mapping.get(canonical)
    if col is None:
        return default
    val = raw.get(col, "").strip()
    if not val:
        return default
    try:
        return int(float(val))
    except ValueError:
        return default
