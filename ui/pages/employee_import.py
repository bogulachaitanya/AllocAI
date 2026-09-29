"""Streamlit page — Employee Import.

Workflow:
    Upload CSV or XLSX
        ↓
    Detect / configure column mapping
        ↓
    Preview valid / invalid / duplicate rows
        ↓
    User confirms
        ↓
    Database import
        ↓
    Import report

Security:
    - File-type and size validation enforced in the service layer.
    - Uploaded bytes are never executed.
    - DB writes happen only after explicit user confirmation.
"""

from __future__ import annotations

import logging

import streamlit as st

logger = logging.getLogger(__name__)


def render() -> None:
    st.title("📥 Employee Import")
    st.caption("Import employees from CSV or Excel files with configurable column mapping.")

    # ── File upload ───────────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "Upload employee file",
        type=["csv", "xlsx"],
        help="Accepted formats: CSV (.csv) or Excel (.xlsx). Maximum 10 MB.",
    )

    if uploaded is None:
        _render_instructions()
        return

    file_bytes = uploaded.read()
    filename = uploaded.name

    st.info(f"📄 **{filename}** — {len(file_bytes) / 1024:.1f} KB uploaded")

    # ── Parse to detect source columns ───────────────────────────────────────
    from schemas.employee_import import (
        CANONICAL_FIELDS,
        REQUIRED_CANONICAL_FIELDS,
        ImportConfig,
        auto_detect_mapping,
    )
    from services.employee_import_service import EmployeeImportService

    try:
        # Quick-parse to get column names without validating yet
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext == "csv":
            import csv as csv_mod
            import io

            text = file_bytes.decode("utf-8-sig", errors="replace")
            reader = csv_mod.DictReader(io.StringIO(text))
            source_columns: list[str] = reader.fieldnames or []
        else:
            import io

            import openpyxl

            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
            ws = wb.active
            first_row = next(ws.iter_rows(values_only=True), None)
            source_columns = [str(h).strip() for h in first_row] if first_row else []
    except Exception as exc:
        st.error(f"Could not read file headers: {exc}")
        return

    if not source_columns:
        st.error("File appears empty or has no header row.")
        return

    st.success(f"Detected {len(source_columns)} columns: `{', '.join(source_columns)}`")

    # ── Column mapping UI ─────────────────────────────────────────────────────
    st.subheader("Column Mapping")
    st.caption(
        "Map each canonical field to the matching column in your file. "
        "Required fields are marked ✱."
    )

    auto_map = auto_detect_mapping(source_columns)
    col_options = ["(not mapped)", *source_columns]

    mapping: dict[str, str] = {}
    cols_per_row = 3
    field_chunks = [
        CANONICAL_FIELDS[i : i + cols_per_row]
        for i in range(0, len(CANONICAL_FIELDS), cols_per_row)
    ]

    for chunk in field_chunks:
        ui_cols = st.columns(cols_per_row)
        for ui_col, canonical in zip(ui_cols, chunk, strict=False):
            label = f"{'✱ ' if canonical in REQUIRED_CANONICAL_FIELDS else ''}{canonical}"
            default = auto_map.get(canonical, "(not mapped)")
            default_idx = col_options.index(default) if default in col_options else 0
            chosen = ui_col.selectbox(
                label,
                options=col_options,
                index=default_idx,
                key=f"mapping_{canonical}",
            )
            if chosen != "(not mapped)":
                mapping[canonical] = chosen

    # ── Validate mapping coverage ─────────────────────────────────────────────
    missing_required = [f for f in REQUIRED_CANONICAL_FIELDS if f not in mapping]
    if missing_required:
        st.warning(
            f"⚠️ Required fields not yet mapped: **{', '.join(missing_required)}**. "
            "Please complete the mapping above."
        )
        return

    # ── Options ───────────────────────────────────────────────────────────────
    skip_duplicates = st.checkbox("Skip duplicate employees (matched by email)", value=True)
    config = ImportConfig(column_mapping=mapping, skip_duplicates=skip_duplicates)

    # ── Preview ───────────────────────────────────────────────────────────────
    if st.button("🔍 Preview Import", type="primary"):
        from db.session import get_db

        with get_db() as session:
            service = EmployeeImportService(session)
            try:
                report, valid_rows = service.parse_and_validate(file_bytes, filename, config)
            except ValueError as exc:
                st.error(f"Import failed: {exc}")
                return

        st.session_state["import_report"] = report
        st.session_state["import_valid_rows"] = valid_rows
        st.session_state["import_config"] = config
        st.session_state["import_filename"] = filename

    # ── Show preview results ──────────────────────────────────────────────────
    report = st.session_state.get("import_report")
    valid_rows = st.session_state.get("import_valid_rows", [])

    if report is None:
        return

    st.divider()
    st.subheader("Import Preview")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Rows", report.total_rows)
    m2.metric("Valid", report.valid_rows, delta=None)
    m3.metric("Invalid", report.invalid_rows, delta=None)
    m4.metric("Duplicates", report.duplicate_rows, delta=None)

    if valid_rows:
        with st.expander(f"✅ Valid records ({len(valid_rows)})", expanded=False):
            import pandas as pd

            df = pd.DataFrame([r.model_dump() for r in valid_rows])
            st.dataframe(df, use_container_width=True)

    if report.errors:
        with st.expander(f"❌ Invalid rows ({report.invalid_rows})", expanded=True):
            import pandas as pd

            err_df = pd.DataFrame([e.model_dump() for e in report.errors])
            st.dataframe(err_df, use_container_width=True)

    # ── Confirm and import ────────────────────────────────────────────────────
    if not valid_rows:
        st.warning("No valid rows to import.")
        return

    st.info(f"Ready to import **{len(valid_rows)}** employee(s). This will write to the database.")

    if st.button(f"✅ Import {len(valid_rows)} Employee(s)", type="primary"):
        from db.session import get_db

        with get_db() as session:
            service = EmployeeImportService(session)
            cfg = st.session_state.get("import_config", config)
            final_report = service.commit_import(valid_rows, report, cfg)
            session.commit()

        st.success(f"✅ Imported **{final_report.imported_rows}** employee(s) successfully.")
        if final_report.messages:
            for msg in final_report.messages:
                st.caption(msg)

        # Clear session state after successful import
        for key in ["import_report", "import_valid_rows", "import_config", "import_filename"]:
            st.session_state.pop(key, None)


def _render_instructions() -> None:
    """Show upload instructions when no file has been uploaded."""
    st.markdown("""
### How to use

1. **Prepare your file** — CSV (`.csv`) or Excel (`.xlsx`), up to 10 MB.
2. **Upload** the file using the file picker above.
3. **Map columns** — the system will auto-detect common column names. Adjust as needed.
4. **Preview** — review valid, invalid, and duplicate rows before committing.
5. **Confirm** — click *Import* to write to the database.

---

### Required fields

| Field | Description |
|---|---|
| `name` | Employee full name |
| `email` | Work email address (used for duplicate detection) |
| `role` | Job title / role |
| `department` | Department or team |
| `seniority` | One of: `junior`, `mid`, `senior`, `lead`, `principal`, `staff` |

### Optional fields

| Field | Description |
|---|---|
| `years_of_experience` | Number (0–60) |
| `domain_expertise` | Comma-separated domains, e.g. `fintech,ml` |
| `availability_percentage` | Integer 0–100 |
| `performance_rating` | Float 1.0–5.0 |
| `work_preferences` | e.g. `remote,agile` |
| `location` | City or office |
| `timezone` | e.g. `UTC`, `US/Eastern` |

---

### Column naming

Column names in your file **do not need to match exactly**.
The system recognises common aliases such as:
- `name` → `Employee Name`, `Full Name`, `Staff Name`
- `email` → `Email Address`, `Work Email`
- `role` → `Job Title`, `Position`, `Title`
- `department` → `Dept`, `Division`, `Team`
- `seniority` → `Level`, `Grade`, `Career Level`

Use the **column mapping** controls to fix any undetected columns.
    """)
