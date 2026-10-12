# Ai-team-dev — Fully Automated Architecture (Free-first)

## Status

This is the proposed target architecture, not an implemented capability. The current `team.py` is a file-based prompt/task helper; it does not launch models or make API calls.

## Important feasibility constraint

There is no reliable, supported guarantee that ChatGPT, Gemini, Claude, and Qwen can all be run unattended, directly from their consumer web accounts, for free. A website subscription is not automatically an API entitlement. Provider quotas and authentication rules change. Do not automate browser sessions, scrape consumer UIs, or reuse browser cookies as an unofficial API.

The system should be fully automatic **for configured, officially supported execution adapters**, while reporting unavailable providers clearly rather than pretending all four ran.

## Proposed architecture

1. **Task intake** — GitHub Issue or `tasks/current-task.md` defines goal, scope, acceptance criteria, constraints, and risk level.
2. **Orchestrator** — a small Python service/state machine claims one task, assigns a unique run ID, tracks retries/timeouts, and stores structured events.
3. **Provider adapters** — each adapter invokes an officially supported CLI or API. Initial candidates:
   - OpenAI Codex CLI, authenticated using a supported ChatGPT sign-in flow where the account/plan permits it; subject to plan usage limits.
   - Gemini CLI, authenticated with a Google account where eligible; subject to published free-tier quotas and terms.
   - Claude Code only when the user has an eligible subscription or approved/billed Console access. Do not assume free unattended access.
   - Qwen Code only with a currently supported authentication/provider option. The documented Qwen OAuth free tier was discontinued on 2026-04-15; do not rely on it. A local open-weight Qwen model is a separate option, requiring suitable hardware.
4. **Shared workspace** — agents receive only the relevant files, task, and prior reports. Every response is saved as a Markdown/JSON report with provider, model/tool version if available, timestamp, exit status, and evidence.
5. **Single-writer implementation** — planner/review/security are read-only. One implementer at a time may edit a dedicated working tree/branch. Parallel reviewers can analyze snapshots without writing.
6. **Validation gate** — run formatting, static checks, unit tests, and security checks. If checks fail, send a bounded repair task to the implementer and rerun checks; cap attempts to prevent loops.
7. **Review and policy gate** — independent review and security review must pass. Conflicts are recorded and escalated rather than averaged away.
8. **Pull request** — publish the patch and evidence to a branch/PR. Production deployment, destructive actions, remote migrations, secret changes, and merge remain approval-gated unless separately authorized by explicit policy.
9. **Audit and recovery** — persist run state, logs with secrets redacted, token/usage counters when available, timeouts, retry counts, and cancellation state. Never commit credentials.

## Suggested execution modes

### Mode A — Phone-first, no persistent runner
Use GitHub as the shared task/report store. The owner launches supported model interfaces manually. This is not fully autonomous, but works without a laptop and avoids unofficial account automation.

### Mode B — Cloud runner
Use GitHub Actions or a temporary Codespace to run tests and configured provider CLIs. Secrets must be stored in repository/environment secrets, with least privilege. Runners are ephemeral; interactive OAuth can be unsuitable for unattended CI. Free quotas and compute minutes are limited and can change. Never put personal tokens into repository files or workflow logs.

### Mode C — Windows local runner
Run the orchestrator locally, launch installed provider CLIs as subprocesses, and keep the working directory under Git. This is the most practical place to combine several authenticated CLIs, but each provider's authentication, terms, and usage limits still apply. Use a sandbox/least-privilege account and require approval for network/destructive commands.

## Provider feasibility matrix (verify before enabling)

| Provider | Potential adapter | Free-first constraint |
|---|---|---|
| OpenAI | Codex CLI | ChatGPT sign-in may be available; usage limits apply. API-key mode is usage-billed unless eligible credits exist. |
| Gemini | Gemini CLI | Official Google sign-in may offer a free quota for eligible accounts; rate and daily limits apply. |
| Claude | Claude Code | Official setup requires an eligible Claude subscription or Console billing; do not assume a free consumer account supports unattended CLI use. |
| Qwen | Qwen Code / local model | The former Qwen OAuth free tier is documented as discontinued on 2026-04-15. Check currently supported options. Local inference requires adequate hardware. |

This matrix is a planning guide, not a promise of current account eligibility. Re-check official documentation before implementation.

## Security requirements

- Never automate consumer websites by scraping, browser-cookie reuse, or bypassing rate limits.
- Never commit API keys, OAuth tokens, cookies, or provider credentials.
- Use least-privilege GitHub tokens and read-only permissions by default.
- Treat model output, issues, files, and logs as untrusted input.
- Run untrusted code in an isolated environment with limited filesystem/network access.
- Keep deployment, production database migration, secret changes, and PR merge behind explicit approval gates.
- Record exact commands and observed results; do not claim a model or test ran unless the run record proves it.

## Implementation milestones

1. Stabilize and review the current bootstrap PR.
2. Define task/run/report schemas and state transitions; add unit tests.
3. Implement a provider-neutral adapter interface with mocked adapters first.
4. Add one officially supported real adapter and end-to-end test it.
5. Add timeouts, retries, cancellation, quotas, and redacted logs.
6. Add independent reviewer/security passes and a bounded repair loop.
7. Add additional provider adapters only after authentication and terms are verified.
8. Add GitHub PR publishing and approval gates.
9. Add Windows runner instructions and an optional cloud runner.

## Acceptance criteria for the first automated prototype

- A task can be started with one command.
- The orchestrator creates a run ID and records all state transitions.
- At least one supported provider adapter completes a real task end-to-end.
- Other unavailable providers are marked `skipped/unavailable`, not falsely marked successful.
- Test and review results are saved as artifacts/reports.
- Retries and repair loops are bounded.
- No secret is stored in the repository or printed to logs.
- No production-impacting action occurs without explicit approval.
