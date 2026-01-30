# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for DiscordOpus.

IMPORTANT: Use --onedir mode (not --onefile) for faster startup.
--onefile unpacks to temp directory on every launch, adding 3-5 seconds.

Build command:
    pyinstaller build.spec

Output:
    dist/DiscordOpus/DiscordOpus.exe
"""

import sys
from pathlib import Path

# Get absolute path to project root
project_root = Path(SPECPATH).resolve()

block_cipher = None

a = Analysis(
    [str(project_root / 'src' / 'main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include React frontend build
        (str(project_root / 'frontend' / 'dist'), 'frontend/dist'),
    ],
    hiddenimports=[
        # Windows APIs
        'win32crypt',
        'win32api',
        'pywintypes',
        'win32timezone',

        # SQLCipher
        'sqlcipher3',
        'sqlcipher3.dbapi2',

        # PyWebView backends
        'webview',
        'webview.platforms.edgechromium',
        'webview.platforms.winforms',

        # Cryptography internals
        'cryptography',
        'cryptography.hazmat.primitives.asymmetric.ed25519',
        'cryptography.hazmat.primitives.asymmetric.x25519',
        'cryptography.hazmat.primitives.ciphers.aead',
        'cryptography.hazmat.backends.openssl',

        # Argon2
        'argon2',
        'argon2.low_level',
        'argon2._ffi',

        # Our modules
        'src',
        'src.main',
        'src.api',
        'src.api.bridge',
        'src.crypto',
        'src.crypto.identity',
        'src.crypto.fingerprint',
        'src.crypto.backup',
        'src.storage',
        'src.storage.paths',
        'src.storage.dpapi',
        'src.storage.db',
        'src.storage.identity_store',
        'src.storage.contacts',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test frameworks
        'pytest',
        'unittest',
        # Exclude development tools
        'pip',
        'setuptools',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # Use --onedir mode
    name='DiscordOpus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid antivirus false positives
    console=False,  # Windowed application (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'assets' / 'icon.ico') if (project_root / 'assets' / 'icon.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # Disable UPX to avoid antivirus false positives
    upx_exclude=[],
    name='DiscordOpus',
)
