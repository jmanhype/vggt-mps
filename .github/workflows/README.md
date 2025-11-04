# GitHub Actions Workflows

This directory contains automated workflows for the VGGT-MPS project.

## Available Workflows

### 1. Weekly Self-Improvement (`weekly-self-improvement.yml`)

An automated maintenance workflow that uses Claude Code to continuously improve the codebase.

**Schedule:** Every Monday at 9:00 AM UTC

**What it does:**
- Analyzes code for quality improvements and potential bugs
- Reviews documentation for accuracy and completeness
- Checks for outdated dependencies
- Suggests small enhancements and optimizations
- Creates a pull request with improvements to the `develop` branch

**How it works:**
1. The workflow runs on schedule (or manual trigger)
2. Uses the `anthropics/claude-code-action@v1` GitHub Action
3. Claude analyzes the codebase based on the maintenance prompt
4. Creates a branch named `auto-improve-{timestamp}`
5. Makes improvements and commits changes
6. Opens a PR against the `develop` branch
7. Team reviews and merges the PR

**Manual Trigger:**
You can manually trigger the workflow from the GitHub Actions tab:
1. Go to Actions → Weekly Self-Improvement
2. Click "Run workflow"
3. Select the branch and click "Run workflow"

**No API Key Required:**
The `anthropics/claude-code-action` handles authentication automatically through GitHub. No additional secrets or API keys need to be configured!

**Customization:**

To modify the maintenance tasks, edit the `prompt` section in `weekly-self-improvement.yml`:

```yaml
with:
  prompt: |
    Your custom maintenance instructions here...
```

To change the schedule, modify the `cron` expression:
```yaml
on:
  schedule:
    - cron: '0 9 * * 1'  # Min Hour Day Month DayOfWeek
```

Common schedules:
- Daily at 2am: `'0 2 * * *'`
- Twice weekly (Mon/Thu): `'0 9 * * 1,4'`
- Monthly (1st): `'0 9 1 * *'`

**Configuration Options:**

The workflow supports these parameters:
- `create_pr: true` - Automatically create a pull request
- `pr_title` - Title for the PR
- `pr_body` - Description for the PR
- `branch_prefix` - Prefix for the created branch
- `base_branch` - Target branch for the PR (default: `develop`)

### 2. Publish to PyPI (`publish.yml`)

Publishes the package to PyPI when a release is created.

**Trigger:** On release publication or manual dispatch

**What it does:**
- Builds the Python package
- Publishes to TestPyPI or PyPI
- Uses trusted publishing (no API tokens needed)

## Best Practices

### Security
- All workflows use specific action versions (not `@latest`)
- Permissions are explicitly set to minimum required
- No sensitive credentials are stored in the repository

### Maintenance
- Review automated PRs before merging
- Update action versions periodically
- Monitor workflow run times and costs

### Branch Strategy
Automated improvements target the `develop` branch per our [contributing guidelines](../../CONTRIBUTING.md). Maintainers promote changes to `main` during releases.

## Troubleshooting

**Workflow fails with permissions error:**
- Check that the repository has Actions enabled
- Verify branch protection rules allow the bot to create PRs
- Ensure the workflow has correct permissions in the YAML

**No PR is created:**
- Check the workflow logs for errors
- Verify `create_pr: true` is set
- Ensure the `develop` branch exists

**Changes seem incorrect:**
- Review the prompt in the workflow file
- Adjust the constraints or instructions
- Consider adding more specific guidelines

## Contributing

When modifying workflows:
1. Test changes in a fork first
2. Use `workflow_dispatch` for manual testing
3. Document any new workflows in this README
4. Follow GitHub Actions best practices

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Claude Code GitHub Action](https://github.com/anthropics/claude-code-action)
- [Cron Expression Generator](https://crontab.guru/)
