#!/usr/bin/env python3
"""Small file-based coordinator for a free-first multi-agent coding workflow."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASK = ROOT / "tasks" / "current-task.md"
REPORTS = ROOT / "reports"
DECISIONS = ROOT / "decisions" / "decision-log.md"

ROLES = {
    "planner": "You are the read-only Planner. Inspect the task and relevant code. Do not edit files. Return observed facts, uncertainties, a minimal plan, acceptance criteria, risks, and exact validation commands.",
    "implementer": "You are the sole Implementer for this pass. Read AGENTS.md and the task. Make the smallest safe change, add regression tests, run relevant checks, and report exact files/commands/results. Do not deploy or run remote migrations.",
    "reviewer": "You are a read-only Reviewer. Do not edit files. Inspect the task and git diff. Look for correctness bugs, security issues, missing tests, and scope creep. Return findings by severity with file/line evidence.",
    "security": "You are a read-only Security Reviewer. Do not edit files or execute destructive commands. Check authentication/authorization, secret exposure, injection, unsafe shell use, dependencies, data handling, and weakened safeguards. Cite concrete evidence.",
}

def read_task():
    return TASK.read_text(encoding="utf-8") if TASK.exists() else "(No task file yet. Create one with new-task.)"

def cmd_status(_args):
    print(f"Project: {ROOT.name}")
    print(f"Task file: {'present' if TASK.exists() else 'missing'}")
    print(f"Current task: {TASK}")
    print("Reports:")
    if REPORTS.exists():
        found = sorted(p.name for p in REPORTS.iterdir() if p.is_file())
        print("\n".join(f"  - {name}" for name in found) if found else "  (none)")
    else:
        print("  (none)")
    print("Coordinator mode: file-based; no API calls or agent subprocesses.")

def cmd_new_task(args):
    TASK.parent.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    DECISIONS.parent.mkdir(parents=True, exist_ok=True)
    if TASK.exists() and not args.overwrite:
        raise SystemExit("tasks/current-task.md already exists; pass --overwrite to replace it.")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    TASK.write_text(
        f"# Current Task\n\n- Created: {now}\n- Status: proposed\n- Scope: {args.title}\n\n"
        "## Problem / expected behavior\nDescribe the observed problem and desired behavior.\n\n"
        "## Constraints\n- Minimal patch\n- No production deploys or remote migrations\n- No secrets in prompts or reports\n\n"
        "## Acceptance criteria\n- [ ] Reproduction or clear reasoned test\n- [ ] Regression test where applicable\n"
        "- [ ] Relevant checks run and results recorded\n- [ ] Diff reviewed by a separate read-only reviewer\n",
        encoding="utf-8")
    print(f"Created {TASK.relative_to(ROOT)}")

def cmd_prompt(args):
    task = read_task()
    print("# AI Dev Team — " + args.role.title() + " brief\n\nRead AGENTS.md first. Shared task:\n\n" + task + "\n## Role-specific instructions\n" + ROLES[args.role] + "\n\n## Output contract\n- Separate observed facts, assumptions, and recommendations.\n- Reference file paths and line numbers where possible.\n- Never claim to have run checks you did not execute.\n- Respect repository security boundaries.")

def cmd_init(_args):
    for name in ("tasks", "reports", "decisions"):
        (ROOT / name).mkdir(parents=True, exist_ok=True)
    if not DECISIONS.exists():
        DECISIONS.write_text("# Decision Log\n\nAppend dated decisions, evidence, alternatives, and owner approval.\n", encoding="utf-8")
    print("Workspace directories are ready.")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(required=True)
    p = sub.add_parser("init", help="create workspace directories")
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("status", help="show task/report status")
    p.set_defaults(func=cmd_status)
    p = sub.add_parser("new-task", help="create a task template")
    p.add_argument("title")
    p.add_argument("--overwrite", action="store_true")
    p.set_defaults(func=cmd_new_task)
    p = sub.add_parser("prompt", help="print a copyable prompt for an agent role")
    p.add_argument("--role", choices=sorted(ROLES), required=True)
    p.set_defaults(func=cmd_prompt)
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
