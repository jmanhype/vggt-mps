# Contributing to VGGT-MPS

Thanks for helping improve VGGT-MPS! This document outlines how we collaborate and publish releases. Please read it fully before opening a pull request.

## Development Workflow

- **Default branch**: `develop` is the day-to-day integration branch. Keep `main` stable for tagged releases only.
- **Feature branches**: create branches from `develop` using descriptive names (e.g. `feature/sparse-masking`, `fix/download-script`).
- **Pull requests**: target `develop`, keep diffs focused, and add tests or docs when behaviour changes. At least one approving review is required; use draft PRs for early discussion.
- **Commit hygiene**: use clear messages written in the imperative mood and avoid mixing unrelated changes.
- **Tooling state**: local IDE/state directories (e.g. `.vincent/`, `.claude/`, `.qodo/`) are ignored. Do not add new editor artefacts without updating `.gitignore`.

## Testing Expectations

- Run the relevant tests in `tests/` before requesting review. For sparse-attention changes, execute `pytest tests/sparse_attention` or the specific script under `tests/sparse_attention/`.
- If you add new features, include unit or smoke tests demonstrating the behaviour. Mention any skipped/slow tests in the PR description.

## Documentation

- Update `README.md` and `docs/README.md` when you add user-facing features or modify the workflow.
- Keep architecture notes in `docs/IMPLEMENTATION_SUMMARY.md`; add diagrams or tables as needed.

## Semantic Versioning

We follow [Semantic Versioning](https://semver.org/) for releases tagged on `main`:

- **MAJOR**: incompatible API or CLI changes, removal of features, or breaking behaviour. Coordinate with maintainers before merging.
- **MINOR**: backwards-compatible feature additions, performance improvements, or new tools.
- **PATCH**: backwards-compatible bug fixes or documentation-only updates that correct behaviour.

### Release Process

1. Merge the desired changes into `develop` and ensure CI/tests pass.
2. Open a PR from `develop` to `main` summarising the release. Confirm documentation is up to date.
3. Once merged, tag the resulting commit using `git tag vMAJOR.MINOR.PATCH && git push origin vMAJOR.MINOR.PATCH`.
4. Draft a GitHub Release linking to the tag and highlighting key changes.

If a release requires hotfixes, cherry-pick them onto `main`, bump the PATCH version, and then port the changes back to `develop`.

## Issue Reporting

- Open GitHub issues with clear reproduction steps, environment details (macOS version, Python version, PyTorch version), and logs.
- For security concerns, contact the maintainers directly instead of opening a public issue.

## Code of Conduct

The project follows the [GitHub Community Guidelines](https://docs.github.com/site-policy/github-terms/github-community-guidelines). Be respectful and constructive.

Happy hacking! 🍎
