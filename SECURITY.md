# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

We take the security of VGGT-MPS seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Where to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

1. **GitHub Security Advisories**: Use the [GitHub Security Advisory](https://github.com/jmanhype/vggt-mps/security/advisories/new) feature (preferred)
2. **Email**: Contact the maintainers by opening a private issue requesting contact information

### What to Include

Please include the following information in your report:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### Response Timeline

- We will acknowledge receipt of your vulnerability report within 48 hours
- We will send you a more detailed response within 7 days indicating the next steps
- We will keep you informed about the progress towards a fix and announcement
- We may ask for additional information or guidance

### Disclosure Policy

- We request that you give us reasonable time to address the issue before any public disclosure
- We will credit you in the security advisory (unless you prefer to remain anonymous)
- We will coordinate with you on the disclosure timeline

## Security Best Practices

When using VGGT-MPS:

1. **Model Weights**: Only download model weights from trusted sources (official Hugging Face repositories)
2. **Input Validation**: Validate and sanitize image inputs, especially when accepting user uploads
3. **Dependencies**: Regularly update dependencies to patch known vulnerabilities
4. **Environment**: Run in sandboxed or containerized environments when processing untrusted input
5. **MCP Server**: If using the MCP server integration, ensure Claude Desktop is up to date

## Known Security Considerations

### Model Weights

- The VGGT model weights (~5GB) should only be downloaded from the official Facebook Research Hugging Face repository
- Verify file integrity if implementing custom download mechanisms

### Image Processing

- The system processes images through PyTorch/torchvision which have their own security considerations
- Be cautious when processing images from untrusted sources
- Consider implementing file type validation and size limits

### GPU Access

- The MPS backend requires GPU access on Apple Silicon
- Ensure appropriate system permissions are configured
- Monitor GPU memory usage to prevent resource exhaustion

## Dependencies Security

We rely on the following security-critical dependencies:

- **PyTorch**: Deep learning framework with GPU acceleration
- **Transformers**: Hugging Face transformers library
- **Pillow**: Image processing library
- **OpenCV**: Computer vision library

We recommend using `pip-audit` or similar tools to check for known vulnerabilities:

```bash
pip install pip-audit
pip-audit
```

## Updates and Patches

Security updates will be released as patch versions (e.g., 2.0.1) and announced via:

- GitHub Security Advisories
- Release notes
- README updates

Subscribe to repository releases to be notified of security updates.

---

Thank you for helping keep VGGT-MPS and its users safe!
