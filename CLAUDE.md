# AI Self-Improvement Guardrails

This document defines the constraints and guidelines for automated AI-driven improvements to this repository via the GitHub Actions self-improvement workflow.

## Purpose

The weekly self-improvement workflow uses Claude Code to automatically analyze and enhance this codebase. These guardrails ensure that automated changes remain safe, focused, and beneficial.

## Allowed Changes

Claude is permitted to make the following types of changes:

### 📝 Documentation
- Update README.md for accuracy and clarity
- Fix typos and grammar errors
- Improve code comments and docstrings
- Update documentation in `docs/` directory
- Ensure examples match current API
- Add missing API documentation
- Update installation instructions

### 🔧 CI/CD and Automation
- Improve GitHub Actions workflows
- Optimize workflow performance
- Update action versions to latest stable
- Add workflow documentation
- Improve error handling in automation

### 📦 Metadata and Configuration
- Update `pyproject.toml` metadata (description, keywords, classifiers)
- Improve package configuration
- Update `.gitignore` entries
- Format configuration files consistently
- Update copyright years

### 🧹 Code Quality (Non-Functional)
- Add or improve type hints
- Format code to PEP 8 standards
- Add missing docstrings
- Improve variable naming for clarity
- Add code comments for complex logic
- Remove commented-out code

### 🐛 Minor Bug Fixes (Low Risk)
- Fix obvious typos in code
- Correct import statement issues
- Fix formatting inconsistencies
- Address linting warnings

## Prohibited Changes

Claude **MUST NOT** make the following types of changes:

### ❌ Breaking Changes
- Changes to public API signatures
- Removal of existing features
- Changes to CLI command structure
- Modifications to exported functions/classes
- Database schema changes

### ❌ Core Functionality
- Modifications to core algorithms (VGGT, sparse attention)
- Changes to model loading or inference logic
- Modifications to MPS/GPU acceleration code
- Changes to 3D reconstruction pipeline
- Alterations to visualization logic

### ❌ Dependencies
- Adding new runtime dependencies
- Removing existing dependencies
- Upgrading dependencies to new major versions
- Changing minimum Python version

### ❌ Security-Sensitive Changes
- Modifications to authentication or authorization
- Changes to environment variable handling
- Updates to security-related code
- Changes to file permissions or access controls

### ❌ High-Risk Operations
- Database migrations
- File system restructuring
- Build system changes
- Test infrastructure modifications

## Change Requirements

All automated changes must:

1. **Be Incremental**: Make small, focused changes
2. **Be Reversible**: Easy to revert if needed
3. **Be Documented**: Include clear commit messages
4. **Be Non-Breaking**: Maintain backward compatibility
5. **Be Testable**: Not break existing tests

## Review Process

1. **Automated PRs** are created against the `develop` branch
2. **Human Review** is required before merging
3. **Testing** must pass before merge
4. **Rollback** is available if issues arise

## Scope of Automation

### Primary Focus Areas (Priority Order)

1. **Documentation Quality**: Keep docs accurate and helpful
2. **Code Readability**: Improve clarity without changing behavior
3. **Tooling**: Optimize CI/CD and development workflows
4. **Metadata**: Keep package info current and accurate

### Out of Scope

- New feature development
- Performance optimization (requires benchmarking)
- Refactoring (requires extensive testing)
- Architecture changes

## Examples

### ✅ Good Automated Changes

```markdown
- Add missing docstring to `vggt_quick_start_inference()`
- Fix typo in README installation section
- Update GitHub Actions to use ubuntu-latest
- Add type hints to utility functions
- Format code with black (PEP 8)
- Update package description in pyproject.toml
```

### ❌ Bad Automated Changes

```markdown
- Upgrade PyTorch to version 2.0 (dependency change)
- Refactor VGGT core to use new architecture (breaking)
- Add new CLI command for video processing (feature)
- Optimize sparse attention algorithm (requires testing)
- Change function signatures for better API (breaking)
- Modify MPS device detection logic (core functionality)
```

## Override Instructions

If you need Claude to make changes outside these guardrails:

1. **Manually trigger** the workflow with a custom prompt
2. **Clearly specify** what changes are needed
3. **Review carefully** before merging
4. **Update this file** if the change type should be allowed regularly

## Version History

- **v1.0** (2025-11-04): Initial guardrails for self-improvement workflow

## Questions?

If you're unsure whether a change is appropriate, err on the side of caution and create an issue for human review instead of making the change automatically.

---

*These guardrails help Claude be a helpful, safe, and predictable contributor to the VGGT-MPS project.*
