# Publishing Guide (Maintainers Only)

This guide is for repository maintainers who need to publish releases to PyPI.

## Prerequisites

1. PyPI account with access to the `vggt-mps` package
2. API tokens configured for PyPI and TestPyPI
3. Write access to the repository

## Setup PyPI Tokens

1. Get your API tokens:
   - PyPI: https://pypi.org/manage/account/token/
   - TestPyPI: https://test.pypi.org/manage/account/token/

2. Configure tokens:
   ```bash
   # Copy template
   cp .pypirc.template ~/.pypirc

   # Edit with your tokens
   nano ~/.pypirc

   # Secure the file
   chmod 600 ~/.pypirc
   ```

## Manual Publishing Process

### 1. Test on TestPyPI First

```bash
# Build and check
make check-dist

# Upload to TestPyPI
make test-upload

# Test installation
pip install -i https://test.pypi.org/simple/ vggt-mps
```

### 2. Publish to PyPI

```bash
# Create a new release with version bump
make release VERSION=2.0.1

# This will:
# - Update version in pyproject.toml
# - Create git tag
# - Build packages
# - Upload to PyPI

# Push tags to GitHub
git push origin main --tags
```

## Automated Publishing (GitHub Actions)

The repository includes GitHub Actions that automatically publish to PyPI when you create a release on GitHub.

### Creating a Release

1. Go to https://github.com/jmanhype/vggt-mps/releases
2. Click "Create a new release"
3. Choose a tag (e.g., `v2.0.1`)
4. Write release notes
5. Publish release

The GitHub Action will automatically:
- Build the distribution packages
- Check package integrity
- Publish to PyPI

### Setting up GitHub Secrets

For automated publishing to work, configure these secrets in your repository:

1. Go to Settings → Secrets and variables → Actions
2. Add repository secrets:
   - `PYPI_API_TOKEN`: Your PyPI API token
   - `TEST_PYPI_API_TOKEN`: Your TestPyPI API token (optional)

## Version Management

Follow semantic versioning:
- MAJOR.MINOR.PATCH (e.g., 2.0.1)
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

## Package Size Considerations

The MANIFEST.in file excludes:
- Model weights (*.pt, *.pth, *.ckpt)
- Large media files (*.mp4, *.avi)
- 3D files (*.ply, *.obj, *.glb)
- Development directories (models/, outputs/, data/)

Users will need to download the model separately:
```python
python main.py download
```

## Troubleshooting

### Package Too Large

If PyPI rejects the package for size:
1. Check what's included: `tar -tzf dist/*.tar.gz | head -20`
2. Update MANIFEST.in to exclude more files
3. Consider using git-lfs for large files

### Version Conflicts

If version already exists on PyPI:
1. Bump version in pyproject.toml
2. Create new tag
3. Retry upload

### Authentication Issues

If upload fails with authentication error:
1. Verify ~/.pypirc exists and has correct tokens
2. Check token scopes on PyPI
3. Try using `--repository-url` flag explicitly

## Quick Reference

```bash
# Build only
make build

# Check package
make check-dist

# Upload to TestPyPI
make test-upload

# Upload to PyPI (production)
make upload

# Full release process
make release VERSION=X.Y.Z
```

## Important Notes

- Never commit .pypirc or tokens to the repository
- Always test on TestPyPI before production
- Keep model weights separate from the package
- Document breaking changes in release notes
- Update README after publishing with new installation instructions