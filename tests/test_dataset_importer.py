from unittest.mock import MagicMock

import pandas as pd

from models.employee import Employee
from schemas.project import StructuredRequirements
from services.dataset_importer import DatasetImporter
from services.recommendation_engine import RecommendationEngine


def create_mock_excel(tmp_path):
    df_emp = pd.DataFrame(
        [
            {
                "employee_id": "E1",
                "name": "Alice Test",
                "base_role": "Dev",
                "department": "Eng",
                "experience_years": 5,
                "current_tech_stack": "Python",
                "availability": "Yes",
                "location": "Remote",
                "projects_completed": 1,
                "tech_transitions": 1,
                "tech_history": "Java",
            }
        ]
    )
    df_proj = pd.DataFrame(
        [
            {
                "project_id": "P1",
                "project_name": "Test Proj",
                "domain": "Finance",
                "tech_stack": "Python",
                "team_size": 2,
                "duration_months": 3,
                "status": "Completed",
                "outcome": "Success",
            }
        ]
    )
    df_team = pd.DataFrame(
        [
            {
                "project_id": "P1",
                "employee_id": "E1",
                "employee_name": "Alice Test",
                "role_on_project": "Dev",
                "tech_stack_used": "Python",
                "project_contribution": "Code",
                "project_outcome": "Success",
                "tech_after_project": "Python",
            }
        ]
    )
    df_tech = pd.DataFrame(
        [
            {
                "employee_id": "E1",
                "employee_name": "Alice Test",
                "project_sequence": 1,
                "completed_project": "P1",
                "tech_used_on_project": "Java",
                "tech_after_project": "Python",
                "next_project_decision_should_use": "Python",
            }
        ]
    )
    df_mem = pd.DataFrame(
        [
            {
                "memory_id": "M1",
                "employee_id": "E1",
                "project_id": "P1",
                "memory_type": "Tech Transition",
                "memory": "Alice used Java then Python",
                "learning": "Update stack",
            }
        ]
    )

    file_path = tmp_path / "mock_dataset.xlsx"
    with pd.ExcelWriter(file_path) as writer:
        df_emp.to_excel(writer, sheet_name="Employees", index=False)
        df_proj.to_excel(writer, sheet_name="Projects", index=False)
        df_team.to_excel(writer, sheet_name="Project_Teams", index=False)
        df_tech.to_excel(writer, sheet_name="Tech_Transitions", index=False)
        df_mem.to_excel(writer, sheet_name="Hindsight_Memories", index=False)

    return str(file_path)


def test_workbook_validation(db_session, hindsight_adapter, tmp_path):
    file_path = create_mock_excel(tmp_path)
    importer = DatasetImporter(db_session, hindsight_adapter)
    valid, result = importer.validate_workbook(file_path)
    assert valid is True
    assert "sizes" in result


def test_idempotent_import(db_session, hindsight_adapter, tmp_path):
    file_path = create_mock_excel(tmp_path)
    importer = DatasetImporter(db_session, hindsight_adapter)

    counts1 = importer.import_workbook(file_path)
    assert counts1["employees"] == 1

    counts2 = importer.import_workbook(file_path)
    emps = db_session.query(Employee).all()
    assert len(emps) == 1
    mems = hindsight_adapter.list_all()
    assert len(mems) == 2


def test_recommendation_with_imported_data(db_session, hindsight_adapter, tmp_path):
    file_path = create_mock_excel(tmp_path)
    importer = DatasetImporter(db_session, hindsight_adapter)
    importer.import_workbook(file_path)

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "Mocked explanation."

    engine = RecommendationEngine(db_session, llm=mock_llm, hindsight=hindsight_adapter)
    reqs = StructuredRequirements(
        title="AI Banking",
        domain="Finance",
        required_skills=["Python"],
        optional_skills=[],
        team_size_min=1,
        team_size_max=2,
        duration_weeks=12,
        key_responsibilities=[],
        risks=[],
    )

    rec = engine.recommend(reqs)
    assert rec is not None
    assert rec.project_title == "AI Banking"
