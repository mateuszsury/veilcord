# Veilcord

<div align="center">
  <img src="assets/logo.png" alt="Veilcord Logo" width="200"/>

  **Private by design. Encrypted by default.**

  [![License](https://img.shields.io/badge/License-Dual%20(Personal%2FCommercial)-blue.svg)](LICENSE)
  [![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg)](https://www.microsoft.com/windows)
  [![Python](https://img.shields.io/badge/Python-3.13+-3776AB.svg)](https://www.python.org/)
  [![React](https://img.shields.io/badge/React-19+-61DAFB.svg)](https://react.dev/)
</div>

---

## What is Veilcord?

**Veilcord** is a secure, peer-to-peer encrypted messaging application designed for privacy-conscious users. Unlike traditional messaging apps that route your data through corporate servers, Veilcord connects users directly while employing Signal Protocol end-to-end encryption. Your conversations are truly private—no server can read your messages, and you retain full control of your data and identity.

Built for Windows, Veilcord combines modern communication features with uncompromising security:

- **End-to-End Encryption**: Signal Protocol with Double Ratchet and X3DH key agreement
- **Peer-to-Peer Architecture**: Direct connections between users, no corporate intermediaries
- **Zero-Knowledge Design**: Your encryption keys never leave your device
- **Offline-First Storage**: SQLCipher encrypted database with DPAPI key protection

---

## Features

### Security & Privacy

- **Signal Protocol Encryption**: Industry-standard E2E encryption for all messages and files
- **X3DH Key Agreement**: Perfect forward secrecy with ephemeral keys
- **Double Ratchet**: Self-healing encryption with automatic key rotation
- **SQLCipher Database**: Encrypted local storage with AES-256
- **DPAPI Key Protection**: Windows secure key storage without master passwords
- **Sender Keys**: Efficient group encryption with forward secrecy

### Communication

- **Text Messaging**: Encrypted P2P text chat with reactions, replies, and edits
- **Voice Calls**: High-quality 1-on-1 and group voice calls using Opus codec
- **Video Calls**: WebRTC video with screen sharing support
- **File Transfer**: Send images, videos, documents, and audio files with encryption
- **Voice Messages**: Record and send voice notes with optional effects
- **Group Chats**: Encrypted group messaging with mesh topology for calls

### Audio & Video Effects

- **Noise Cancellation**: AI-powered DeepFilterNet3 and RNNoise for crystal-clear audio
- **Voice Effects**: Real-time pitch shifting, reverb, and creative audio processing
- **Audio Enhancement**: Professional vocal chain with compressor, EQ, de-esser, and gate
- **Virtual Backgrounds**: Blur, image, or animated backgrounds with MediaPipe segmentation
- **Beauty Filters**: Skin smoothing, brightening, and sharpening for video calls
- **Creative Filters**: Grayscale, sepia, vignette, and other artistic video effects
- **AR Overlays**: Face-tracked glasses, hats, and masks powered by MediaPipe
- **Screen Overlays**: Watermarks, borders, and cursor highlighting for screen sharing
- **Hardware Acceleration**: Automatic quality adaptation based on GPU/CPU capabilities

### Modern Interface

- **Discord-Inspired UI**: Clean, familiar layout with icon bar and channel list
- **Dark Theme**: Easy-on-the-eyes design with blood red accents
- **Virtual Scrolling**: Smooth performance with thousands of messages
- **Smooth Animations**: Framer Motion for polished transitions and interactions
- **Responsive Design**: Optimized for various screen sizes and resolutions

---

## Quick Start

### Installation

1. **Download** the latest release from [Releases](https://github.com/mateuszsury/veilcord/releases)
2. **Extract** the ZIP file to your preferred location
3. **Run** `Veilcord.exe`

On first launch, Veilcord will:
- Generate your cryptographic identity (Ed25519 and X25519 key pairs)
- Create an encrypted local database in `%APPDATA%\Veilcord\`
- Connect to the signaling server for peer discovery

### First Launch

1. **Settings Panel**: Click the gear icon to view your public key and configure preferences
2. **Add Contact**: Share your public key with a contact and add theirs in the contacts panel
3. **Start Chatting**: Select a contact to open a secure P2P connection and start messaging

### Connecting to Contacts

**To add a contact:**
1. Open the **Contacts** panel (person icon)
2. Click **Add Contact**
3. Enter their name and public key
4. Click **Save**

**To start a conversation:**
- Click on a contact in the list
- Wait for the P2P connection to establish (green status indicator)
- Start typing and send your first message

---

## How It Works

### Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Veilcord A    │◄───────►│ Signaling Server │◄───────►│   Veilcord B    │
│                 │  STUN   │  (Presence only) │  STUN   │                 │
│  ┌───────────┐  │         └──────────────────┘         │  ┌───────────┐  │
│  │SQLCipher  │  │                                       │  │SQLCipher  │  │
│  │ Database  │  │         ┌──────────────────┐         │  │ Database  │  │
│  └───────────┘  │         │  WebRTC P2P      │         │  └───────────┘  │
│                 │◄───────►│  Data Channel    │◄───────►│                 │
│  Signal Protocol│  E2E    │  (Encrypted)     │  E2E    │  Signal Protocol│
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

### Encryption Overview

1. **Identity Keys**: Each user has Ed25519 (signing) and X25519 (key agreement) keypairs
2. **Key Exchange**: X3DH protocol establishes a shared secret during connection
3. **Message Encryption**: Double Ratchet protocol encrypts each message with unique keys
4. **Group Encryption**: Sender Keys provide efficient group messaging with forward secrecy
5. **Storage Encryption**: SQLCipher encrypts the local database with keys protected by Windows DPAPI

### Signaling Server

The signaling server **only** handles:
- Peer discovery (who is online?)
- WebRTC ICE candidate exchange (how to connect?)
- Presence updates (status changes)

**The server CANNOT:**
- Read your messages
- Access your encryption keys
- Decrypt your files
- Intercept your calls

All communication is peer-to-peer once connected. The signaling server sees encrypted WebRTC metadata only.

---

## Building from Source

### Prerequisites

- **Python 3.13+** (with pip)
- **Node.js 20+** (with npm)
- **ffmpeg** (for video thumbnails): Download from [ffmpeg.org](https://ffmpeg.org/) and add to PATH
- **Git** (optional, for cloning)

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/mateuszsury/veilcord.git
cd veilcord
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install frontend dependencies:**
```bash
cd frontend
npm install
```

4. **Build the frontend:**
```bash
npm run build
```

5. **Return to project root:**
```bash
cd ..
```

### Development

**Run in development mode:**
```bash
python src/main.py
```

**Frontend hot reload (separate terminal):**
```bash
cd frontend
npm run dev
```

**Lint and format:**
```bash
# Python (if using black/flake8)
black src/
flake8 src/

# Frontend
cd frontend
npm run lint
```

### Production Build

**Create a standalone executable:**
```bash
pyinstaller build.spec
```

Output: `dist/Veilcord/Veilcord.exe`

**Test the build:**
```bash
cd dist/Veilcord
Veilcord.exe
```

---

## Security

### Reporting Vulnerabilities

If you discover a security vulnerability, please **DO NOT** open a public issue.

Instead, email security details to: [Your security email here]

We take security seriously and will respond within 48 hours.

### Security Model

**Threats we protect against:**
- Server compromise (P2P + E2E encryption)
- Man-in-the-middle attacks (X3DH key exchange with identity verification)
- Local storage compromise (SQLCipher + DPAPI)
- Message interception (Signal Protocol with perfect forward secrecy)
- Replay attacks (Message sequence numbers and timestamps)

**Limitations:**
- **Symmetric NAT**: ~20-30% of users may fail to connect (no TURN relay)
- **Endpoint Security**: We cannot protect against compromised devices
- **Visual Verification**: Users must manually verify contact public keys
- **Server Availability**: Signaling server required for initial peer discovery

### Trust Model

- **Signaling Server**: Trusted for presence and connection metadata, NOT for messages
- **STUN Servers**: Trusted for NAT traversal assistance (IP addresses visible)
- **Local System**: Trusted (we use Windows DPAPI and filesystem encryption)
- **Contacts**: You choose whom to trust by adding their public keys

---

## Contributing

We welcome contributions! Please read [CONTRIBUTING.md](.github/CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

**Quick links:**
- [Code of Conduct](.github/CODE_OF_CONDUCT.md)
- [Issue Tracker](https://github.com/mateuszsury/veilcord/issues)
- [Development Guide](https://github.com/mateuszsury/veilcord/wiki)

---

## License

Veilcord uses a dual-license model:

- **Personal Use**: Free for individuals and non-commercial use
- **Commercial Use**: Paid license required for businesses and revenue-generating use

See [LICENSE](LICENSE) for full terms.

---

## Acknowledgments

Veilcord is built on the shoulders of giants:

- **Cryptography**: [cryptography](https://cryptography.io/), [DoubleRatchet](https://github.com/Syndace/python-doubleratchet), [X3DH](https://github.com/Syndace/python-x3dh)
- **WebRTC**: [aiortc](https://github.com/aiortc/aiortc)
- **Signal Protocol**: Based on Signal's open specifications
- **Storage**: [SQLCipher](https://www.zetetic.net/sqlcipher/), [pywin32](https://github.com/mhammond/pywin32)
- **Audio/Video**: [sounddevice](https://python-sounddevice.readthedocs.io/), [opencv-python](https://github.com/opencv/opencv-python), [PyOgg](https://github.com/TeamPyOgg/PyOgg)
- **Effects**: [DeepFilterNet](https://github.com/Rikorose/DeepFilterNet), [RNNoise](https://gitlab.xiph.org/xiph/rnnoise), [Pedalboard](https://github.com/spotify/pedalboard), [MediaPipe](https://github.com/google/mediapipe)
- **Frontend**: [React](https://react.dev/), [Vite](https://vitejs.dev/), [Tailwind CSS](https://tailwindcss.com/), [Framer Motion](https://www.framer.com/motion/), [Zustand](https://zustand-demo.pmnd.rs/)
- **Packaging**: [PyInstaller](https://pyinstaller.org/), [pywebview](https://pywebview.flowrl.com/)

Special thanks to the open-source community for making privacy-focused communication possible.

---

<div align="center">
  <strong>Made with privacy in mind.</strong>

  [GitHub](https://github.com/mateuszsury/veilcord) • [Report Bug](https://github.com/mateuszsury/veilcord/issues) • [Request Feature](https://github.com/mateuszsury/veilcord/issues)
</div>
