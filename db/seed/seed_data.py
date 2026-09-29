"""Seed data for ProjectMind development environment.

ALL employees are FICTIONAL. No real personal information is used.
Uses Faker with a fixed seed for reproducibility.
"""

from __future__ import annotations

import json
import logging
import random

from faker import Faker

from config.settings import get_settings
from db.session import get_db
from models.assignment import Assignment
from models.employee import Certification, Employee, EmployeeSkill, Skill
from models.outcome import ProjectOutcome
from models.project import Project, ProjectRequiredSkill

logger = logging.getLogger(__name__)

# Fixed seed for reproducibility
_FAKER = Faker()
Faker.seed(42)
random.seed(42)

# ── Skill catalog ────────────────────────────────────────────────────────────

SKILLS: list[tuple[str, str]] = [
    # Backend
    ("Python", "Backend"),
    ("Java", "Backend"),
    ("Go", "Backend"),
    ("Node.js", "Backend"),
    ("Django", "Backend"),
    ("FastAPI", "Backend"),
    ("Spring Boot", "Backend"),
    ("REST API Design", "Backend"),
    ("GraphQL", "Backend"),
    ("Microservices", "Backend"),
    # Frontend
    ("React", "Frontend"),
    ("Vue.js", "Frontend"),
    ("Angular", "Frontend"),
    ("TypeScript", "Frontend"),
    ("CSS / SCSS", "Frontend"),
    ("Next.js", "Frontend"),
    # Data / ML
    ("Machine Learning", "AI/ML"),
    ("Deep Learning", "AI/ML"),
    ("PyTorch", "AI/ML"),
    ("TensorFlow", "AI/ML"),
    ("Scikit-learn", "AI/ML"),
    ("Data Engineering", "Data"),
    ("Apache Spark", "Data"),
    ("Kafka", "Data"),
    ("SQL", "Data"),
    ("PostgreSQL", "Data"),
    ("MongoDB", "Data"),
    ("dbt", "Data"),
    # Cloud / DevOps
    ("AWS", "Cloud"),
    ("Azure", "Cloud"),
    ("GCP", "Cloud"),
    ("Terraform", "DevOps"),
    ("Docker", "DevOps"),
    ("Kubernetes", "DevOps"),
    ("CI/CD", "DevOps"),
    ("Linux Administration", "DevOps"),
    # Security
    ("Cybersecurity", "Security"),
    ("Penetration Testing", "Security"),
    ("SIEM", "Security"),
    ("Zero Trust Architecture", "Security"),
    # Domain
    ("Fintech Compliance", "Domain"),
    ("Healthcare HL7/FHIR", "Domain"),
    ("ERP Systems", "Domain"),
    ("Payment Processing", "Domain"),
    # Soft skills / management
    ("Agile / Scrum", "Process"),
    ("Technical Leadership", "Leadership"),
    ("Stakeholder Management", "Leadership"),
    ("System Design", "Architecture"),
    ("Solution Architecture", "Architecture"),
    ("API Gateway Design", "Architecture"),
]

CERTIFICATIONS: list[tuple[str, str]] = [
    ("AWS Certified Solutions Architect", "Amazon"),
    ("AWS Certified Developer", "Amazon"),
    ("Azure Solutions Architect Expert", "Microsoft"),
    ("Google Professional Cloud Architect", "Google"),
    ("Certified Kubernetes Administrator (CKA)", "CNCF"),
    ("PMP - Project Management Professional", "PMI"),
    ("Certified ScrumMaster (CSM)", "Scrum Alliance"),
    ("CISSP", "ISC2"),
    ("CompTIA Security+", "CompTIA"),
    ("Google Professional Data Engineer", "Google"),
    ("Databricks Certified Associate Developer", "Databricks"),
    ("TensorFlow Developer Certificate", "Google"),
]

DEPARTMENTS: list[str] = [
    "Engineering",
    "Data & Analytics",
    "AI / Machine Learning",
    "DevOps & Infrastructure",
    "Security",
    "Product",
    "Architecture",
]

SENIORITY_LEVELS: list[tuple[str, float, float]] = [
    # (level, min_years, max_years)
    ("junior", 0.5, 2.5),
    ("mid", 2.0, 5.0),
    ("senior", 4.0, 9.0),
    ("lead", 7.0, 14.0),
    ("principal", 10.0, 20.0),
    ("staff", 12.0, 22.0),
]

DOMAINS: list[str] = [
    "fintech",
    "healthcare",
    "e-commerce",
    "cloud",
    "ml",
    "saas",
    "cybersecurity",
    "logistics",
    "general",
]

SAMPLE_PROJECTS: list[dict] = [
    {
        "title": "Real-Time Fraud Detection Platform",
        "domain": "fintech",
        "description": "Build an ML-powered system to detect payment fraud in real time.",
        "status": "completed",
        "client": "Meridian Financial",
        "duration_weeks": 16,
        "required_skills": ["Python", "Machine Learning", "Kafka", "PostgreSQL", "AWS"],
    },
    {
        "title": "Healthcare Patient Portal",
        "domain": "healthcare",
        "description": "Develop a HIPAA-compliant patient portal with appointment scheduling.",
        "status": "completed",
        "client": "CareFirst Health",
        "duration_weeks": 12,
        "required_skills": ["React", "Django", "PostgreSQL", "Healthcare HL7/FHIR"],
    },
    {
        "title": "E-Commerce Recommendation Engine",
        "domain": "e-commerce",
        "description": "Build a personalized product recommendation engine.",
        "status": "active",
        "client": "ShopNova",
        "duration_weeks": 20,
        "required_skills": ["Python", "Machine Learning", "Scikit-learn", "MongoDB"],
    },
    {
        "title": "Cloud Migration — Legacy ERP",
        "domain": "cloud",
        "description": "Migrate on-premise ERP system to Azure cloud.",
        "status": "completed",
        "client": "GlobalMfg Corp",
        "duration_weeks": 24,
        "required_skills": ["Azure", "Terraform", "Docker", "ERP Systems"],
    },
    {
        "title": "Zero Trust Security Implementation",
        "domain": "cybersecurity",
        "description": "Design and implement zero trust network architecture.",
        "status": "completed",
        "client": "TechShield Inc",
        "duration_weeks": 10,
        "required_skills": ["Zero Trust Architecture", "Cybersecurity", "Azure"],
    },
]

SAMPLE_HINDSIGHT_MEMORIES: list[dict] = [
    {
        "content": (
            "A fintech fraud detection project that included a domain expert in payment "
            "processing alongside ML engineers delivered 40% better fraud catch rate. "
            "Pure ML teams without domain knowledge struggled with false positives."
        ),
        "summary": "Domain expertise + ML expertise outperforms pure ML teams in fintech",
        "memory_type": "team_pattern",
        "domain": "fintech",
        "tags": ["fintech", "ml", "team_composition"],
    },
    {
        "content": (
            "Healthcare projects consistently require a dedicated HIPAA compliance lead. "
            "Projects that skipped this role experienced scope creep and regulatory delays "
            "averaging 3 additional weeks."
        ),
        "summary": "Healthcare projects require a dedicated compliance role to avoid delays",
        "memory_type": "lesson_learned",
        "domain": "healthcare",
        "tags": ["healthcare", "compliance", "risk"],
    },
    {
        "content": (
            "Cloud migration projects are most successful when a solutions architect is "
            "involved from week 1. Teams that added architecture expertise mid-project "
            "experienced significant rework."
        ),
        "summary": "Early architecture involvement critical for cloud migration success",
        "memory_type": "lesson_learned",
        "domain": "cloud",
        "tags": ["cloud", "architecture", "migration"],
    },
    {
        "content": (
            "Teams where senior and junior engineers were paired (1:1 mentoring ratio) "
            "showed 25% higher code quality ratings and faster junior onboarding across "
            "multiple e-commerce platform projects."
        ),
        "summary": "Senior-junior pairing improves code quality in e-commerce projects",
        "memory_type": "collaboration_pattern",
        "domain": "e-commerce",
        "tags": ["mentoring", "quality", "collaboration"],
    },
    {
        "content": (
            "Security implementation projects consistently overrun when team members lack "
            "hands-on penetration testing experience. Certification alone (CISSP) was not "
            "sufficient without practical experience."
        ),
        "summary": "Security projects need hands-on pentest experience, not just certifications",
        "memory_type": "risk_pattern",
        "domain": "cybersecurity",
        "tags": ["security", "risk", "experience"],
    },
]


def seed_database() -> None:
    """Seed the database with fictional employees and sample projects."""
    with get_db() as session:
        # Check if already seeded
        count = session.query(Employee).count()
        if count > 0:
            logger.info("Database already seeded (%d employees). Skipping.", count)
            return

        settings = get_settings()
        target_count = settings.seed_employee_count

        logger.info("Seeding database with %d fictional employees...", target_count)

        # ── Create skills ─────────────────────────────────────────────────
        skill_objects: dict[str, Skill] = {}
        for skill_name, category in SKILLS:
            skill = Skill(name=skill_name, category=category)
            session.add(skill)
            skill_objects[skill_name] = skill
        session.flush()

        # ── Create employees ──────────────────────────────────────────────
        employees: list[Employee] = []
        used_emails: set[str] = set()

        # Distribute seniority realistically
        seniority_distribution = [
            ("junior", 0.20),
            ("mid", 0.30),
            ("senior", 0.30),
            ("lead", 0.12),
            ("principal", 0.05),
            ("staff", 0.03),
        ]

        seniority_pool: list[str] = []
        for level, ratio in seniority_distribution:
            count = max(1, int(target_count * ratio))
            seniority_pool.extend([level] * count)
        random.shuffle(seniority_pool)
        seniority_pool = (seniority_pool * (target_count // len(seniority_pool) + 1))[:target_count]

        for i in range(target_count):
            level = seniority_pool[i]
            level_data = next(d for d in SENIORITY_LEVELS if d[0] == level)
            _, min_yr, max_yr = level_data

            years_exp = round(random.uniform(min_yr, max_yr), 1)

            # Generate unique email
            for _ in range(10):
                email = _FAKER.email()
                if email not in used_emails:
                    used_emails.add(email)
                    break

            dept = random.choice(DEPARTMENTS)
            domain_count = random.randint(1, 3)
            emp_domains = ", ".join(random.sample(DOMAINS, domain_count))

            emp = Employee(
                name=_FAKER.name(),
                email=email,
                role=_generate_role(dept, level),
                department=dept,
                seniority=level,
                years_of_experience=years_exp,
                domain_expertise=emp_domains,
                is_available=random.random() > 0.15,  # 85% available
                availability_percentage=random.choice([25, 50, 75, 100, 100, 100]),
                performance_rating=round(random.gauss(3.6, 0.5), 1),
                work_preferences=random.choice(["remote", "hybrid", "on-site", "remote,agile"]),
                location=_FAKER.city(),
                timezone=random.choice(
                    ["UTC", "US/Eastern", "US/Pacific", "Europe/London", "Asia/Kolkata"]
                ),
            )
            # Clamp performance rating
            if emp.performance_rating:
                emp.performance_rating = max(1.0, min(5.0, emp.performance_rating))
            session.add(emp)
            employees.append(emp)

        session.flush()

        # ── Assign skills to employees ────────────────────────────────────
        all_skill_names = list(skill_objects.keys())
        for emp in employees:
            # Number of skills based on seniority
            skill_count_map = {
                "junior": (2, 5),
                "mid": (4, 8),
                "senior": (5, 10),
                "lead": (6, 12),
                "principal": (7, 14),
                "staff": (8, 15),
            }
            min_s, max_s = skill_count_map.get(emp.seniority, (3, 7))
            n_skills = random.randint(min_s, max_s)
            chosen_skills = random.sample(all_skill_names, min(n_skills, len(all_skill_names)))

            for skill_name in chosen_skills:
                proficiency = _proficiency_for_seniority(emp.seniority)
                years_with = round(random.uniform(0.5, emp.years_of_experience), 1)
                es = EmployeeSkill(
                    employee_id=emp.id,
                    skill_id=skill_objects[skill_name].id,
                    proficiency=proficiency,
                    years_with_skill=years_with,
                )
                session.add(es)

        session.flush()

        # ── Assign certifications ─────────────────────────────────────────
        for emp in employees:
            if emp.seniority in ("senior", "lead", "principal", "staff"):
                n_certs = random.randint(0, 2)
            else:
                n_certs = random.randint(0, 1)
            for _ in range(n_certs):
                cert_name, issuer = random.choice(CERTIFICATIONS)
                cert = Certification(
                    employee_id=emp.id,
                    name=cert_name,
                    issuer=issuer,
                    issued_year=random.randint(2018, 2024),
                    expires_year=random.choice([None, None, 2026, 2027, 2028]),
                )
                session.add(cert)

        session.flush()

        # ── Create sample projects with assignments ────────────────────────
        project_objects: list[Project] = []
        for proj_data in SAMPLE_PROJECTS:
            proj = Project(
                title=proj_data["title"],
                description=proj_data["description"],
                client=proj_data.get("client", ""),
                domain=proj_data["domain"],
                status=proj_data["status"],
                duration_weeks=proj_data.get("duration_weeks"),
                team_size_min=3,
                team_size_max=6,
            )
            session.add(proj)
            project_objects.append(proj)

        session.flush()

        # Assign required skills to projects
        for proj, proj_data in zip(project_objects, SAMPLE_PROJECTS, strict=False):
            for skill_name in proj_data.get("required_skills", []):
                if skill_name in skill_objects:
                    prs = ProjectRequiredSkill(
                        project_id=proj.id,
                        skill_id=skill_objects[skill_name].id,
                        minimum_proficiency=3,
                        is_mandatory=True,
                    )
                    session.add(prs)

        session.flush()

        # Create assignments for completed projects
        available_employees = [e for e in employees if e.is_available]
        for proj, proj_data in zip(project_objects, SAMPLE_PROJECTS, strict=False):
            if proj_data["status"] in ("completed", "active"):
                team_size = random.randint(3, 5)
                team = random.sample(available_employees[:50], min(team_size, 50))
                collab_ids = [str(e.id) for e in team]

                for emp in team:
                    assignment = Assignment(
                        employee_id=emp.id,
                        project_id=proj.id,
                        role_on_project=emp.role,
                        allocation_percentage=random.choice([50, 75, 100]),
                        status="completed" if proj_data["status"] == "completed" else "active",
                        individual_performance_rating=round(random.gauss(3.8, 0.4), 1),
                        collaborated_with=json.dumps(
                            [int(i) for i in collab_ids if int(i) != emp.id]
                        ),
                    )
                    if assignment.individual_performance_rating:
                        assignment.individual_performance_rating = max(
                            1.0, min(5.0, assignment.individual_performance_rating)
                        )
                    session.add(assignment)

        session.flush()

        # Create outcomes for completed projects
        for proj, proj_data in zip(project_objects, SAMPLE_PROJECTS, strict=False):
            if proj_data["status"] == "completed":
                outcome = ProjectOutcome(
                    project_id=proj.id,
                    outcome_status="success",
                    delivered_on_time=random.choice([True, True, False]),
                    delivered_on_budget=random.choice([True, True, False]),
                    quality_rating=round(random.gauss(4.0, 0.4), 1),
                    client_feedback="The team delivered excellent results and exceeded our expectations.",
                    manager_feedback="Strong collaboration and technical execution throughout.",
                    observations="Team communicated well. Would work together again.",
                    extracted_lessons=json.dumps(
                        [
                            "Early domain expert involvement critical",
                            "Regular stakeholder check-ins improved alignment",
                        ]
                    ),
                    retained_memory_ids="[]",
                )
                if outcome.quality_rating:
                    outcome.quality_rating = max(1.0, min(5.0, outcome.quality_rating))
                session.add(outcome)

        session.flush()

        # ── Seed Hindsight memories ───────────────────────────────────────
        _seed_hindsight_memories()

        logger.info(
            "Seed complete: %d employees, %d projects created.",
            len(employees),
            len(project_objects),
        )


def _seed_hindsight_memories() -> None:
    """Pre-populate Hindsight with organizational memory examples."""
    from hindsight.adapter import get_hindsight_adapter
    from hindsight.models import MemoryType, RetainRequest

    adapter = get_hindsight_adapter()

    if adapter.count() > 0:
        logger.info("Hindsight already has memories. Skipping Hindsight seed.")
        return

    for mem_data in SAMPLE_HINDSIGHT_MEMORIES:
        adapter.retain(
            RetainRequest(
                content=mem_data["content"],
                summary=mem_data["summary"],
                memory_type=MemoryType(mem_data["memory_type"]),
                domain=mem_data.get("domain", "general"),
                tags=mem_data.get("tags", []),
            )
        )

    logger.info("Seeded %d Hindsight memories.", len(SAMPLE_HINDSIGHT_MEMORIES))


def _generate_role(department: str, seniority: str) -> str:
    role_map: dict[str, dict[str, str]] = {
        "Engineering": {
            "junior": "Junior Software Engineer",
            "mid": "Software Engineer",
            "senior": "Senior Software Engineer",
            "lead": "Engineering Lead",
            "principal": "Principal Engineer",
            "staff": "Staff Engineer",
        },
        "Data & Analytics": {
            "junior": "Junior Data Analyst",
            "mid": "Data Engineer",
            "senior": "Senior Data Engineer",
            "lead": "Data Engineering Lead",
            "principal": "Principal Data Engineer",
            "staff": "Staff Data Engineer",
        },
        "AI / Machine Learning": {
            "junior": "ML Engineer (Junior)",
            "mid": "ML Engineer",
            "senior": "Senior ML Engineer",
            "lead": "ML Tech Lead",
            "principal": "Principal ML Scientist",
            "staff": "Staff ML Engineer",
        },
        "DevOps & Infrastructure": {
            "junior": "Junior DevOps Engineer",
            "mid": "DevOps Engineer",
            "senior": "Senior DevOps Engineer",
            "lead": "DevOps Lead",
            "principal": "Principal Infrastructure Architect",
            "staff": "Staff Platform Engineer",
        },
        "Security": {
            "junior": "Security Analyst (Junior)",
            "mid": "Security Engineer",
            "senior": "Senior Security Engineer",
            "lead": "Security Lead",
            "principal": "Principal Security Architect",
            "staff": "Staff Security Engineer",
        },
        "Product": {
            "junior": "Associate Product Manager",
            "mid": "Product Manager",
            "senior": "Senior Product Manager",
            "lead": "Group Product Manager",
            "principal": "Principal Product Manager",
            "staff": "Staff Product Manager",
        },
        "Architecture": {
            "junior": "Junior Solutions Architect",
            "mid": "Solutions Architect",
            "senior": "Senior Solutions Architect",
            "lead": "Architecture Lead",
            "principal": "Principal Architect",
            "staff": "Distinguished Architect",
        },
    }
    return role_map.get(department, {}).get(seniority, f"{seniority.title()} Engineer")


def _proficiency_for_seniority(seniority: str) -> int:
    mapping = {
        "junior": random.choice([1, 2, 2]),
        "mid": random.choice([2, 3, 3]),
        "senior": random.choice([3, 4, 4]),
        "lead": random.choice([3, 4, 5]),
        "principal": random.choice([4, 5, 5]),
        "staff": random.choice([4, 5, 5]),
    }
    return mapping.get(seniority, 3)
