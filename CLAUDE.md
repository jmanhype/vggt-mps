# CLAUDE.md — Repo Guardrails
- Scope: only docs/CI/metadata unless a human explicitly asks for code changes in an issue with label "ai-implement".
- Never change license, module names, or public APIs without a human-approved issue.
- Prefer minimal deltas: small PRs over refactors.
- Always include a plaintext "receipt" line in PR descriptions: `receipt: sha256(<content-without-receipt>)`.
- If tests exist, run them before proposing changes; if none, scaffold the lightest smoke test only.
