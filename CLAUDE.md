# Claude Code Guardrails

This file defines what Claude Code is allowed to modify when performing automated improvements.

## Allowed Modifications

Claude Code MAY modify:
- Documentation files (README.md, docs/*, *.md)
- CI/CD configurations (.github/workflows/*, .gitlab-ci.yml, etc.)
- Metadata files (package.json, pyproject.toml, setup.py - metadata only)
- License files
- Security policies (SECURITY.md)
- Code of Conduct
- Contributing guidelines
- GitHub-specific files (.gitignore, CODEOWNERS, etc.)

## Restricted Modifications

Claude Code MUST NOT modify without explicit approval:
- Source code (src/*, lib/*, *.py, *.js, *.ts, etc.)
- Test files
- Configuration that affects runtime behavior
- Database schemas or migrations
- API definitions or contracts
- Dependency versions (only suggest, don't auto-update)

## Exception: Issues Labeled `ai-implement`

When an issue is labeled `ai-implement`, Claude Code may modify source code to implement the requested feature or fix, but must:
1. Reference the issue number in the PR
2. Follow existing code style and patterns
3. Include tests if the project has a test suite
4. Not change public APIs without discussion in the issue

## Pull Request Requirements

All PRs created by Claude Code MUST include:
1. A clear description of what was changed and why
2. A receipt line in the format: `Receipt: <hash>`
3. Reference to the workflow run that created it
4. Minimal, focused changes (prefer small PRs over large ones)

## General Principles

1. **Minimal Deltas**: Make the smallest change that solves the problem
2. **No Breaking Changes**: Never introduce breaking changes
3. **Follow Existing Patterns**: Match the style and structure of existing code
4. **Documentation First**: When in doubt, improve documentation rather than code
5. **Safety First**: If uncertain, create an issue for human review instead of making changes

---

*This file was created to ensure safe and predictable AI-assisted repository maintenance.*
