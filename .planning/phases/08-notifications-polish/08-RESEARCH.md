# Phase 8: Notifications & Polish - Research

**Researched:** 2026-01-31
**Domain:** Windows notifications, auto-updating, Python packaging
**Confidence:** MEDIUM

## Summary

This research investigated three primary technical domains for Phase 8: Windows toast notifications with action buttons, secure auto-updating with cryptographic verification, and production packaging with Nuitka to reduce antivirus false positives.

**Windows Notifications:** The Windows-Toasts library (v1.3.1+) provides comprehensive WinRT-based toast notifications with interactive buttons, text inputs, and selection boxes. Critical requirement: custom AUMID registration is mandatory for notification callbacks after relegation to Windows Action Center. The library respects Windows Do Not Disturb/Focus Assist automatically at the OS level—no programmatic control needed.

**Auto-Updating:** Tufup (built on python-tuf) provides secure, cryptographically-verified updates with patch-based bandwidth optimization. It's packaging-agnostic and integrates with PyInstaller by bundling the root.json metadata file. The framework handles metadata signing, patch generation, and secure installation with rollback capabilities.

**Nuitka Packaging:** Nuitka compiles Python to native C code, reducing antivirus false positives from 11/61 (PyInstaller) to 1/60 in real-world tests. Version 2.5.7+ includes pywebview support fixes. The standalone mode is recommended for testing before switching to onefile mode.

**Primary recommendation:** Use Windows-Toasts with InteractableWindowsToaster for notifications, implement tufup for auto-updates during Phase 8, and defer Nuitka migration to a separate packaging phase after core functionality is stable.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Windows-Toasts | 1.3.1+ | Windows toast notifications with actions | Active maintenance, WinRT-based (future-proof), supports all Windows notification features including buttons/inputs, handles interaction callbacks |
| tufup | 0.10.0+ | Secure auto-updater | Built on TUF security framework, packaging-agnostic, cryptographic verification, patch-based updates, active maintenance |
| Nuitka | 2.5.7+ | Python to native compiler | Better AV false positive rate vs PyInstaller, native compilation (not bundling), IP protection, active development |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-tuf | (via tufup) | TUF metadata signing/verification | Automatically used by tufup; manual interaction only for advanced key rotation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Windows-Toasts | win11toast | win11toast has simpler API but less flexible callback system; Windows-Toasts provides full WinRT feature parity |
| Windows-Toasts | toasted | toasted supports all notification elements but smaller community; Windows-Toasts has better documentation |
| tufup | Custom solution | Rolling your own update system risks security vulnerabilities; tufup delegates to security-vetted python-tuf |
| Nuitka | PyInstaller (current) | PyInstaller faster builds but higher false positive rate; defer Nuitka until Phase 8 complete |

**Installation:**
```bash
pip install windows-toasts>=1.3.1
pip install tufup>=0.10.0
pip install nuitka>=2.5.7  # For production packaging phase
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── services/
│   ├── notification_service.py    # Windows toast notification wrapper
│   └── update_service.py          # Tufup integration & update logic
├── ui/
│   └── settings/
│       └── notifications.tsx      # Notification enable/disable UI
└── updater/
    ├── settings.py                # Tufup configuration (paths, URLs)
    └── client.py                  # Update check/download/install logic
```

### Pattern 1: Notification Service Wrapper
**What:** Centralized service for all Windows notifications with AUMID registration and callback routing
**When to use:** All notification scenarios (messages, calls, system events)
**Example:**
```python
# Source: https://windows-toasts.readthedocs.io/en/latest/interactable.html
from windows_toasts import InteractableWindowsToaster, Toast, ToastButton, ToastActivatedEventArgs

class NotificationService:
    def __init__(self, app_name: str, aumid: str):
        self.toaster = InteractableWindowsToaster(aumid)
        self._callbacks = {}

    def show_message_notification(self, sender: str, preview: str, channel_id: str):
        """Show notification for new message with 'Open' action."""
        toast = Toast([f"Message from {sender}", preview])
        toast.AddAction(ToastButton('Open', f'action=open_chat&channel={channel_id}'))

        def on_activated(args: ToastActivatedEventArgs):
            if 'action=open_chat' in args.arguments:
                # Extract channel_id from arguments and emit event
                self._handle_open_chat(args.arguments)

        toast.on_activated = on_activated
        self.toaster.show_toast(toast)

    def show_call_notification(self, caller: str, call_id: str):
        """Show notification for incoming call with Accept/Reject actions."""
        toast = Toast([f"Incoming call from {caller}"])
        toast.AddAction(ToastButton('Accept', f'action=accept&call={call_id}'))
        toast.AddAction(ToastButton('Reject', f'action=reject&call={call_id}'))

        def on_activated(args: ToastActivatedEventArgs):
            if 'action=accept' in args.arguments:
                self._handle_accept_call(call_id)
            elif 'action=reject' in args.arguments:
                self._handle_reject_call(call_id)

        toast.on_activated = on_activated
        self.toaster.show_toast(toast)
```

### Pattern 2: Tufup Update Integration
**What:** Auto-update client that checks/downloads/installs updates on app launch
**When to use:** Application initialization and user-triggered update checks
**Example:**
```python
# Source: https://github.com/dennisvang/tufup-example
from tufup.client import Client
import logging

class UpdateService:
    def __init__(self, app_name: str, current_version: str, update_url: str, metadata_dir: str, install_dir: str):
        self.client = Client(
            app_name=app_name,
            app_version=current_version,
            update_server_url=update_url,
            metadata_dir=metadata_dir,
            target_dir=install_dir
        )

    def check_for_updates(self, include_prereleases: bool = False) -> str | None:
        """Check if updates available. Returns version string or None."""
        try:
            pre = 'rc' if include_prereleases else None
            return self.client.check_for_updates(pre=pre)
        except Exception as e:
            logging.error(f"Update check failed: {e}")
            return None

    def download_and_install_update(self) -> bool:
        """Download and apply available update. Returns success status."""
        try:
            self.client.update()
            return True
        except Exception as e:
            logging.error(f"Update installation failed: {e}")
            return False
```

### Pattern 3: AUMID Registration Script
**What:** One-time registration of custom AUMID for branded notifications
**When to use:** Application first-run or installer
**Example:**
```python
# Source: https://windows-toasts.readthedocs.io/en/latest/custom_aumid.html
# Use the provided register_hkey_aumid.py script
# Command line: python -m windows_toasts.scripts.register_hkey_aumid --help

# After registration, use the custom AUMID in your application:
CUSTOM_AUMID = "YourCompany.DiscordOpus.App"
toaster = InteractableWindowsToaster(CUSTOM_AUMID)
```

### Anti-Patterns to Avoid
- **Manual Do Not Disturb detection:** Windows automatically respects Focus Assist/DND for toast notifications; attempting to detect/control it programmatically via registry is unreliable and unnecessary
- **Bundling root.json separately:** The tufup root metadata MUST be included in the PyInstaller bundle via .spec file; external files will fail verification
- **Using non-InteractableWindowsToaster for buttons:** Regular WindowsToaster doesn't support callbacks; always use InteractableWindowsToaster for interactive notifications
- **Skipping standalone mode testing:** Always test Nuitka compilation with --mode=standalone before switching to --mode=onefile; debugging data file issues in onefile mode is significantly harder

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Auto-updater system | Custom HTTP download + file replacement | tufup | TUF framework prevents replay attacks, MITM attacks, indefinite freeze attacks; handles patch generation, metadata signing, rollback; security-vetted by experts |
| Windows notifications | win32api toast calls | Windows-Toasts library | WinRT bindings are future-proof; library handles AUMID registration, callback routing, Action Center persistence, notification templates |
| Update signing/verification | Custom signature validation | python-tuf (via tufup) | TUF implements defense-in-depth with root/timestamp/snapshot/targets roles; prevents key compromise scenarios; NIST-vetted framework |
| Patch file generation | Manual binary diff | tufup's built-in patch creation | Handles archive naming conventions, version parsing, size optimization (patches vs full archives) |

**Key insight:** Security and reliability are non-negotiable for auto-update systems. Tufup delegates cryptographic security to python-tuf (TUF reference implementation), which is maintained by security professionals and follows NIST guidelines. Custom implementations inevitably miss edge cases (freeze attacks, key rotation, partial download recovery).

## Common Pitfalls

### Pitfall 1: Notification Callbacks Not Firing After Action Center Relegation
**What goes wrong:** Notifications clicked from the Windows Action Center (after initial toast disappears) don't trigger on_activated callbacks; instead they trigger on_dismissed with no arguments.
**Why it happens:** Default AUMID is "Command Prompt" which doesn't properly register activation handlers for Action Center clicks.
**How to avoid:** Register a custom AUMID using the provided register_hkey_aumid.py script before showing interactive notifications.
**Warning signs:** Callbacks work when clicking the toast immediately but fail when clicking from Action Center; on_dismissed fires instead of on_activated.

### Pitfall 2: Tufup Root Metadata Missing in PyInstaller Bundle
**What goes wrong:** Application starts but update checks fail with verification errors or "root metadata not found" exceptions.
**Why it happens:** PyInstaller doesn't automatically bundle non-.py files; root.json must be explicitly added to the .spec file.
**How to avoid:** Add root.json to datas in .spec file: `datas=[('path/to/root.json', 'tufup_metadata')]`
**Warning signs:** Development (unfrozen) updates work but frozen executable update checks fail with metadata errors.

### Pitfall 3: Nuitka Onefile Mode Data File Paths
**What goes wrong:** Application compiled with --mode=onefile can't find data files (icons, config) that worked in standalone mode.
**Why it happens:** Onefile mode extracts to temp directory (e.g., /tmp/onefile_*) instead of current directory; relative paths break.
**How to avoid:** Always test with --mode=standalone first; use sys._MEIPASS or __file__-relative paths for data files; explicitly include data with --include-data-dir flags.
**Warning signs:** Standalone build works perfectly but onefile build has missing icons, config files, or resource loading errors.

### Pitfall 4: Update Installation While App Running
**What goes wrong:** Update installation fails or corrupts files because Windows locks executable files that are currently running.
**Why it happens:** Attempting to replace running executables violates Windows file locking.
**How to avoid:** Download updates during app runtime but defer installation to next launch, or implement "restart to install" workflow with external installer process.
**Warning signs:** Update downloads succeed but installation fails with permission/access denied errors; partial updates leave app broken.

### Pitfall 5: Missing PyQt5 Plugin for pywebview with Nuitka
**What goes wrong:** Nuitka-compiled pywebview application crashes with "ModuleNotFoundError: No module named 'webview.platforms.qt'" when using Qt backend.
**Why it happens:** Nuitka doesn't automatically detect pywebview's Qt backend dependency.
**How to avoid:** Add `--enable-plugin=pyqt5` flag when compiling with Nuitka if pywebview uses Qt backend (or use the default Windows backend which doesn't require this).
**Warning signs:** Application works in development but compiled executable crashes on startup with Qt module import errors.

### Pitfall 6: Notification Arguments String Parsing
**What goes wrong:** Complex notification arguments with special characters fail to parse correctly in callbacks.
**Why it happens:** Arguments are passed as simple strings; URL-encoding or special characters may break naive parsing.
**How to avoid:** Use simple key=value format for arguments (e.g., `action=accept&call=123`); parse with urllib.parse.parse_qs or simple string splitting; avoid spaces and special characters.
**Warning signs:** Some notifications work but others with complex IDs (UUIDs, base64) fail to trigger correct actions.

## Code Examples

Verified patterns from official sources:

### Message Notification with Open Action
```python
# Source: https://windows-toasts.readthedocs.io/en/latest/interactable.html
from windows_toasts import InteractableWindowsToaster, Toast, ToastButton

AUMID = "MyCompany.DiscordOpus.App"  # Must be pre-registered
toaster = InteractableWindowsToaster(AUMID)

def notify_new_message(sender: str, preview: str, channel_id: str):
    toast = Toast([f"Message from {sender}", preview])
    toast.AddAction(ToastButton('Open', f'channel={channel_id}'))

    toast.on_activated = lambda args: open_channel(args.arguments.split('=')[1])
    toaster.show_toast(toast)
```

### Incoming Call Notification with Accept/Reject
```python
# Source: https://windows-toasts.readthedocs.io/en/latest/interactable.html
def notify_incoming_call(caller: str, call_id: str):
    toast = Toast([f"Incoming call from {caller}"])
    toast.AddAction(ToastButton('Accept', f'accept:{call_id}'))
    toast.AddAction(ToastButton('Reject', f'reject:{call_id}'))

    def handle_call_action(args):
        action, cid = args.arguments.split(':')
        if action == 'accept':
            accept_call(cid)
        elif action == 'reject':
            reject_call(cid)

    toast.on_activated = handle_call_action
    toaster.show_toast(toast)
```

### Update Check on Launch
```python
# Source: https://github.com/dennisvang/tufup-example
from tufup.client import Client
import logging

def check_and_prompt_update(current_version: str):
    client = Client(
        app_name="DiscordOpus",
        app_version=current_version,
        update_server_url="https://updates.example.com",
        metadata_dir="./tufup_metadata",
        target_dir="./app"
    )

    try:
        available_version = client.check_for_updates()
        if available_version:
            # Show UI prompt with changelog
            if user_accepts_update():
                client.update()  # Download and install
                # Prompt restart
                restart_application()
    except Exception as e:
        logging.error(f"Update check failed: {e}")
```

### PyInstaller Spec File with Tufup Root Metadata
```python
# Source: https://github.com/dennisvang/tufup-example
# main.spec
a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('tufup_metadata/root.json', 'tufup_metadata'),  # CRITICAL: Include root metadata
    ],
    hiddenimports=['tufup', 'tufup.client'],
    # ... rest of spec
)
```

### Nuitka Compilation with pywebview
```bash
# Source: https://github.com/Nuitka/Nuitka/issues/3251
# Recommended approach for pywebview applications

# First, test with standalone mode
nuitka --standalone \
       --enable-plugin=pyqt5 \
       --include-data-dir=assets=assets \
       --windows-icon-from-ico=app.ico \
       src/main.py

# After verification, switch to onefile
nuitka --onefile \
       --enable-plugin=pyqt5 \
       --include-data-dir=assets=assets \
       --windows-icon-from-ico=app.ico \
       src/main.py
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| win10toast library | Windows-Toasts with WinRT | 2022-2023 | WinRT bindings are future-proof; win10toast uses deprecated pywin32 |
| PyUpdater | tufup | 2021 (PyUpdater archived) | PyUpdater no longer maintained; tufup uses vetted python-tuf security framework |
| PyInstaller only | Nuitka for production | 2024-2025 | Nuitka reduces AV false positives from ~18% to ~1.6% detection rate |
| Manual DND detection | Rely on OS behavior | Always (Windows 10+) | Windows automatically respects Focus Assist for all toast notifications |

**Deprecated/outdated:**
- **win10toast, win10toast-persist, win10toast-click**: Abandoned projects using pywin32 instead of WinRT; use Windows-Toasts instead
- **PyUpdater**: Archived in 2021; no security updates; migrate to tufup
- **Manual notification duration in seconds**: WinRT only supports short/long duration presets (not pywin32's arbitrary seconds)

## Open Questions

Things that couldn't be fully resolved:

1. **Nuitka compilation with aiortc native dependencies**
   - What we know: Nuitka 2.5.7+ supports pywebview; cryptography package works with proper flags
   - What's unclear: aiortc has native WebRTC dependencies (libvpx, opus) that may require special Nuitka configuration
   - Recommendation: Test Nuitka compilation early in Phase 8; if aiortc issues arise, defer Nuitka migration to separate phase and continue using PyInstaller for Phase 8 delivery

2. **Update server hosting and CDN configuration**
   - What we know: Tufup works with any HTTP server; example uses Python's built-in http.server
   - What's unclear: Production hosting strategy (AWS S3, Azure Blob, GitHub Releases, custom server)
   - Recommendation: Start with simple HTTP server for development; finalize production hosting during PKG-03 implementation

3. **Notification icon customization per notification type**
   - What we know: AUMID registration sets application-wide icon; toast notifications can include hero images
   - What's unclear: Can individual toasts override the AUMID icon for different notification types (message vs call)?
   - Recommendation: Use single AUMID icon for app identity; add hero images to toasts for visual differentiation if needed

4. **Update rollback mechanism**
   - What we know: Tufup supports patch-based updates; can detect verification failures
   - What's unclear: Automatic rollback process if update installation corrupts app
   - Recommendation: Implement backup of current version before update installation; manual rollback instructions for users

## Sources

### Primary (HIGH confidence)
- Windows-Toasts documentation: https://windows-toasts.readthedocs.io/en/latest/
- Windows-Toasts GitHub: https://github.com/DatGuy1/Windows-Toasts
- Windows-Toasts Interactable Toasts: https://windows-toasts.readthedocs.io/en/latest/interactable.html
- Windows-Toasts Custom AUMID: https://windows-toasts.readthedocs.io/en/latest/custom_aumid.html
- Tufup GitHub repository: https://github.com/dennisvang/tufup
- Tufup example repository: https://github.com/dennisvang/tufup-example
- Nuitka user documentation: https://nuitka.net/user-documentation/
- Nuitka tips: https://nuitka.net/user-documentation/tips.html

### Secondary (MEDIUM confidence)
- Windows-Toasts PyPI: https://pypi.org/project/Windows-Toasts/
- Tufup PyPI: https://pypi.org/project/tufup/
- Nuitka GitHub issues (pywebview support): https://github.com/Nuitka/Nuitka/issues/3251
- Nuitka vs PyInstaller AV comparison: https://dev.to/weisshufer/from-pyinstaller-to-nuitka-convert-python-to-exe-without-false-positives-19jf
- Python toast notifications tutorial: https://tongere.hashnode.dev/python-windows-toast-notifications

### Tertiary (LOW confidence)
- win11toast library (alternative, not recommended): https://pypi.org/project/win11toast/
- toasted library (alternative, smaller community): https://github.com/ysfchn/toasted
- Windows Focus Assist general info: https://support.microsoft.com/en-us/windows/notifications-and-do-not-disturb-in-windows-feeca47f-0baf-5680-16f0-8801db1a8466

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official documentation confirms Windows-Toasts and tufup are actively maintained with clear APIs; Nuitka AV benefits verified in real-world tests
- Architecture: MEDIUM - Patterns based on official examples but not directly tested with this codebase's specific stack (pywebview + aiortc)
- Pitfalls: MEDIUM - Compiled from GitHub issues and documentation warnings; AUMID requirement verified in official docs; Nuitka onefile behavior documented in issue tracker

**Research date:** 2026-01-31
**Valid until:** 2026-03-15 (45 days - stable ecosystem, quarterly release cycles for these libraries)
