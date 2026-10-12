# OpenClaw + Hermes Integration Plan for Ai-team-dev

## Status and scope

Design only. This document does not install either runtime, add credentials, execute models, deploy services, or change the existing coordinator. The current `team.py` remains a file-based prompt helper until implementation work is approved and tested.

## Recommendation

Keep **Ai-team-dev as the source of truth and task orchestrator**. Integrate external runtimes behind optional adapters rather than replacing the existing workflow or allowing two independent orchestrators to compete.

- **OpenClaw:** optional user-facing gateway for messaging and task intake. Treat it as an interface/dispatch layer, not the authority for repository permissions or release approval.
- **Hermes Agent:** optional worker runtime for model/tool execution. It can connect to supported providers, including local Ollama-compatible endpoints, but requires at least one configured inference provider.
- **Ai-team-dev:** owns task IDs, scope, role permissions, run state, reports, validation gates, and PR/merge policy.
- **GitHub:** canonical source for code, issues, branches, pull requests, and CI evidence.
- **Ollama:** optional local inference backend when suitable hardware is available. Local model inference avoids API billing but still consumes hardware, power, and time.

Do not run both OpenClaw and Hermes as competing top-level orchestrators for the same task. Start with one integration at a time.

## Proposed topology

```text
GitHub Issue / task file
          |
          v
Ai-team-dev orchestrator (task ID, policy, run state)
          |
          +--> Planner adapter (read-only)
          |
          +--> Implementer adapter (single writer, isolated branch/worktree)
          |
          +--> Reviewer adapter (read-only snapshot)
          |
          +--> Security adapter (read-only snapshot)
          |
          v
Tests + bounded repair loop + approval gate
          |
          v
Report / Pull Request / CI evidence

Optional entry point: OpenClaw gateway -> authenticated task intake -> Ai-team-dev
Optional worker runtime: Ai-team-dev adapter -> Hermes -> approved model provider
Optional local provider: Hermes -> Ollama endpoint on a reachable host
```

The diagram describes a target design, not an existing integration.

## Responsibility boundaries

| Component | Owns | Must not own |
|---|---|---|
| Ai-team-dev | Task/run state, role policy, audit trail, retries, test gates, approval decisions | Provider credentials in Git; unbounded agent loops |
| OpenClaw | Optional chat interface, inbound message routing, user interaction | Sole authorization for repository changes; production approval by inference |
| Hermes | Optional model/tool execution and agent work | Merge/deploy authority; shared concurrent write access |
| Ollama | Optional local model serving | Workflow state or authorization |
| GitHub Actions | Deterministic CI and test execution | Unreviewed production deploys or secret rotation |

## Integration phases

### Phase 0 — no-risk baseline

1. Keep the existing feature branch and open PR unmerged.
2. Run the current Python smoke tests and inspect CI for the exact head commit.
3. Add adapter interface and schema tests without requiring a provider login.
4. Do not add secrets or enable external tool execution in CI.

### Phase 1 — provider-neutral adapter contract

Define a small interface such as:

- `capabilities()`: report supported modes and whether auth is configured; never return secret values.
- `run(task, role, workspace, timeout)`: return a structured result.
- `cancel(run_id)`: best-effort cancellation.
- `healthcheck()`: report unavailable/auth-required/ready without making a paid model request.

Every result should include run ID, adapter name/version, status (`success`, `failed`, `timeout`, `cancelled`, `skipped`), start/end time, exit code when available, report path, and redacted error summary.

Implement a deterministic mock adapter first. Tests must cover timeout, unavailable provider, malformed output, non-zero exit, cancellation, and secret redaction.

### Phase 2 — choose one execution path

Recommended order:

1. **First prototype:** mock adapter plus GitHub Actions tests. No model charges and no credentials needed.
2. **First real adapter:** choose either a supported CLI runtime or Hermes after confirming its authentication flow works in the intended runner. Do not promise fully unattended OAuth until it has been tested end-to-end.
3. **OpenClaw intake:** add only if messaging-based task submission is actually needed. Require pairing/allowlists and pass requests to Ai-team-dev's policy checks.
4. **Second runtime:** add OpenClaw or Hermes as a separate adapter only after Phase 2 has a tested rollback path.
5. **Local Ollama:** defer until a Windows machine or other suitable host is available; an iPhone is not a practical always-on local model server for this design.

### Phase 3 — safe coding workflow

1. Planner creates a plan and acceptance criteria; read-only.
2. Owner/orchestrator checks scope and risk.
3. One implementer works in an isolated branch/worktree.
4. Tests run in a restricted runner.
5. Reviewer and security reviewer inspect a read-only diff.
6. At most two automated repair attempts by default; then stop and report.
7. Open a PR with evidence. Keep merge, deploy, remote migrations, production secrets, and destructive actions approval-gated.

## Free-first reality check

- OpenClaw is open source and self-hosted; hosting and model inference are still the operator's responsibility. Its official docs state that a provider API key is needed for a typical setup, and warn that sandboxing/exec approvals are not necessarily enabled by default.
- Hermes supports multiple inference providers, including local endpoints such as Ollama. It still needs at least one configured inference provider; some provider paths are paid or subscription-based.
- Ollama with a local model can avoid per-request API billing but requires compatible hardware and is not cost-free in power, time, or maintenance.
- Free cloud quotas, OAuth eligibility, and CLI terms can change. Verify the chosen provider's current official terms before enabling it.
- Do not scrape consumer chat websites, reuse browser cookies, bypass quotas, or assume a website subscription grants API access.
- Never call an integration "free" until the exact model/provider, quota, authentication method, and hosting costs are identified.

## Security controls required before any real tool execution

- Default-deny tool policy; enable only required commands and directories.
- Separate read-only reviewer workspaces from the implementer's write workspace.
- Require explicit allowlists for network access and shell commands.
- Never expose host secrets, SSH keys, browser profiles, or unrelated files to agents.
- Store credentials only in approved secret storage or local secret stores; never in Git, task files, reports, or prompts.
- Treat repository content, issues, model output, and downloaded skills/plugins as untrusted.
- Pin versions where practical; review plugin/skill source before installation.
- Keep audit logs, redact credentials, and cap timeouts, retries, concurrency, and spend.
- Production changes, merge, deploy, remote migrations, and credential rotation require explicit owner approval.

## Acceptance criteria

- The current file-based workflow continues to work without OpenClaw, Hermes, Ollama, or provider credentials.
- Mock adapter tests pass in CI without network access or model calls.
- Missing provider/authentication is reported as `skipped` or `unavailable`, not success.
- One real provider path completes a bounded end-to-end task before a second runtime is added.
- Only one component can write to a task workspace at a time.
- Reports contain reproducible evidence and no secrets.
- Repair attempts and tool permissions are bounded.
- No merge, deploy, or production mutation occurs without explicit approval.

## Official references

- OpenClaw repository: https://github.com/openclaw/openclaw
- OpenClaw architecture/security notes: https://docs.openclaw.ai/start/why-openclaw
- Hermes Agent repository: https://github.com/NousResearch/hermes-agent
- Hermes provider documentation: https://hermes-agent.nousresearch.com/docs/integrations/providers/
- Ollama + Hermes integration: https://github.com/ollama/ollama/blob/main/docs/integrations/hermes.mdx
