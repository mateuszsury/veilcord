# Security Policy

## Reporting a Vulnerability

**Please DO NOT open public issues for security vulnerabilities.**

If you discover a security vulnerability in Veilcord, please report it privately:

**Email:** mateuszsury25@gmail.com

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Initial Response:** Within 48 hours
- **Status Update:** Within 7 days
- **Fix Timeline:** Depends on severity (critical: 24-48h, high: 1 week, medium: 2 weeks)

### Scope

Security issues we're interested in:

- Encryption bypasses or weaknesses
- Authentication/authorization flaws
- Data leakage vulnerabilities
- Remote code execution
- Denial of service in critical paths
- Cryptographic implementation flaws

### Out of Scope

- Issues requiring physical device access
- Social engineering attacks
- Issues in dependencies (report to upstream)
- Theoretical attacks without proof of concept

### Recognition

We appreciate security researchers who help keep Veilcord secure. With your permission, we'll acknowledge your contribution in our release notes.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Security Features

Veilcord implements multiple security layers:

- **Signal Protocol**: Industry-standard E2E encryption
- **X3DH Key Agreement**: Perfect forward secrecy
- **Double Ratchet**: Self-healing encryption
- **SQLCipher**: AES-256 encrypted local storage
- **Windows DPAPI**: OS-level key protection
- **Ed25519 Signatures**: Message authentication
