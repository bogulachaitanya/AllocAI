"""Dataset Importer Service for Excel data."""

import logging
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from hindsight.adapter import HindsightAdapter
from hindsight.models import MemoryType, RetainRequest
from models.assignment import Assignment
from models.employee import Employee
from models.project import Project

logger = logging.getLogger(__name__)


class DatasetImporter:
    """Imports complex Excel dataset into ProjectMind database and Hindsight."""

    def __init__(self, session: Session, hindsight_adapter: HindsightAdapter):
        self.session = session
        self.hindsight_adapter = hindsight_adapter

    def validate_workbook(self, file_path: str) -> tuple[bool, dict[str, Any]]:
        """Validate that all required sheets and columns exist."""
        required_sheets = {
            "Employees": [
                "employee_id",
                "name",
                "base_role",
                "department",
                "experience_years",
                "current_tech_stack",
                "availability",
                "location",
                "projects_completed",
                "tech_transitions",
                "tech_history",
            ],
            "Projects": [
                "project_id",
                "project_name",
                "domain",
                "tech_stack",
                "team_size",
                "duration_months",
                "status",
                "outcome",
            ],
            "Project_Teams": [
                "project_id",
                "employee_id",
                "employee_name",
                "role_on_project",
                "tech_stack_used",
                "project_contribution",
                "project_outcome",
                "tech_after_project",
            ],
            "Tech_Transitions": [
                "employee_id",
                "employee_name",
                "project_sequence",
                "completed_project",
                "tech_used_on_project",
                "tech_after_project",
                "next_project_decision_should_use",
            ],
            "Hindsight_Memories": [
                "memory_id",
                "employee_id",
                "project_id",
                "memory_type",
                "memory",
                "learning",
            ],
        }

        try:
            xl = pd.ExcelFile(file_path)
            sheets = xl.sheet_names
        except Exception as e:
            return False, {"error": f"Failed to read Excel file: {e!s}"}

        errors = []
        for sheet, cols in required_sheets.items():
            if sheet not in sheets:
                errors.append(f"Missing sheet: {sheet}")
            else:
                df = xl.parse(sheet)
                missing_cols = [c for c in cols if c not in df.columns]
                if missing_cols:
                    errors.append(f"Missing columns in {sheet}: {missing_cols}")

        if errors:
            return False, {"errors": errors}

        # Basic check for sizes
        sizes = {}
        for sheet in required_sheets.keys():
            sizes[sheet] = len(xl.parse(sheet))

        return True, {"sizes": sizes}

    def import_workbook(self, file_path: str) -> dict[str, int]:
        """Perform the actual import. Must be called after validation."""
        xl = pd.ExcelFile(file_path)

        # 1. Import Employees
        df_emp = xl.parse("Employees").fillna("")
        emp_count = 0
        existing_emp_names = {e.name: e.id for e in self.session.query(Employee).all()}
        # We need a stable identifier, but dataset uses 'employee_id' which is not in Employee model.
        # However, we can use 'email' to deduplicate. The dataset doesn't have email!
        # We'll use name as unique identifier, or generate fake email from name.

        # We'll store a mapping of source employee_id to db employee.id
        emp_id_map = {}

        for _, row in df_emp.iterrows():
            name = str(row["name"]).strip()
            # Idempotent: check if exists
            if name in existing_emp_names:
                emp_id_map[str(row["employee_id"])] = existing_emp_names[name]
                continue

            email = name.lower().replace(" ", ".") + "@example.com"
            avail_str = str(row["availability"]).lower()
            is_avail = "avail" in avail_str

            # current_tech_stack is e.g. "Python | FastAPI | PostgreSQL"
            # Store as-is in domain_expertise for display; create EmployeeSkill rows below
            current_tech_raw = str(row.get("current_tech_stack", "")).strip()
            tech_history_raw = str(row.get("tech_history", "")).strip()

            emp = Employee(
                name=name,
                email=email,
                role=str(row["base_role"]).strip(),
                department=str(row["department"]).strip(),
                seniority="senior",  # Default as not in dataset
                years_of_experience=float(row["experience_years"])
                if row["experience_years"]
                else 0.0,
                # domain_expertise stores the raw current tech stack for display
                domain_expertise=current_tech_raw,
                # work_preferences stores tech_history for historical skill extraction
                work_preferences=tech_history_raw,
                is_available=is_avail,
                availability_percentage=100 if is_avail else 0,
                location=str(row["location"]),
            )
            self.session.add(emp)
            self.session.flush()  # to get ID
            existing_emp_names[name] = emp.id
            emp_id_map[str(row["employee_id"])] = emp.id

            # ── Create EmployeeSkill rows from current_tech_stack ─────────
            if current_tech_raw:
                for tech in current_tech_raw.split("|"):
                    tech_name = tech.strip()
                    if not tech_name:
                        continue
                    existing_skill = (
                        self.session.query(__import__("models.employee", fromlist=["Skill"]).Skill)
                        .filter_by(name=tech_name)
                        .first()
                    )
                    if existing_skill is None:
                        from models.employee import Skill

                        existing_skill = Skill(name=tech_name, category="Technology")
                        self.session.add(existing_skill)
                        self.session.flush()
                    from models.employee import EmployeeSkill

                    emp_skill = EmployeeSkill(
                        employee_id=emp.id,
                        skill_id=existing_skill.id,
                        proficiency=3,  # Proficient (current stack = known)
                        years_with_skill=0.0,
                    )
                    self.session.add(emp_skill)

            emp_count += 1

        # 2. Import Projects
        df_proj = xl.parse("Projects").fillna("")
        proj_count = 0
        existing_proj_titles = {p.title: p.id for p in self.session.query(Project).all()}
        proj_id_map = {}

        for _, row in df_proj.iterrows():
            title = str(row["project_name"]).strip()
            if title in existing_proj_titles:
                proj_id_map[str(row["project_id"])] = existing_proj_titles[title]
                continue

            duration = (
                int(row["duration_months"]) * 4 if str(row["duration_months"]).isdigit() else 0
            )
            team_size = int(row["team_size"]) if str(row["team_size"]).isdigit() else 1

            proj = Project(
                title=title,
                domain=str(row["domain"]),
                status=str(row["status"]).lower(),
                team_size_min=team_size,
                team_size_max=team_size,
                duration_weeks=duration,
            )
            self.session.add(proj)
            self.session.flush()
            existing_proj_titles[title] = proj.id
            proj_id_map[str(row["project_id"])] = proj.id
            proj_count += 1

        # 3. Import Project Teams (Assignments)
        df_teams = xl.parse("Project_Teams").fillna("")
        team_count = 0

        # Get existing assignments to avoid duplicates
        existing_assignments = set(
            (a.employee_id, a.project_id) for a in self.session.query(Assignment).all()
        )

        for _, row in df_teams.iterrows():
            e_id_src = str(row["employee_id"])
            p_id_src = str(row["project_id"])
            if e_id_src not in emp_id_map or p_id_src not in proj_id_map:
                continue

            db_e_id = emp_id_map[e_id_src]
            db_p_id = proj_id_map[p_id_src]

            if (db_e_id, db_p_id) in existing_assignments:
                continue

            notes = (
                f"Contribution: {row['project_contribution']}\n"
                f"Tech Stack Used: {row['tech_stack_used']}\n"
                f"Project Outcome: {row['project_outcome']}\n"
                f"Tech After Project: {row['tech_after_project']}"
            )

            assign = Assignment(
                employee_id=db_e_id,
                project_id=db_p_id,
                role_on_project=str(row["role_on_project"]),
                status="completed" if str(row["project_outcome"]).lower() != "active" else "active",
                manager_notes=notes,
            )
            self.session.add(assign)
            existing_assignments.add((db_e_id, db_p_id))
            team_count += 1

        self.session.commit()

        # 4 & 5. Import Tech Transitions and Hindsight Memories
        # We will map both as Hindsight Memories.
        # Hindsight Memories sheet has clear mapping.
        # Tech Transitions will be added as "Tech Transition" memory type if not redundant.

        memories_count = 0
        df_mem = xl.parse("Hindsight_Memories").fillna("")
        existing_mem_ids = {m.memory_id for m in self.hindsight_adapter.list_all(limit=10000)}

        retain_reqs = []
        for _, row in df_mem.iterrows():
            mem_id = str(row["memory_id"])
            if mem_id in existing_mem_ids:
                continue

            e_id_src = str(row["employee_id"])
            p_id_src = str(row["project_id"])

            db_e_id = str(emp_id_map.get(e_id_src, e_id_src))
            db_p_id = str(proj_id_map.get(p_id_src, p_id_src))

            # Using exact fields as required
            m_type_str = str(row["memory_type"]).strip()
            # fallback if unknown
            m_type = (
                MemoryType.TECH_TRANSITION
                if m_type_str == "Tech Transition"
                else MemoryType.PROJECT_OUTCOME
            )

            req = RetainRequest(
                memory_id=mem_id,
                content=str(row["memory"]),
                summary=str(row["learning"]),
                memory_type=m_type,
                project_title=f"Project {p_id_src}",
                metadata={"employee_id": db_e_id, "project_id": db_p_id, "source": "excel_import"},
            )
            retain_reqs.append(req)
            existing_mem_ids.add(mem_id)
            memories_count += 1

        # Process Tech Transitions as Memories too
        df_tech = xl.parse("Tech_Transitions").fillna("")
        tech_trans_count = 0
        for idx, row in df_tech.iterrows():
            e_id_src = str(row["employee_id"])
            p_id_src = str(row["completed_project"])
            db_e_id = str(emp_id_map.get(e_id_src, e_id_src))
            db_p_id = str(proj_id_map.get(p_id_src, p_id_src))

            # Generate a stable ID for idempotent import
            mem_id = f"TECH_TRANS_{e_id_src}_{p_id_src}_{idx}"
            if mem_id in existing_mem_ids:
                continue

            content = f"Tech Transition for {row['employee_name']}: used '{row['tech_used_on_project']}' on project {p_id_src}, transitioned to '{row['tech_after_project']}'."
            summary = f"Decision should use: {row['next_project_decision_should_use']}"

            req = RetainRequest(
                memory_id=mem_id,
                content=content,
                summary=summary,
                memory_type=MemoryType.TECH_TRANSITION,
                metadata={
                    "employee_id": db_e_id,
                    "project_id": db_p_id,
                    "source": "excel_import_tech",
                },
            )
            retain_reqs.append(req)
            existing_mem_ids.add(mem_id)
            tech_trans_count += 1

        if retain_reqs:
            self.hindsight_adapter.bulk_retain(retain_reqs)

        return {
            "employees": emp_count,
            "projects": proj_count,
            "assignments": team_count,
            "tech_transitions": tech_trans_count,
            "hindsight_memories": memories_count,
        }
