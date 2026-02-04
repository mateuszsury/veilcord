# Contributing to Veilcord

Thank you for your interest in contributing to Veilcord! We welcome contributions from the community to help make secure, private communication accessible to everyone.

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [Your contact email].

## How Can I Contribute?

### Reporting Bugs

Before submitting a bug report:
1. **Check existing issues** - Your bug may already be reported
2. **Try the latest version** - The bug may already be fixed
3. **Gather information** - OS version, Python version, steps to reproduce

**Submit a bug report:**
- Use the [GitHub issue tracker](https://github.com/mateuszsury/veilcord/issues)
- Use a clear, descriptive title
- Describe the exact steps to reproduce the issue
- Describe the behavior you observed and what you expected
- Include screenshots if relevant
- Include your environment details (Windows version, Veilcord version)

**Security vulnerabilities** should be reported privately via email, not GitHub issues. See [Security](#security) below.

### Suggesting Features

We welcome feature suggestions! Before submitting:
1. **Check existing issues** - The feature may already be requested
2. **Consider the scope** - Does it align with Veilcord's privacy focus?
3. **Explain the use case** - Why would this feature be valuable?

**Submit a feature request:**
- Use the GitHub issue tracker with a clear title
- Describe the feature and its motivation
- Explain how it would work from a user perspective
- Consider potential privacy or security implications

### Pull Requests

**Before starting work:**
1. Comment on an existing issue or open a new one to discuss your idea
2. Wait for feedback from maintainers to ensure it aligns with project goals
3. Fork the repository and create a branch

**Development workflow:**

1. **Set up your environment** - See [Building from Source](../README.md#building-from-source)
2. **Create a branch** - Use a descriptive name (e.g., `feat/group-call-ui` or `fix/message-encryption-bug`)
3. **Make your changes** - Follow code style guidelines below
4. **Test your changes** - Ensure no regressions
5. **Commit with clear messages** - Use conventional commits (see below)
6. **Push and submit a PR** - Link to related issues

**Pull request guidelines:**
- Keep PRs focused on a single feature or fix
- Update documentation if needed (README, comments)
- Add tests for new functionality
- Ensure the code builds successfully
- Respond to review feedback promptly

### Commit Message Style

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring (no behavior change)
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `chore`: Build, tooling, dependencies

**Examples:**
```
feat(crypto): add X25519 key exchange support
fix(ui): prevent message duplication in chat list
docs(readme): update installation instructions
```

## Code Style Guidelines

### Python

- **PEP 8** - Follow Python style guidelines
- **Type hints** - Use type annotations where possible
- **Docstrings** - Document classes and complex functions
- **Imports** - Group by stdlib, third-party, local
- **Line length** - 88 characters (Black formatter default)

**Example:**
```python
from typing import Optional
import asyncio

async def send_message(
    contact_id: str,
    message: str,
    timeout: Optional[int] = 30
) -> bool:
    """
    Send an encrypted message to a contact.

    Args:
        contact_id: Public key of the recipient
        message: Plain text message to send
        timeout: Connection timeout in seconds

    Returns:
        True if message sent successfully, False otherwise
    """
    # Implementation...
```

### TypeScript / React

- **ESLint** - Follow project ESLint configuration
- **Functional components** - Use hooks, not class components
- **TypeScript** - Use strict types, avoid `any`
- **File naming** - PascalCase for components, camelCase for utilities
- **Imports** - Organize by external, internal, relative

**Example:**
```typescript
interface MessageProps {
  content: string;
  timestamp: number;
  senderName: string;
}

export const Message: React.FC<MessageProps> = ({
  content,
  timestamp,
  senderName
}) => {
  return (
    <div className="message">
      <span className="sender">{senderName}</span>
      <p className="content">{content}</p>
      <time>{new Date(timestamp).toLocaleString()}</time>
    </div>
  );
};
```

## Testing

**Run existing tests:**
```bash
# Python (if tests exist)
pytest tests/

# Frontend
cd frontend
npm test
```

**Write tests for:**
- New cryptographic functions (critical)
- API bridge methods
- UI components with complex logic
- File transfer and chunking logic

## Security

**Reporting security vulnerabilities:**
- **DO NOT** open a public GitHub issue
- Email details to: [Your security email]
- Include steps to reproduce and potential impact
- Allow 48 hours for initial response

**Security guidelines:**
- Never commit secrets, keys, or credentials
- Use type-safe cryptographic libraries
- Validate all user input
- Follow principle of least privilege
- Consider timing attacks in crypto code

## License Agreement

By contributing to Veilcord, you agree that:
- Your contributions will be licensed under the same dual license as the project
- You have the right to submit the contribution
- You understand the personal/commercial license distinction

See [LICENSE](../LICENSE) for full terms.

## Development Resources

- **Documentation**: See README.md for architecture overview
- **Issues**: [GitHub issue tracker](https://github.com/mateuszsury/veilcord/issues)
- **Wiki**: [Development guides](https://github.com/mateuszsury/veilcord/wiki)

## Questions?

Not sure where to start? Open a GitHub issue with the `question` label or reach out to the maintainers.

Thank you for contributing to privacy-focused communication!

---

*Last updated: 2026-02-04*
