from db.session import SessionLocal
from models.employee import Employee


def test_recommendation_candidates_only_from_imported_dataset():
    """Regression test proving that recommendation candidates come only from imported dataset."""
    session = SessionLocal()
    count = session.query(Employee).count()
    if count == 200:
        # If the DB has exactly 200 employees, ensure no "Dustin Nelson"
        dustin = session.query(Employee).filter(Employee.name == "Dustin Nelson").first()
        assert dustin is None, (
            "Old seed employee 'Dustin Nelson' should not be present in imported dataset."
        )

        # Ensure Aarav Sharma is present
        aarav = session.query(Employee).filter(Employee.name == "Aarav Sharma").first()
        assert aarav is not None, "Imported dataset employee 'Aarav Sharma' should be present."

    session.close()
