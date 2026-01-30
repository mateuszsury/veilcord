# DiscordOpus

## What This Is

Peer-to-peer komunikator podobny do Discorda — wiadomości tekstowe, rozmowy głosowe i wideo, przesyłanie plików bez limitu — z pełnym szyfrowaniem end-to-end. Aplikacja desktopowa dla Windows (Python + React w webview), pakowana jako pojedynczy plik `.exe`. Tożsamość użytkowników oparta na kluczach kryptograficznych, bez centralnej bazy kont.

## Core Value

Prywatna, w pełni szyfrowana komunikacja P2P bez zaufania do centralnego serwera — użytkownicy kontrolują swoje dane i tożsamość.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Wiadomości tekstowe 1:1 z historią
- [ ] Wiadomości tekstowe grupowe (pokoje)
- [ ] Lista kontaktów z dodawaniem po kluczu publicznym
- [ ] Tworzenie pokojów i zapraszanie przez link/kod
- [ ] Rozmowy głosowe 2+ osób
- [ ] Rozmowy wideo 2+ osób
- [ ] Przesyłanie plików bez limitu rozmiaru
- [ ] Wiadomości głosowe (nagrywanie i wysyłanie audio)
- [ ] Statusy online (dostępny/niedostępny/zajęty)
- [ ] Powiadomienia systemowe Windows
- [ ] Udostępnianie ekranu w rozmowach
- [ ] Pełne szyfrowanie E2E (wiadomości, połączenia, pliki)
- [ ] Lokalna zaszyfrowana historia rozmów
- [ ] Serwer sygnalizacyjny do NAT traversal
- [ ] Pojedynczy plik `.exe` jako instalator/aplikacja

### Out of Scope

- TURN relay server — akceptowane że ~10-20% połączeń za symetrycznym NAT nie zadziała
- Rejestracja email/hasło — tożsamość tylko przez klucze kryptograficzne
- Jasny motyw — tylko ciemny kosmiczny motyw
- Synchronizacja historii między urządzeniami — historia tylko lokalnie
- Aplikacja mobilna — tylko Windows desktop w v1
- Konta zarządzane przez serwer — brak centralnej bazy użytkowników

## Context

**Architektura techniczna:**
- Backend: Python
- Frontend: React z webview (pywebview lub podobne)
- Pakowanie: PyInstaller lub podobne do single `.exe`
- Szyfrowanie: Prawdopodobnie libsodium/NaCl dla E2E
- P2P: WebRTC dla audio/wideo/data channels
- NAT traversal: ICE/STUN + własny serwer sygnalizacyjny

**UI/UX:**
- Ciemny motyw kosmiczny — gwiazdy, animacje, głęboki kosmos
- Layout inspirowany Discordem — sidebar z kontaktami/pokojami, główny panel czatu
- Nowoczesne animacje i przejścia

**Infrastruktura:**
- Serwer sygnalizacyjny na VPS (np. Hetzner)
- Minimalistyczny — tylko wymiana SDP/ICE candidates
- Bez przechowywania wiadomości — tylko sygnalizacja

**Model biznesowy:**
- Freemium — darmowa podstawa, płatne funkcje premium (do określenia)

## Constraints

- **Platform**: Windows only (v1) — inne platformy w przyszłości
- **Packaging**: Single `.exe` — użytkownik pobiera jeden plik
- **Privacy**: Zero-knowledge server — serwer nie widzi treści komunikacji
- **Tech stack**: Python + React — wymaganie użytkownika
- **NAT**: Bez TURN relay — część połączeń może nie działać

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| E2E encryption dla wszystkiego | Prywatność jako core value | — Pending |
| Tożsamość przez klucze krypto | Brak centralnej bazy kont, większa prywatność | — Pending |
| Bez TURN relay | Prostsze, tańsze, akceptowane ograniczenie | — Pending |
| Python + React webview | Wymaganie użytkownika, znajomość technologii | — Pending |
| Tylko ciemny motyw | Spójność UI, kosmiczny design | — Pending |

---
*Last updated: 2026-01-30 after initialization*
