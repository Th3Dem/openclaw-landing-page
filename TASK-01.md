Paula (pm_bot), init project: Landing Page presenting AI dev team & services.

REQUIREMENTS:
- Scope: High-converting, static info landing page. NO interactive buttons, forms, or clickable CTAs.
- Architecture: Single-page app / static HTML rendered via FastAPI (py_bot).
- Content Sections:
  1. Hero: Human + AI engineering synergy. 1 dev + 5 AI bots = studio-grade output. Key metrics (10x velocity, 100% QA, 0 bad commits).
  2. Workflow (Automated Flow): Diagram/desc: User -> pm_bot (Task) -> dev_bot/py_bot (Code+Tests) -> qa_bot (Audit) -> git_bot (PR/Release).
  3. Team Roster: Roles & skills for pm_bot, dev_bot (Go), py_bot (Python), qa_bot (Security/QA), git_bot (Release).
  4. Capabilities: High-load Go backends, FastAPI microservices, Telegram bots, Docker/SSH automation, CI/CD pipelines.
  5. Analytics & Trust: AI vs Classic dev matrix (speed, test coverage, security).

ROLES & DEPLOYMENT:
- py_bot: Build FastAPI app serving HTML/CSS/JS, write pytest suite (>=80% coverage), create Dockerfile, deploy to local dev-stage container via Docker API/SSH. Produce DEV_HANDOVER.md.
- qa_bot: Audit code & Dockerfile (bandit, pip-audit, security scan). Verify pytests. Issue APPROVED/REJECTED.
- git_bot: On QA approval, branch feat/task-01-landing-page, commit, push, create GitHub PR.

Prepare TASK-01.md and trigger py_bot.
