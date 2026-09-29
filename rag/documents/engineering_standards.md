# Engineering Standards — ProjectMind Company Documentation

## Version: 2024.1
## Classification: Internal Use Only

---

## 1. Technology Standards

### 1.1 Backend Development
- Primary language: Python 3.12+ for all new services
- Web frameworks: FastAPI (APIs), Django (full-stack), Flask (lightweight services)
- All services must expose health-check endpoints at `/health`
- Code must pass ruff linting and bandit security checks before review

### 1.2 Frontend Development
- TypeScript is required for all new frontend work
- React 18+ for component-based UIs
- Accessibility: WCAG 2.1 AA compliance required

### 1.3 Database
- PostgreSQL for production relational data
- SQLite acceptable for development and testing only
- All schema changes must go through migration scripts (Alembic)
- No direct SQL generation from user input

### 1.4 Cloud Infrastructure
- AWS is the primary cloud provider
- Azure approved for Microsoft-integrated workloads
- All infrastructure must be defined in Terraform
- No manual console deployments in production

---

## 2. Security Standards

### 2.1 Authentication & Authorization
- All services must implement role-based access control (RBAC)
- API keys must never be committed to version control
- Secrets management via environment variables or AWS Secrets Manager
- JWT tokens expire after 1 hour; refresh tokens after 7 days

### 2.2 Data Protection
- PII data must be encrypted at rest (AES-256) and in transit (TLS 1.3)
- Healthcare data must comply with HIPAA
- Financial data must comply with PCI-DSS
- GDPR compliance required for EU users

### 2.3 Code Security
- No use of `eval()`, `exec()`, or dynamic code execution
- No shell command injection: avoid `subprocess` with `shell=True`
- Dependency audits required before each release
- Security scans: bandit + pip-audit in CI pipeline

---

## 3. Role Guidelines

### 3.1 Software Engineer
- Responsible for feature implementation, code review, and testing
- Expected to write unit tests with >80% coverage
- Required to participate in architecture reviews

### 3.2 Senior Software Engineer
- All of Software Engineer responsibilities plus
- Leads technical design for features
- Mentors junior team members
- Contributes to engineering standards

### 3.3 Engineering Lead / Tech Lead
- Sets technical direction for a team
- Owns the team's architecture decisions
- Partners with Product Manager on roadmap

### 3.4 Solutions Architect
- Responsible for cross-system design
- Produces Architecture Decision Records (ADRs)
- Validates designs for security, scalability, cost

### 3.5 Principal / Staff Engineer
- Company-wide technical influence
- Owns critical engineering decisions
- Drives engineering culture

---

## 4. Project Process Standards

### 4.1 Project Phases
1. Discovery & Requirements
2. Architecture Design
3. Development Sprints (2-week cycles)
4. Testing & QA
5. Deployment & Monitoring
6. Retrospective

### 4.2 Team Composition Guidelines
- Projects under 4 weeks: minimum 2 engineers
- Projects 4-12 weeks: minimum 3 engineers, 1 senior
- Projects 12+ weeks: minimum 5 engineers, 1 lead, 1 architect
- All teams must have at least one security-aware engineer

### 4.3 Definition of Done
- All tests pass
- Code review approved by senior engineer
- Security scan passed
- Documentation updated
- Deployed to staging and verified

---

## 5. Technology Selection Guidelines

### 5.1 Database Selection
| Use Case | Recommended |
|---|---|
| Relational data, ACID required | PostgreSQL |
| Document store | MongoDB |
| Time series | InfluxDB |
| Cache | Redis |
| Search | Elasticsearch |

### 5.2 Messaging
| Use Case | Recommended |
|---|---|
| Event streaming | Apache Kafka |
| Task queue | Celery + Redis |
| Simple pub/sub | AWS SNS/SQS |

---

## 6. ML / AI Project Guidelines

### 6.1 Team Requirements for ML Projects
- At least one ML Engineer (Senior level recommended)
- A Data Engineer for pipeline work
- Domain expert participation required for industry-specific ML

### 6.2 Model Governance
- All models must have documented training data provenance
- Model drift monitoring required in production
- Explainability documentation required for high-stakes decisions

### 6.3 LLM Usage
- LLM outputs must be validated before use
- LLM must never directly modify production databases
- Prompts must include anti-injection guardrails
- All LLM evidence must be clearly labeled as inference
