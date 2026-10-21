# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Proactive & Continuous Evolution of the `.agents/` Workspace

> **CORE GOVERNANCE DIRECTIVE:**
> AI agents and developers MUST autonomously improve, update, and expand `.agents/` whenever an optimization, unhandled edge case, automation opportunity, or architectural drift is identified. Never wait for user prompting.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. Triggers for Autonomous `.agents/` Improvement

Execute immediate updates to `.agents/` upon detecting any of the following:

1. **Bug Resolution & Defect Retrospectives:**
   - Whenever fixing a defect (e.g. schema drift, SSRF bypass, CSS geometry overlap, uncaught error status), check if existing directives or skills could have prevented it.
   - Update the relevant directive in `.agents/rules/` or playbook in `.agents/skills/` with the exact pattern and preventive invariants.

2. **Repetitive Procedure Automation:**
   - Any manual or multi-step validation procedure (e.g. ORM parity checks, contract verifications, linter runs, container inspection) susceptible to automation MUST be codified as an executable script in `.agents/scripts/`.
   - Scripts MUST adhere to Rule Zero (executing inside Docker, not on the host Ubuntu) and pass ShellCheck without warnings.

3. **Domain & API Surface Expansion:**
   - When new endpoints, MCP tools, RouterOS v7 features, or database models are added, immediately update the corresponding skill in `.agents/skills/` (e.g. `rosgrid-noc-operator`, `mikrotik-webfig-safemode`).
   - If a new architectural domain emerges, create a new specialized skill with `SKILL.md` following standard frontmatter conventions.

4. **Token Efficiency & Density Optimization:**
   - Continuously refactor `.agents/rules/` and `.agents/skills/` to eliminate redundancy, enhance token density, and maintain concise, unambiguous technical English (~35% context savings) while guaranteeing Spanish for all user interactions.

5. **Multi-Agent Tooling & Config Maintenance:**
   - Keep integration configs for external agents (`claude_desktop.json`, `hermes_agent.yaml`) in sync whenever MCP tools or server arguments change.

---

## 2. Evolution Workflow & Validation Gate

When updating `.agents/`:

1. Apply changes directly to `rules/`, `skills/`, or `scripts/`.
2. If adding a new script, ensure `chmod +x` and verify with ShellCheck.
3. Keep [AGENTS.md](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/AGENTS.md) and [.agents/README.md](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/.agents/README.md) synchronized with any new rules or skills.
4. Run `./.agents/scripts/certify_task_completion.sh` to certify the workspace before completing the task.
