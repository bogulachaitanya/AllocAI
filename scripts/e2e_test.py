"""E2E test for AI Banking Assistant — Python/NLP/FastAPI/SQL/AWS recommendation."""

from db.session import SessionLocal
from hindsight.adapter import get_hindsight_adapter
from schemas.project import StructuredRequirements
from services.recommendation_engine import RecommendationEngine

session = SessionLocal()
adapter = get_hindsight_adapter()
print(f"Stored Memories: {adapter.count()}")

req = StructuredRequirements(
    title="AI Banking Assistant",
    domain="fintech",
    required_skills=["Python", "NLP", "FastAPI", "SQL", "AWS"],
    preferred_skills=[],
    team_size_min=3,
    team_size_max=5,
    duration_weeks=16,
    key_responsibilities=[],
    risks=[],
)

engine = RecommendationEngine(session=session, hindsight=adapter)

# Before
rec_before = engine.recommend_without_hindsight(requirements=req)
print("\n--- BEFORE HINDSIGHT ---")
print(f"Team size: {len(rec_before.recommended_team)}")
print(f"Skill Coverage: {rec_before.skill_coverage}%")
for m in rec_before.recommended_team:
    current = ", ".join(m.skill_detail.matched_skills) or "None"
    historical = ", ".join(m.skill_detail.historical_matched) or "None"
    effective = ", ".join(m.effective_skill_coverage) or "None"
    print(f"  {m.employee_name} ({m.employee_role}): score={m.project_fit_score}")
    print(f"    Current skills matched: {current}")
    print(f"    Historical skills matched: {historical}")
    print(f"    Effective coverage: {effective}")

# After
rec_after = engine.recommend(requirements=req)
print("\n--- WITH HINDSIGHT ---")
print(f"Team size: {len(rec_after.recommended_team)}")
print(f"Skill Coverage: {rec_after.skill_coverage}%")
print(f"Hindsight Memories Found: {rec_after.hindsight_memories_found}")
for m in rec_after.recommended_team:
    current = ", ".join(m.skill_detail.matched_skills) or "None"
    historical = ", ".join(m.skill_detail.historical_matched) or "None"
    print(f"  {m.employee_name} ({m.employee_role}): score={m.project_fit_score}")
    print(f"    Current skills matched: {current}")
    print(f"    Historical skills matched: {historical}")

# Hindsight Evidence
hindsight_ev = [e for e in rec_after.evidence if e.source.value == "hindsight"]
print(f"\nHindsight Evidence items ({len(hindsight_ev)}):")
for ev in hindsight_ev[:5]:
    print(f"  [{ev.source}] {ev.title}: {ev.statement[:100]}")

session.close()
