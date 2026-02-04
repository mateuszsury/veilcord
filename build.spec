# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Veilcord.

IMPORTANT: Use --onedir mode (not --onefile) for faster startup.
--onefile unpacks to temp directory on every launch, adding 3-5 seconds.

Build command:
    pyinstaller build.spec

Output:
    dist/Veilcord/Veilcord.exe
"""

import sys
from pathlib import Path

# Get absolute path to project root
project_root = Path(SPECPATH).resolve()

block_cipher = None

# Find PyOgg DLLs
import sys
# In venv, site-packages is at .venv/Lib/site-packages, not Scripts/Lib/site-packages
venv_root = Path(sys.executable).parent.parent
site_packages = venv_root / 'Lib' / 'site-packages'
pyogg_dir = site_packages / 'pyogg'

# PyOgg DLLs to include
pyogg_dlls = [
    (str(pyogg_dir / 'opus.dll'), 'pyogg'),
    (str(pyogg_dir / 'opusenc.dll'), 'pyogg'),
    (str(pyogg_dir / 'opusfile.dll'), 'pyogg'),
    (str(pyogg_dir / 'libogg.dll'), 'pyogg'),
    (str(pyogg_dir / 'libvorbis.dll'), 'pyogg'),
    (str(pyogg_dir / 'libvorbisfile.dll'), 'pyogg'),
    (str(pyogg_dir / 'libFLAC.dll'), 'pyogg'),
]

a = Analysis(
    [str(project_root / 'src' / 'main.py')],
    pathex=[str(project_root)],
    binaries=pyogg_dlls,
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

        # Signal Protocol (E2E encryption)
        'doubleratchet',
        'doubleratchet.recommended',
        'doubleratchet.migrations',
        'x3dh',
        'x3dh.recommended',
        'x3dh.migrations',
        'xeddsa',
        'xeddsa.bindings',
        'pydantic',
        'pydantic_core',
        'annotated_types',

        # Argon2
        'argon2',
        'argon2.low_level',
        'argon2._ffi',

        # PyOgg - voice message encoding
        'pyogg',
        'pyogg.opus',
        'pyogg.opus_encoder',
        'pyogg.opus_decoder',
        'pyogg.opus_file',
        'pyogg.ogg',
        'pyogg.vorbis',
        'pyogg.flac',

        # WebSockets & Networking
        'websockets',
        'websockets.client',
        'websockets.server',
        'websockets.legacy',
        'websockets.legacy.client',
        'websockets.legacy.server',

        # WebRTC (aiortc)
        'aiortc',
        'aiortc.rtcpeerconnection',
        'aiortc.rtcdatachannel',
        'aiortc.mediastreams',
        'aioice',
        'av',
        'pylibsrtp',
        'pyee',
        'pyopenssl',
        'OpenSSL',

        # Audio/Video
        'sounddevice',
        'numpy',
        'cv2',
        'mss',
        'PIL',
        'PIL.Image',
        'Pillow',

        # Audio Effects
        'pedalboard',
        'pyrnnoise',

        # Video/AI
        'mediapipe',
        'mediapipe.python',
        'mediapipe.python.solutions',

        # File transfer
        'ffmpeg',

        # Notifications
        'windows_toasts',
        'winrt',
        'winrt.windows.ui.notifications',

        # Updates (TUF)
        'tuf',
        'tufup',
        'securesystemslib',
        'bsdiff4',
        'pynacl',
        'nacl',

        # HTTP
        'requests',
        'urllib3',
        'certifi',

        # Async I/O
        'aiofiles',
        'asyncio',

        # Misc
        'psutil',
        'colorama',
        'tqdm',

        # Our modules
        'src',
        'src.main',
        'src.api',
        'src.api.bridge',
        'src.crypto',
        'src.crypto.identity',
        'src.crypto.fingerprint',
        'src.crypto.backup',
        'src.crypto.session',
        'src.crypto.ratchet',
        'src.storage',
        'src.storage.paths',
        'src.storage.dpapi',
        'src.storage.db',
        'src.storage.identity_store',
        'src.storage.contacts',
        'src.voice',
        'src.voice.voice_message',
        'src.voice.audio_track',
        'src.voice.call_service',
        'src.voice.device_manager',
        'src.voice.models',
        'src.voice.video_track',
        'src.voice.effects',
        'src.network',
        'src.network.service',
        'src.network.messaging',
        'src.network.signaling_client',
        'src.file_transfer',
        'src.groups',
        'src.notifications',
        'src.updates',
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
    name='Veilcord',
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
    name='Veilcord',
)
