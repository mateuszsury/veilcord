---
phase: 10-ui-ux-redesign
plan: 01
subsystem: ui
tags: [tailwindcss, design-system, css-variables, discord-theme]

# Dependency graph
requires:
  - phase: 09-audio-video-effects
    provides: Complete v1.0 application ready for UI redesign
provides:
  - Discord-inspired design token system via Tailwind v4 @theme
  - 33 CSS custom properties for colors, spacing, z-index, animation
  - Virtual scrolling, icons, and skeleton loader dependencies
affects: [10-02, 10-03, 10-04, 10-05, 10-06, 10-07, 10-08, 10-09, 10-10]

# Tech tracking
tech-stack:
  added: [@tanstack/react-virtual, lucide-react, react-loading-skeleton]
  patterns: [Tailwind v4 @theme directive, CSS custom properties for theming]

key-files:
  created: []
  modified:
    - frontend/src/index.css
    - frontend/package.json
    - frontend/src/components/layout/AppLayout.tsx

key-decisions:
  - "Discord dark palette with softer grays (#1e1f22 primary) instead of pure black"
  - "Blood red accent (#991b1b) for interactive elements - darker, serious, elegant"
  - "Blue links (#00a8fc) like Discord, red only for accents"
  - "5-level z-index scale (base=1 to toast=4000)"

patterns-established:
  - "Color classes: bg-discord-*, text-discord-*, border-accent-*"
  - "Animation variables: --ease-smooth, --ease-snappy, --duration-fast/normal/slow"
  - "Focus ring: red (#dc2626) with 2px width and offset"

# Metrics
duration: 5min
completed: 2026-02-02
---

# Phase 10 Plan 01: Design System Foundation Summary

**Complete Tailwind v4 design system with Discord dark palette, blood red accents, 33 CSS custom properties, and virtual scrolling dependencies**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-02T07:00:00Z
- **Completed:** 2026-02-02T07:05:00Z
- **Tasks:** 3
- **Files modified:** 4 (package.json, package-lock.json, index.css, AppLayout.tsx)

## Accomplishments

- Installed @tanstack/react-virtual, lucide-react, react-loading-skeleton for UI components
- Created comprehensive design system with 33 CSS custom properties
- Replaced cosmic theme with Discord-inspired dark palette
- Added blood red accent system (5 variations) for interactive elements
- Defined status colors, z-index scale, and animation timing
- Added accessibility features (focus ring, prefers-reduced-motion)
- Updated AppLayout to use new design system

## Task Commits

Each task was committed atomically:

1. **Task 1: Install new dependencies** - `40d1921` (chore)
2. **Task 2: Create Discord design system in @theme** - `91681e7` (feat)
3. **Task 3: Update AppLayout to use new design system** - `115f31c` (refactor)

## Files Created/Modified

- `frontend/package.json` - Added 3 new dependencies for UI components
- `frontend/package-lock.json` - Dependency lockfile updated
- `frontend/src/index.css` - Complete design system with @theme directive
- `frontend/src/components/layout/AppLayout.tsx` - Uses bg-discord-bg-primary

## Design System Contents

### Colors (19 properties)

**Discord Backgrounds:**
- `--color-discord-bg-primary`: #1e1f22 (darkest)
- `--color-discord-bg-secondary`: #2b2d31 (panels)
- `--color-discord-bg-tertiary`: #313338 (hover/cards)
- `--color-discord-bg-modifier-hover`: #35373c
- `--color-discord-bg-modifier-active`: #3f4147

**Discord Text:**
- `--color-discord-text-primary`: #f2f3f5 (headings)
- `--color-discord-text-secondary`: #b5bac1 (body)
- `--color-discord-text-muted`: #949ba4 (labels)
- `--color-discord-text-link`: #00a8fc (links)

**Blood Red Accent:**
- `--color-accent-red`: #991b1b
- `--color-accent-red-hover`: #b91c1c
- `--color-accent-red-active`: #7f1d1d
- `--color-accent-red-glow`: rgba(153, 27, 27, 0.3)
- `--color-accent-red-text`: #dc2626

**Status Colors:**
- `--color-status-online`: #23a55a
- `--color-status-away`: #f0b232
- `--color-status-busy`: #f23f42
- `--color-status-offline`: #80848e

### Layout & Spacing (2 properties)

- `--sidebar-icon-width`: 80px
- `--sidebar-channel-width`: 240px

### Z-Index Scale (5 properties)

- `--z-base`: 1
- `--z-dropdown`: 1000
- `--z-modal`: 2000
- `--z-overlay`: 3000
- `--z-toast`: 4000

### Animation (5 properties)

- `--ease-smooth`: cubic-bezier(0.3, 0, 0, 1)
- `--ease-snappy`: cubic-bezier(0.2, 0, 0, 1)
- `--duration-fast`: 150ms
- `--duration-normal`: 200ms
- `--duration-slow`: 300ms

### Focus Ring (2 properties)

- `--ring-width`: 2px
- `--ring-offset`: 2px
- `--color-focus-ring`: #dc2626

## Decisions Made

1. **Discord-like palette with softer grays** - Used #1e1f22 instead of pure black for less eye strain
2. **Blue links, red accents** - Links use #00a8fc like Discord; red reserved for interactive accents
3. **Darker red accent (#991b1b)** - More serious and elegant than bright red
4. **5-level z-index scale** - Prevents z-index wars with clear hierarchy

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Design tokens are available globally via Tailwind utility classes
- Ready for component redesign in plans 02-10
- All subsequent plans can use: `bg-discord-*`, `text-discord-*`, `border-accent-*`

---
*Phase: 10-ui-ux-redesign*
*Completed: 2026-02-02*
