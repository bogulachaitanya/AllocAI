from config.settings import get_settings
from hindsight.adapter import get_hindsight_adapter

settings = get_settings()
print(f"HINDSIGHT_ADAPTER: {settings.hindsight_adapter}")
print(f"HINDSIGHT_DB_PATH: {settings.hindsight_db_path}")

adapter = get_hindsight_adapter()
count = adapter.count()
print(f"Total Memories: {count}")

mems = adapter.list_all(limit=3)
for m in mems:
    emp = m.metadata.get("employee_id")
    proj = m.metadata.get("project_id")
    print(f"Memory: {m.memory_id} | Type: {m.memory_type} | Emp: {emp} | Proj: {proj}")
    print(f"  Content: {m.content}")
    print(f"  Learning: {m.summary}")

from hindsight.models import MemoryType, RecallRequest

req = RecallRequest(
    query="fintech Python",
    domain="fintech",
    memory_types=[
        MemoryType.TEAM_PATTERN,
        MemoryType.LESSON_LEARNED,
        MemoryType.PROJECT_OUTCOME,
        MemoryType.COLLABORATION_PATTERN,
        MemoryType.TECH_TRANSITION,
    ],
    top_k=5,
)
results = adapter.recall(req)
print(f"Recall for 'fintech Python' returned {len(results)} results")
