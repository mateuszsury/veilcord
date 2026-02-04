# Phase 11: Branding, Documentation & Release - Research

**Researched:** 2026-02-04
**Domain:** Application Branding, Technical Documentation, GitHub Release Management
**Confidence:** HIGH

## Summary

This research covers the complete lifecycle of rebranding a desktop application from "DiscordOpus" to "Veilcord" and publishing it to GitHub with professional documentation and binary releases. The phase involves three distinct technical domains: codebase renaming/migration, documentation creation following GitHub best practices, and GitHub release management with binary distribution.

**Key Challenge Identified:** The codebase contains cryptographic protocol constants (HKDF info parameters, associated data) with "DiscordOpus" hardcoded as byte strings. These CANNOT be changed without breaking backward compatibility with existing encrypted sessions and stored data. Migration requires careful planning to avoid data loss.

**Standard Approach:**
1. Use IDE refactoring tools for safe renaming across the codebase
2. Keep cryptographic constants unchanged (they're internal protocol identifiers, not user-facing branding)
3. Follow Keep a Changelog format for CHANGELOG.md
4. Use shields.io badges for README status indicators
5. Implement dual licensing with clear personal/commercial distinction
6. Use GitHub's official templates for CONTRIBUTING.md and CODE_OF_CONDUCT.md
7. Create multi-resolution .ico files (16x16 to 256x256) for Windows compatibility
8. Follow semantic versioning (v1.0.0) for initial release

**Primary recommendation:** Separate user-facing branding changes (UI, window titles, AUMID) from internal protocol constants (crypto info parameters). Only rename the former to avoid breaking existing user data.

## Standard Stack

### Core Tools

| Tool/Service | Version | Purpose | Why Standard |
|--------------|---------|---------|--------------|
| shields.io | 2026 | README badges | Serves 1.6B images/month, used by VS Code, Vue.js, Bootstrap |
| Keep a Changelog | 1.1.0 | Changelog format | ISO 8601 dates, semantic versioning integration, widely adopted |
| GitHub Templates | 2026 | Community files | Official GitHub-provided templates for CONTRIBUTING, CODE_OF_CONDUCT |
| ConvertICO | 2026 | PNG→ICO conversion | Multi-resolution support (16-256px), Windows 11/10 compatible |
| semantic-release | 2026 | Automated versioning | Standard for GitHub release automation (optional) |

### Supporting Tools

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| Canva Logo Maker | 2026 | Logo creation | Free, AI-powered, no design skills needed |
| Adobe Express | 2026 | Icon design | Professional templates, drag-and-drop |
| LOGO.com | 2026 | Brand assets | Unlimited high-res files, favicon generation |
| PyInstaller --clean | 6.18.0 | Build cleanup | When dependencies change or PyInstaller updates |
| gh CLI | 2026 | Release creation | Automated release with changelog and assets |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| shields.io badges | Custom SVG badges | More customization but no auto-updates, maintenance burden |
| Keep a Changelog | Auto-generated from commits | Loses human curation, less context for users |
| Manual PNG→ICO | Pillow script | More control but manual, risk of missing sizes |
| GitHub web UI | gh CLI for releases | GUI simpler for first-time, CLI better for automation |

**Installation:**
```bash
# For automated releases (optional)
pip install semantic-release

# GitHub CLI (Windows)
winget install GitHub.cli

# No installation needed for web-based tools:
# - shields.io
# - ConvertICO.com
# - Logo makers (Canva, Adobe Express, LOGO.com)
```

## Architecture Patterns

### Recommended Project Structure

After Phase 11 completion:

```
DiscordOpus/  (rename to veilcord locally after GitHub push)
├── .github/
│   ├── CONTRIBUTING.md         # Contribution guidelines
│   ├── CODE_OF_CONDUCT.md      # Community standards
│   └── ISSUE_TEMPLATE/          # Issue templates (optional)
├── assets/
│   └── icon.ico                 # Multi-res Windows icon (16-256px)
├── docs/                        # Additional documentation (optional)
│   ├── ARCHITECTURE.md
│   └── API.md
├── frontend/
├── src/
├── .gitignore
├── build.spec                   # PyInstaller spec (Veilcord branding)
├── CHANGELOG.md                 # Keep a Changelog format
├── LICENSE                      # Dual license (personal/commercial)
├── README.md                    # Comprehensive project overview
└── requirements.txt
```

### Pattern 1: Safe Codebase Renaming

**What:** Systematic renaming of application identifiers across codebase while preserving internal protocol constants.

**When to use:** When rebranding an application with existing user data and cryptographic protocols.

**Categories of Renaming:**

1. **MUST CHANGE (User-Facing):**
   - Window titles (main.py)
   - Package names (frontend/package.json)
   - HTML titles (frontend/index.html)
   - AUMID (notifications/service.py)
   - Build artifact names (build.spec)
   - File paths (%APPDATA%/Veilcord/)
   - Documentation/comments

2. **MUST NOT CHANGE (Protocol Internal):**
   - HKDF info parameters (crypto/signal_session.py)
   - Associated data constants (crypto/signal_session.py)
   - Message chain constants (groups/sender_keys.py)

**Example:**
```python
# File: src/main.py
# CHANGE THIS:
window = webview.create_window(
    'Veilcord',  # Changed from 'DiscordOpus'
    ...
)

# File: src/crypto/signal_session.py
# DO NOT CHANGE THIS (internal protocol identifier):
INFO_ROOT_CHAIN = b"DiscordOpus_RootChain_v1"  # Keep unchanged!
INFO_MESSAGE_CHAIN = b"DiscordOpus_MessageChain_v1"  # Keep unchanged!
INFO_AEAD = b"DiscordOpus_AEAD_v1"  # Keep unchanged!
```

**Rationale:** Cryptographic info parameters are domain separators in HKDF. Changing them produces different derived keys, making existing encrypted data unreadable. These are internal protocol identifiers, not user-facing branding.

Source: [Cryptography documentation](https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/)

### Pattern 2: Keep a Changelog Format

**What:** Structured changelog with categorized changes for each version.

**When to use:** For all releases, updated before each GitHub release creation.

**Example:**
```markdown
# Changelog

All notable changes to Veilcord will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-02-04

### Added
- End-to-end encrypted text messaging with Signal Protocol
- P2P voice and video calls with WebRTC
- File transfer with chunked encryption
- Group messaging with sender keys
- Screen sharing during calls
- Audio effects (noise reduction, voice changer, equalizer)
- Video effects (background blur, beauty filters, creative filters)
- Windows desktop notifications
- Secure local storage with SQLCipher and DPAPI
- Auto-updates with TUF framework

### Security
- Double Ratchet encryption for messages
- X3DH key agreement protocol
- Perfect forward secrecy
- Post-compromise security
- Windows DPAPI for key protection

[1.0.0]: https://github.com/mateuszsury/veilcord/releases/tag/v1.0.0
```

**Categories:**
- **Added** - New features
- **Changed** - Changes to existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Security-related changes

Source: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

### Pattern 3: Dual License Structure

**What:** Two separate licenses - one for personal use (free), one for commercial use (paid).

**When to use:** For sustainable open-source projects that need commercial funding.

**LICENSE file structure:**
```markdown
# Veilcord License

Veilcord is dual-licensed:

## Personal Use License (Free)

Copyright (c) 2026 Mateusz Sury

Permission is hereby granted, free of charge, to any **individual** person obtaining a copy
of this software and associated documentation files (the "Software"), to use the Software
for **personal, non-commercial purposes** only, subject to the following conditions:

- The Software may not be used for any commercial purpose
- The Software may not be redistributed or resold
- This notice must be included in all copies or substantial portions of the Software

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND...

## Commercial Use License (Paid)

For commercial use, including but not limited to:
- Use within a business or organization
- Integration into commercial products or services
- Redistribution as part of a commercial offering

Please contact: [email] for licensing terms.

## Definition of Commercial Use

Commercial use includes any use where the primary purpose is monetary compensation or
business advantage, including but not limited to:
- Use by employees in the course of their employment
- Use by contractors or consultants for clients
- Integration into products or services that are sold or monetized
```

**Alternative Approach:** Use AGPL + commercial license (stronger copyleft drives commercial sales)

Source: [GitHub dual-license-templates](https://github.com/lawndoc/dual-license-templates)

### Pattern 4: Professional README Structure

**What:** Comprehensive README with SEO optimization and user-focused content.

**Structure:**
```markdown
# Veilcord

[Logo/Banner Image]

[![License](https://img.shields.io/badge/license-Dual-blue.svg)](LICENSE)
[![Windows](https://img.shields.io/badge/platform-Windows-blue.svg)]()
[![Release](https://img.shields.io/github/v/release/mateuszsury/veilcord)](releases)

**Private by design. Encrypted by default.**

Veilcord is a privacy-focused peer-to-peer encrypted messaging application for Windows.
No servers, no tracking, no data collection - just secure communication.

[Screenshot]

## Features

### 🔒 Security First
- **End-to-end encryption** using Signal Protocol (Double Ratchet + X3DH)
- **Perfect forward secrecy** - compromised keys don't decrypt past messages
- **Post-compromise security** - automatic recovery from key compromise
- **Zero knowledge** - all encryption happens locally, no cloud storage

### 💬 Rich Communication
[Feature list with icons]

## Quick Start

### Installation

1. Download the latest release: [Veilcord-v1.0.0.exe](releases)
2. Run the installer
3. Launch Veilcord

### First Message

[Step-by-step with screenshots]

## How It Works

[Technical architecture overview with diagram]

## Building from Source

[Prerequisites, installation, build commands]

## Contributing

See [CONTRIBUTING.md](.github/CONTRIBUTING.md)

## Security

Report security vulnerabilities to: [email]

## License

Dual licensed - see [LICENSE](LICENSE)

## Contact

- GitHub: [@mateuszsury](https://github.com/mateuszsury)
- Issues: [GitHub Issues](issues)
```

**SEO Optimization:**
- Repository name: `veilcord` (keyword-rich, memorable)
- Description: "Privacy-focused P2P encrypted messaging app with E2E encryption, voice/video calls, and file transfer"
- Topics (exact match): `encryption`, `p2p`, `messaging`, `privacy`, `webrtc`, `signal-protocol`, `e2e-encryption`, `desktop-app`, `windows`, `python`, `react`, `typescript`, `secure-messaging`

Sources:
- [GitHub SEO Guide 2025](https://www.gitdevtool.com/blog/github-seo)
- [The Ultimate Guide to GitHub SEO](https://dev.to/infrasity-learning/the-ultimate-guide-to-github-seo-for-2025-38kl)

### Pattern 5: Windows Icon Multi-Resolution ICO

**What:** Single .ico file containing multiple image sizes for crisp display at all resolutions.

**Required sizes:**
- 16x16 - Small icons, file explorer
- 32x32 - Standard icons
- 48x48 - Large icons
- 64x64 - Extra large icons (Classic Mode)
- 256x256 - High DPI displays, Windows 10/11

**Optimal sizes (comprehensive):**
- 16x16, 24x24, 32x32, 48x48, 64x64, 128x128, 256x256

**Process:**
1. Design logo at highest resolution (1024x1024 PNG)
2. Export as PNG with transparency
3. Use ConvertICO.com or similar tool
4. Select all required sizes
5. Generate multi-resolution .ico

**PyInstaller integration:**
```python
# build.spec
exe = EXE(
    ...
    icon=str(project_root / 'assets' / 'icon.ico'),  # Multi-res ICO
)
```

**Icon Cache Issue:** Windows caches icons aggressively. After rebuilding with new icon:
- Rename the .exe file OR
- Copy to different location OR
- Clear icon cache (restart Explorer)

Sources:
- [Windows ICO Made Simple](https://creativefreedom.co.uk/icon-designers-blog/windows-ico-made-simple/)
- [Microsoft Learn - App Icon Construction](https://learn.microsoft.com/en-us/windows/apps/design/style/iconography/app-icon-construction)

### Pattern 6: GitHub Release with Binary Assets

**What:** Tagged release with changelog, binary .exe, and checksums.

**Process:**
```bash
# 1. Build the binary
pyinstaller --clean build.spec

# 2. Create distributable (zip or installer)
cd dist
7z a Veilcord-v1.0.0-Windows.zip Veilcord/

# 3. Generate checksums
certutil -hashfile Veilcord-v1.0.0-Windows.zip SHA256 > checksums.txt

# 4. Create annotated tag
git tag -a v1.0.0 -m "Release v1.0.0 - Initial public release"
git push origin v1.0.0

# 5. Create GitHub release with gh CLI
gh release create v1.0.0 \
  --title "Veilcord v1.0.0 - Initial Release" \
  --notes-file CHANGELOG.md \
  Veilcord-v1.0.0-Windows.zip \
  checksums.txt

# Alternative: Use GitHub web UI
# Navigate to Releases → Draft a new release → Choose tag → Upload assets
```

**Semantic Versioning:**
- v1.0.0 - Initial stable release
- v1.0.1 - Patch (bug fixes)
- v1.1.0 - Minor (new features, backward compatible)
- v2.0.0 - Major (breaking changes)

**Prefix Convention:** Use `v` prefix (v1.0.0, not 1.0.0) for clarity and tooling compatibility.

Sources:
- [Semantic Versioning 2.0.0](https://semver.org/)
- [GitHub Releases and Tags Guide](https://blog.sivo.it.com/github-releases-and-tags/how-do-you-tag-a-release-in-github/)

### Anti-Patterns to Avoid

- **Changing crypto constants:** NEVER change HKDF info parameters, associated data, or chain constants - breaks existing data
- **Incomplete icon sizes:** Missing standard sizes (16, 32, 48, 256) causes blurry icons at some scales
- **Vague LICENSE:** "Free for personal, contact for commercial" without clear definitions leads to licensing disputes
- **Broken links in README:** Dead links to screenshots, badges, or documentation hurt credibility and SEO
- **Too many badges:** More than 5-7 badges clutters README and reduces focus
- **Missing .gitignore before initial push:** Accidentally pushing `node_modules/`, `dist/`, or secrets
- **Force pushing to main:** Rewriting history on public repository breaks clones and forks

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Logo/icon design | Custom graphics editor workflow | Canva/Adobe Express + ConvertICO | Free templates, AI-powered, multi-resolution export built-in |
| Changelog format | Custom markdown structure | Keep a Changelog standard | Widely recognized, parser-friendly, semantic versioning integration |
| README badges | Manual SVG creation | shields.io | Auto-updating, 1.6B images/month, CDN-backed, consistent styling |
| CONTRIBUTING template | Write from scratch | GitHub's official templates | Battle-tested, community-standard, covers legal/ethical bases |
| CODE_OF_CONDUCT | Custom code of conduct | Contributor Covenant (GitHub template) | Widely adopted, legally vetted, trusted by major projects |
| PNG→ICO conversion | PIL/Pillow script | ConvertICO.com or similar | Handles all required sizes, validates format, Windows-tested |
| License text | Custom legal text | Established licenses (MIT, AGPL, dual-license templates) | Legally vetted, recognized by GitHub/tooling, reduces ambiguity |
| Icon cache clearing | Manual Windows registry edits | Rename .exe or copy to new location | Registry edits risky, simple rename achieves same result |

**Key insight:** Documentation and branding are well-established domains with mature tooling. Custom solutions add maintenance burden without meaningful differentiation. Use standard formats and templates so users/contributors know what to expect.

## Common Pitfalls

### Pitfall 1: Breaking Encrypted Data by Renaming Crypto Constants

**What goes wrong:** Developer renames ALL instances of "DiscordOpus" to "Veilcord", including cryptographic info parameters in HKDF calls. Existing users' encrypted messages, files, and sessions become unreadable after update.

**Why it happens:** Crypto constants look like application identifiers, but they're actually domain separators in key derivation. Changing `info=b"DiscordOpus_X3DH_SharedSecret_v1"` to `info=b"Veilcord_X3DH_SharedSecret_v1"` produces completely different derived keys via HKDF.

**How to avoid:**
1. Audit all renaming locations BEFORE executing
2. Identify crypto protocol constants (HKDF info, AEAD associated data)
3. Exclude these from renaming operations
4. Add comments: `# DO NOT RENAME: Protocol identifier, not user-facing branding`
5. Test with existing user data: Create test messages with old build, verify readable with new build

**Warning signs:**
- Unit tests fail after renaming (session establishment, encryption/decryption)
- Error logs show "decryption failed" or "MAC verification failed"
- Existing database opens but messages are corrupted

**Detection:** Search for `b"DiscordOpus` (byte strings) separately from `"DiscordOpus"` (regular strings). Byte strings in crypto modules are likely protocol constants.

Source: [Cryptography Key Derivation Functions](https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/)

### Pitfall 2: Icon Cache Confusion After PyInstaller Rebuild

**What goes wrong:** Developer rebuilds .exe with new Veilcord icon, but Windows Explorer still shows old DiscordOpus icon. Developer assumes PyInstaller failed, wastes time debugging icon embedding.

**Why it happens:** Windows maintains an icon cache (IconCache.db) for performance. When .exe metadata doesn't change (same file path, similar timestamp), Windows uses cached icon instead of reading from file.

**How to avoid:**
1. After rebuilding, rename .exe (e.g., DiscordOpus.exe → Veilcord.exe)
2. Verify icon embedded: Right-click .exe → Properties → Icon should match
3. If icon still wrong, copy .exe to different folder (forces cache refresh)
4. Document in build instructions: "Icon changes require rename or copy"

**Alternative (nuclear option):** Clear icon cache manually:
```cmd
:: Close all Explorer windows first
taskkill /IM explorer.exe /F
del /A /Q "%localappdata%\IconCache.db"
start explorer.exe
```

**Warning signs:**
- Icon correct in Properties but wrong in Explorer
- Icon changes when file is copied to different location
- Icon changes when .exe is renamed

Sources:
- [PyInstaller Icon Settings Discussion](https://github.com/orgs/pyinstaller/discussions/8584)
- [How to Add Icon to PyInstaller](https://coderslegacy.com/python/add-icon-to-pyinstaller-exe/)

### Pitfall 3: Incomplete .gitignore Before Initial Push

**What goes wrong:** Developer creates GitHub repository, runs `git add .`, pushes entire project. GitHub rejects push due to large files (node_modules/, dist/, .venv/), or worse, accepts push with secrets (.env, API keys).

**Why it happens:** Default git behavior is to track all files. Without .gitignore, binary build artifacts, dependencies, and sensitive files are staged.

**How to avoid:**
1. Create .gitignore BEFORE initial commit
2. Use GitHub's Python + Node templates as base
3. Add project-specific exclusions:
```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
venv/
dist/
build/
*.spec.bak

# Node.js
node_modules/
frontend/dist/

# Build artifacts
*.exe
*.zip
*.msi

# Sensitive
.env
*.key
secrets/

# IDE
.vscode/
.idea/
*.swp

# Windows
Thumbs.db
desktop.ini

# Application data (user testing)
%APPDATA%/Veilcord/
```

4. Test with `git status` before `git add .`
5. Use `git add -p` for interactive staging (safer than `-A`)

**Warning signs:**
- `git status` shows hundreds of files in node_modules/
- Push fails with "file exceeds 100 MB"
- .env or credentials.json appears in staged files

**Recovery:** If secrets pushed:
- Do NOT just delete file and commit - it's in history
- Use `git filter-branch` or BFG Repo-Cleaner to purge history
- Rotate all exposed secrets immediately

Sources:
- [GitHub .gitignore Guide](https://docs.github.com/en/get-started/getting-started-with-git/ignoring-files)
- [GitHub gitignore Templates](https://github.com/github/gitignore)

### Pitfall 4: Vague Dual License Definitions

**What goes wrong:** LICENSE says "free for personal use, contact for commercial." User deploys Veilcord internally at a non-profit. Non-profit argues they're "personal" (no revenue), developer argues it's "commercial" (organizational use). Legal dispute ensues.

**Why it happens:** Terms like "personal," "commercial," "business" have no universal legal definition. What counts as "commercial use" varies by jurisdiction and interpretation.

**How to avoid:**
1. Define terms explicitly in LICENSE:
```markdown
## Definition of Commercial Use

"Commercial use" means any use where the primary purpose is monetary
compensation or business advantage, INCLUDING:

- Use by employees in the course of their employment
- Use by contractors or consultants for clients
- Use within any organization (for-profit or non-profit)
- Integration into products or services that are sold or monetized
- Use that generates direct or indirect revenue

"Personal use" means use by an individual person for their own private,
non-work-related communication, NOT including:

- Use on work devices or for work purposes
- Use shared with coworkers or business contacts
- Use in home offices during work hours
```

2. Provide examples of each category
3. Include contact for ambiguous cases
4. Consider using established licenses (AGPL + commercial exception) instead of custom text

**Warning signs:**
- LICENSE uses terms without definitions
- No examples of permitted/prohibited uses
- Conflicts between different license sections

**Alternative:** Use Fair Source license or Prosperity License (permissive for non-commercial, time-delayed commercial availability).

Source: [Dual Licensing Explained](https://www.termsfeed.com/blog/dual-license-open-source-commercial/)

### Pitfall 5: Missing Multi-Resolution Icon Sizes

**What goes wrong:** Developer creates beautiful 256x256 icon, converts to .ico with only that one size. Icon looks crisp in Windows 10 large icons view, but blurry/pixelated in taskbar (32x32) and file explorer small icons (16x16).

**Why it happens:** Windows scales from the closest available size. Scaling 256→16 loses detail and clarity. Each icon size needs manual optimization for that scale.

**How to avoid:**
1. Design icon to be recognizable at 16x16 (simplify details)
2. Create optimized versions at each size:
   - 16x16: Simplified, bold shapes, no fine details
   - 32x32: Moderate detail
   - 48x48: More detail
   - 256x256: Full detail
3. Use ConvertICO.com with ALL standard sizes selected
4. Test by viewing in Explorer at different zoom levels

**Optimal workflow:**
1. Design at 1024x1024 (master)
2. Export 256x256, 128x128, 64x64, 48x48, 32x32, 24x24, 16x16
3. Manually optimize 16x16 and 32x32 (most common sizes)
4. Combine into single multi-resolution .ico

**Warning signs:**
- Icon looks sharp in Properties dialog but blurry in Explorer
- Details disappear or become muddy at small sizes
- Icon looks different in taskbar vs. desktop

Source: [Icon Size Guidelines](https://blog.icons8.com/articles/choosing-the-right-size-and-format-for-icons/)

### Pitfall 6: Forgetting to Update AUMID for Notifications

**What goes wrong:** Developer renames app to Veilcord, updates window title, package.json, builds new .exe. Notifications still show "DiscordOpus" in Action Center, confusing users.

**Why it happens:** Windows notifications use AUMID (Application User Model ID) to identify the source. AUMID is separate from window title and .exe name. Hardcoded in `src/notifications/service.py`.

**How to avoid:**
1. Include AUMID in renaming checklist:
```python
# src/notifications/service.py
AUMID = "Veilcord.SecureMessenger"  # Changed from DiscordOpus.SecureMessenger
```

2. Test notifications after renaming (send test message, check Action Center)
3. Search codebase for old app name in all contexts: `grep -r "DiscordOpus" --include="*.py"`

**Format:** AUMID should follow pattern: `CompanyOrApp.ProductName.SubProduct.VersionInfo`
- No strict validation, but alphanumeric + dots recommended
- Example: `Veilcord.SecureMessenger` or `Veilcord.Desktop.v1`

**Warning signs:**
- Notifications work but show wrong app name
- Action Center groups notifications under old name
- Toast icons correct but title wrong

Source: [Custom AUMIDs - Windows-Toasts](https://windows-toasts.readthedocs.io/en/latest/custom_aumid.html)

### Pitfall 7: Not Using PyInstaller `--clean` After Renaming

**What goes wrong:** Developer updates build.spec with new name, reruns `pyinstaller build.spec`. Build succeeds but .exe crashes on startup or shows mixed old/new branding due to stale cached modules.

**Why it happens:** PyInstaller caches compiled Python modules and dependency metadata in `%LOCALAPPDATA%\pyinstaller\` and `build/` directory. Cache is invalidated by .py file changes but NOT by .spec changes or comment updates.

**How to avoid:**
1. Always use `--clean` after major changes:
```bash
pyinstaller --clean build.spec
```

2. `--clean` is required when:
   - Renaming application (spec file changes)
   - Updating dependencies (`pip install --upgrade`)
   - Upgrading PyInstaller itself
   - Strange crashes or import errors

3. `--clean` NOT needed for:
   - Editing .py source files (auto-detected)
   - Changing import statements (auto-detected)

4. Document in build instructions:
```markdown
## Clean Build (after renaming or dependency updates)
pyinstaller --clean build.spec

## Normal Build (source code changes only)
pyinstaller build.spec
```

**Warning signs:**
- .exe contains mix of old and new names
- Import errors for modules that definitely exist
- .exe works on dev machine but not on clean Windows install

**Cache locations:**
- Build temp: `build/` (next to .spec)
- Global cache: `%LOCALAPPDATA%\pyinstaller\`

Source: [PyInstaller --clean Documentation](https://github.com/orgs/pyinstaller/discussions/7116)

## Code Examples

### Example 1: Safe Renaming with Exclusions

```python
# Renaming strategy for src/storage/paths.py

# BEFORE (DiscordOpus):
def get_app_data_dir() -> Path:
    """Get %APPDATA%/DiscordOpus/"""
    appdata = os.getenv('APPDATA')
    if not appdata:
        raise OSError("APPDATA environment variable is not set")

    app_dir = Path(appdata) / 'DiscordOpus'  # User-facing path
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

# AFTER (Veilcord):
def get_app_data_dir() -> Path:
    """Get %APPDATA%/Veilcord/"""  # Updated documentation
    appdata = os.getenv('APPDATA')
    if not appdata:
        raise OSError("APPDATA environment variable is not set")

    app_dir = Path(appdata) / 'Veilcord'  # CHANGED: User-facing path
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir
```

**Migration Note:** Changing this path creates a new data directory. Existing users lose access to contacts/messages. Solution: Migration script to copy data from old path to new path on first run, or keep old path for backward compatibility.

### Example 2: Crypto Constants - DO NOT RENAME

```python
# src/crypto/signal_session.py

# DO NOT RENAME THESE - They are protocol identifiers, not branding
INFO_ROOT_CHAIN = b"DiscordOpus_RootChain_v1"
INFO_MESSAGE_CHAIN = b"DiscordOpus_MessageChain_v1"
INFO_AEAD = b"DiscordOpus_AEAD_v1"
ASSOCIATED_DATA = b"DiscordOpus_v1"
MESSAGE_CHAIN_CONSTANT = b"DiscordOpus_MessageChainConstant"

def x3dh_derive_shared_secret(...):
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"DiscordOpus_X3DH_SharedSecret_v1",  # DO NOT RENAME!
        backend=default_backend()
    ).derive(shared_secret)
```

**Why:** HKDF uses `info` parameter for domain separation. Different info → different derived key → decryption fails. These byte strings are never shown to users, only used internally.

**Verification:**
```python
# Test that old and new builds derive same keys
old_info = b"DiscordOpus_RootChain_v1"
new_info = b"Veilcord_RootChain_v1"  # WRONG!

key_old = HKDF(..., info=old_info).derive(shared_secret)
key_new = HKDF(..., info=new_info).derive(shared_secret)

assert key_old != key_new  # Keys are different - data migration required!
```

Source: [Cryptography HKDF Documentation](https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/)

### Example 3: README with Shields.io Badges

```markdown
# Veilcord

<div align="center">
  <img src="assets/logo.png" alt="Veilcord Logo" width="200"/>

  **Private by design. Encrypted by default.**

  [![License](https://img.shields.io/badge/license-Dual-blue.svg)](LICENSE)
  [![Platform](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows)](https://github.com/mateuszsury/veilcord/releases)
  [![Release](https://img.shields.io/github/v/release/mateuszsury/veilcord)](https://github.com/mateuszsury/veilcord/releases)
  [![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
  [![React](https://img.shields.io/badge/react-19.0-61DAFB?logo=react)](https://react.dev/)
</div>

---

## 🔒 End-to-End Encrypted Messaging

Veilcord is a privacy-focused peer-to-peer messaging application for Windows...
```

**Badges from shields.io:**
- Static: `https://img.shields.io/badge/<LABEL>-<MESSAGE>-<COLOR>`
- Dynamic: `https://img.shields.io/github/v/release/<USER>/<REPO>`
- With logo: Add `?logo=<LOGO_NAME>` (see shields.io for logo list)

**Best practices:**
- Maximum 5-7 badges (License, Platform, Release, Language versions)
- Consistent color scheme
- Link badges to relevant pages (release badge → Releases page)

Source: [Shields.io Documentation](https://shields.io/)

### Example 4: GitHub Release Creation with gh CLI

```bash
#!/bin/bash
# release.sh - Automated release script

set -e  # Exit on error

VERSION="v1.0.0"
CHANGELOG="CHANGELOG.md"

# 1. Ensure clean working directory
if ! git diff-index --quiet HEAD --; then
    echo "Error: Uncommitted changes. Commit first."
    exit 1
fi

# 2. Clean build
echo "Building Veilcord ${VERSION}..."
pyinstaller --clean build.spec

# 3. Create distributable
echo "Creating distribution package..."
cd dist
7z a "Veilcord-${VERSION}-Windows.zip" Veilcord/

# 4. Generate checksums
echo "Generating checksums..."
certutil -hashfile "Veilcord-${VERSION}-Windows.zip" SHA256 > checksums.txt

# 5. Create and push tag
echo "Creating git tag..."
cd ..
git tag -a "${VERSION}" -m "Release ${VERSION}"
git push origin "${VERSION}"

# 6. Create GitHub release
echo "Creating GitHub release..."
gh release create "${VERSION}" \
  --title "Veilcord ${VERSION} - Initial Release" \
  --notes-file "${CHANGELOG}" \
  "dist/Veilcord-${VERSION}-Windows.zip" \
  "dist/checksums.txt"

echo "Release ${VERSION} published successfully!"
echo "Download: https://github.com/mateuszsury/veilcord/releases/tag/${VERSION}"
```

**Manual alternative (GitHub web UI):**
1. Go to repository → Releases → Draft a new release
2. Choose tag: v1.0.0 (create new tag on publish)
3. Release title: Veilcord v1.0.0 - Initial Release
4. Description: Paste from CHANGELOG.md
5. Attach files: Drag Veilcord-v1.0.0-Windows.zip, checksums.txt
6. Publish release

Source: [GitHub CLI Manual](https://cli.github.com/manual/gh_release_create)

### Example 5: Multi-Resolution Icon Creation Workflow

```bash
# Assuming you have a 1024x1024 logo.png

# 1. Export individual sizes (using ImageMagick or similar)
convert logo.png -resize 256x256 logo-256.png
convert logo.png -resize 128x128 logo-128.png
convert logo.png -resize 64x64 logo-64.png
convert logo.png -resize 48x48 logo-48.png
convert logo.png -resize 32x32 logo-32.png
convert logo.png -resize 24x24 logo-24.png
convert logo.png -resize 16x16 logo-16.png

# 2. Manually optimize 16x16 and 32x32 in image editor (simplify details)

# 3. Combine into multi-resolution ICO (using ImageMagick)
convert logo-16.png logo-24.png logo-32.png logo-48.png logo-64.png logo-128.png logo-256.png icon.ico

# 4. Move to assets directory
mv icon.ico assets/icon.ico

# 5. Verify sizes
identify assets/icon.ico
# Output should show all 7 sizes
```

**Web-based alternative (easier):**
1. Visit ConvertICO.com
2. Upload logo.png (1024x1024 recommended)
3. Select sizes: 16, 24, 32, 48, 64, 128, 256
4. Click "Convert ICO"
5. Download multi-resolution icon.ico

**Testing:**
```python
# verify_icon.py - Check ICO contains all sizes
from PIL import Image

ico = Image.open('assets/icon.ico')
print(f"Format: {ico.format}")
print(f"Size: {ico.size}")
print(f"Sizes in ICO: {ico.info.get('sizes', 'Unknown')}")

# Expected output:
# Format: ICO
# Size: (256, 256)
# Sizes in ICO: [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
```

Sources:
- [ConvertICO - PNG to ICO Converter](https://convertico.com/)
- [Icon Size Guidelines](https://blog.icons8.com/articles/choosing-the-right-size-and-format-for-icons/)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual CHANGELOG editing | Automated via conventional commits + semantic-release | 2020-2023 | Reduces human error, enforces consistency, but loses curation |
| Custom LICENSE files | Established templates (MIT, AGPL, dual-license-templates) | 2015-2020 | Legal clarity, GitHub auto-detection, tooling support |
| Manual .ico creation (multiple files) | Multi-resolution single .ico | Windows Vista (2007) | Single file, automatic size selection, better DPI support |
| README text-only | README with badges, screenshots, GIFs | 2015-2020 | SEO, visual appeal, faster comprehension |
| Repository description optional | Description + Topics required for SEO | GitHub search updates 2021-2023 | Discoverability critical for open source adoption |
| GitHub Releases as afterthought | Releases-first workflow with assets | GitHub Releases maturity 2018-2020 | Users expect binary downloads, checksums, changelogs |

**Deprecated/outdated:**
- **Single-size .ico files:** Windows Vista+ supports multi-resolution ICO, no reason to use single-size anymore
- **No .gitignore:** GitHub now prompts for .gitignore during repository creation
- **Manual badge URLs:** shields.io auto-generates badges from GitHub metadata (release, stars, license)
- **Plain text LICENSE:** GitHub auto-detects standard licenses and shows badge, custom text loses this
- **No CODE_OF_CONDUCT:** Required for GitHub "Community Standards" checklist, affects repository discoverability

**Emerging trends (2025-2026):**
- AI-generated README content (GitHub Copilot, ChatGPT) - use with caution, verify accuracy
- Automated release notes from PR titles/commits (GitHub auto-generated release notes)
- Badge fatigue - trend toward fewer, more meaningful badges (license, release, platform only)

## Open Questions

### Question 1: User Data Migration Strategy

**What we know:** Changing `%APPDATA%/DiscordOpus/` to `%APPDATA%/Veilcord/` creates new data directory. Existing users lose contacts, messages, and identity after update.

**What's unclear:** Should we:
- A) Keep old path for backward compatibility (no migration needed, but path doesn't match branding)
- B) Auto-migrate on first run (copy data.db, identity.key to new path, delete old)
- C) Prompt user to choose (manual migration, more control)

**Recommendation:**
- **For v1.0.0 initial release:** Use new path (%APPDATA%/Veilcord/) from the start - no migration needed as no users exist yet
- **For future rebrands:** Implement auto-migration with fallback to old path if copy fails

**Risks:**
- Auto-migration failure leaves user with no data access
- Keeping old path creates confusion (why is Veilcord data in DiscordOpus folder?)

**Validation needed:** Test migration failure scenarios (disk full, permission denied, file in use)

### Question 2: Cryptographic Protocol Versioning

**What we know:** Current crypto constants include version suffix: `b"DiscordOpus_RootChain_v1"`. This suggests future versioning is planned.

**What's unclear:** If protocol needs to change (upgrade from Double Ratchet v1 to v2), how to handle:
- Mixed-version sessions (user A on v1, user B on v2)
- Backward compatibility (can v2 read v1 messages?)
- Protocol negotiation (how do peers agree on version?)

**Recommendation:**
- Document current version (v1) in technical specification
- Plan for protocol negotiation in handshake (exchange supported versions)
- Keep v1 constants unchanged forever (append v2, v3, etc. for future protocols)

**Impact on rebranding:** None for v1.0.0, but establishes precedent that protocol constants are versioned identifiers, not branding.

### Question 3: GitHub Topics Selection Priority

**What we know:** GitHub allows up to 20 topics (tags) for SEO and discoverability. Topics are exact-match in search.

**What's unclear:** Which 20 topics maximize discoverability for target audience (privacy-conscious users, developers)?

**Recommendation:** Start with core technical topics (HIGH confidence):
1. `encryption`
2. `p2p`
3. `messaging`
4. `privacy`
5. `webrtc`
6. `signal-protocol`
7. `e2e-encryption`
8. `desktop-app`
9. `windows`
10. `python`
11. `react`
12. `typescript`
13. `secure-messaging`

Then add niche topics (MEDIUM confidence):
14. `end-to-end-encryption`
15. `peer-to-peer`
16. `voice-chat`
17. `video-call`
18. `file-transfer`
19. `pywebview`
20. `sqlcipher`

**Validation needed:** Research competitor repositories (Signal, Element, Briar) to see which topics drive traffic.

## Sources

### Primary (HIGH confidence)

**Official Documentation:**
- [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) - Changelog format standard
- [Semantic Versioning 2.0.0](https://semver.org/) - Version numbering specification
- [Microsoft Learn - App Icon Construction](https://learn.microsoft.com/en-us/windows/apps/design/style/iconography/app-icon-construction) - Windows icon requirements
- [GitHub Docs - Ignoring Files](https://docs.github.com/en/get-started/getting-started-with-git/ignoring-files) - .gitignore setup
- [GitHub Docs - CONTRIBUTING Guidelines](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors) - Community standards
- [GitHub Docs - Code of Conduct](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/adding-a-code-of-conduct-to-your-project) - CODE_OF_CONDUCT setup
- [PyInstaller 6.18.0 Documentation](https://pyinstaller.org/en/stable/usage.html) - PyInstaller usage and --clean flag
- [Cryptography.io - Key Derivation Functions](https://cryptography.io/en/latest/hazmat/primitives/key-derivation-functions/) - HKDF info parameter semantics

**Standards & Templates:**
- [Shields.io](https://shields.io/) - Badge generation service
- [GitHub gitignore Templates](https://github.com/github/gitignore) - Official .gitignore templates
- [lawndoc/dual-license-templates](https://github.com/lawndoc/dual-license-templates) - Commercial license templates

### Secondary (MEDIUM confidence)

**SEO & Best Practices (2025-2026 guides):**
- [The Ultimate Guide to GitHub SEO for 2025](https://dev.to/infrasity-learning/the-ultimate-guide-to-github-seo-for-2025-38kl) - Repository optimization
- [GitHub Repository Best Practices](https://dev.to/pwd9000/github-repository-best-practices-23ck) - Community standards
- [README Badges GitHub Best Practices](https://daily.dev/blog/readme-badges-github-best-practices) - Badge usage guidelines
- [Git Tags and Releases Best Practices](https://devtoolhub.com/git-tags-releases-best-practices/) - Release workflow

**Icon Creation & Conversion:**
- [ConvertICO - PNG to ICO Converter](https://convertico.com/) - Multi-resolution ICO generation
- [Windows ICO Made Simple](https://creativefreedom.co.uk/icon-designers-blog/windows-ico-made-simple/) - ICO format guide
- [Icon Size Guidelines](https://blog.icons8.com/articles/choosing-the-right-size-and-format-for-icons/) - Required sizes for all platforms

**Licensing & Legal:**
- [Dual Licensing Explained](https://www.termsfeed.com/blog/dual-license-open-source-commercial/) - Dual license model overview
- [FOSSA Blog - Dual-Licensing Models](https://fossa.com/blog/dual-licensing-models-explained/) - Real-world examples

**PyInstaller & Building:**
- [PyInstaller Icon Settings Discussion](https://github.com/orgs/pyinstaller/discussions/8584) - Icon cache issues
- [PyInstaller --clean Documentation](https://github.com/orgs/pyinstaller/discussions/7116) - When to use --clean
- [How to Add Icon to PyInstaller](https://coderslegacy.com/python/add-icon-to-pyinstaller-exe/) - Tutorial with examples

**Windows Notifications:**
- [Windows-Toasts Custom AUMID](https://windows-toasts.readthedocs.io/en/latest/custom_aumid.html) - AUMID configuration
- [Microsoft Learn - Find AUMID](https://learn.microsoft.com/en-us/windows/configuration/store/find-aumid) - AUMID discovery

### Tertiary (LOW confidence)

**Community Resources:**
- [jehna/readme-best-practices](https://github.com/jehna/readme-best-practices) - README templates (community-maintained)
- [matiassingers/awesome-readme](https://github.com/matiassingers/awesome-readme) - Curated README examples
- [GitHub Marketplace - Changelog Actions](https://github.com/marketplace/actions/create-github-releases-based-on-changelog) - Automation tools

**Logo Design Tools (marketing pages, not technical):**
- [Canva Logo Maker](https://www.canva.com/create/logos/) - Free online design tool
- [Adobe Express](https://www.adobe.com/express/create/logo) - Logo templates
- [LOGO.com](https://logo.com/) - AI-powered logo generation

## Metadata

**Confidence breakdown:**
- **Codebase renaming strategy:** HIGH - Clear technical distinction between user-facing identifiers and crypto protocol constants, backed by cryptography documentation
- **Icon creation workflow:** HIGH - Official Microsoft documentation + established tools with millions of users
- **Documentation standards (README, CHANGELOG, CONTRIBUTING):** HIGH - GitHub official docs + widely adopted community standards (Keep a Changelog, shields.io)
- **Dual licensing structure:** MEDIUM - Established pattern with real-world examples, but legal nuances require lawyer review for production use
- **GitHub SEO optimization:** MEDIUM - Based on 2025-2026 blog posts and community guides, not official GitHub documentation
- **PyInstaller --clean flag:** HIGH - Official PyInstaller 6.18.0 documentation and developer discussions
- **User data migration strategy:** LOW - Open question, no established pattern for %APPDATA% path changes in existing deployments

**Research date:** 2026-02-04

**Valid until:** 2026-09-04 (6 months - stable domain with slow-moving standards like Keep a Changelog, Semantic Versioning. GitHub features and SEO algorithms may change faster, re-validate quarterly.)

**Re-research triggers:**
- PyInstaller major version update (breaking changes to icon handling)
- GitHub releases major search algorithm update (affects SEO recommendations)
- Windows 12 release (may change icon format requirements or AUMID handling)
- User reports of icon cache issues not solved by documented workarounds
