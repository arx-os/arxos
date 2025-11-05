# Security Policy

## Supported Versions

We actively support security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

### Preferred Method: Email

Send an email to: **security@arxos.io**

Include:
- Description of the vulnerability
- Steps to reproduce (if applicable)
- Potential impact
- Suggested fix (if you have one)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Resolution Timeline**: Depends on severity and complexity

### Severity Levels

We classify vulnerabilities using the following severity levels:

- **Critical**: Remote code execution, authentication bypass, data breach
- **High**: Privilege escalation, sensitive data exposure
- **Medium**: Information disclosure, denial of service
- **Low**: Minor security issues, best practice violations

### What We Expect

- **Good faith**: Act in good faith to avoid privacy violations, destruction of data, and interruption or degradation of our service
- **Responsible disclosure**: Give us a reasonable time to address the issue before public disclosure
- **Details**: Provide sufficient information to reproduce and understand the issue

### What You Can Expect

- **Confirmation**: We'll acknowledge receipt of your report within 48 hours
- **Updates**: We'll keep you informed of our progress
- **Credit**: We'll credit you in our security advisories (if you wish)
- **Responsible handling**: We'll work with you to understand and resolve the issue quickly

## Security Best Practices

When using ArxOS:

1. **Never commit secrets**: Use `.env` files or secure configuration management
2. **Keep dependencies updated**: Run `cargo update` regularly
3. **Use pre-commit hooks**: Install security hooks with `./scripts/setup-security-hooks.sh`
4. **Review code changes**: Always review changes before committing
5. **Use strong authentication**: For Git operations, use GPG-signed commits

## Security Features

ArxOS includes several built-in security features:

- **Path Safety**: All file I/O operations are protected against directory traversal attacks
- **FFI Safety**: Comprehensive null pointer checks in mobile FFI functions
- **Input Validation**: All user inputs are validated before processing
- **Secret Detection**: Pre-commit hooks scan for accidentally committed secrets
- **Memory Safety**: Rust's memory safety guarantees prevent common vulnerabilities

## Known Security Considerations

### Building Data Privacy

- ArxOS uses Git for version control of building data
- **Important**: Building data files (`building.yaml`) are excluded from version control by default
- User-generated building files in the repository root are ignored via `.gitignore`
- When sharing building data, ensure it doesn't contain sensitive information

### Hardware Integration

- Hardware examples use placeholder credentials
- **Never commit real WiFi passwords, API keys, or tokens**
- Use environment variables or secure configuration management for production deployments

### Mobile Apps

- Mobile apps use secure FFI interfaces
- No sensitive data is stored in mobile app code
- User authentication is handled securely

## Disclosure Policy

We follow responsible disclosure practices:

1. **Private Report**: Vulnerabilities are reported privately
2. **Investigation**: We investigate and verify the issue
3. **Fix Development**: We develop and test fixes
4. **Release**: We release fixes and security advisories
5. **Public Disclosure**: After fixes are released, we may publicly disclose the issue

## Security Updates

Security updates are released as:
- **Patch releases**: For critical security fixes (e.g., 0.1.1 → 0.1.2)
- **Minor releases**: For security improvements (e.g., 0.1.x → 0.2.0)
- **Security advisories**: Published in `docs/security/` directory

## Additional Resources

- [Security Guide](../docs/development/SECURITY.md) - Comprehensive security documentation
- [Configuration Guide](../docs/core/CONFIGURATION.md) - Secure configuration practices
- [Pre-commit Hooks](../scripts/setup-security-hooks.sh) - Security hooks setup

---

**Last Updated**: January 2025  
**Contact**: security@arxos.io

