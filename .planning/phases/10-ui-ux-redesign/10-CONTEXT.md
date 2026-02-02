# Phase 10: UI/UX Redesign - Context

**Gathered:** 2026-02-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete rebuild of the user interface with production-grade quality. Discord-inspired layout in black-red color scheme, smooth animations, logical grouping, and exceptional UX. All existing features remain functional - this phase is purely visual/interaction redesign.

</domain>

<decisions>
## Implementation Decisions

### Layout Architecture
- **Discord-style dual sidebar:** Narrow icon bar (left) + wider channel/chat list panel
- **Icon bar contents:** Home + Contacts + Groups + Settings (four main sections, each switches the channel list)
- **User panel location:** Bottom of icon bar (Discord style) - avatar + status + mic/speaker controls
- **Chat area structure:** Header + messages + input (Discord pattern) - contact/group info header, scrollable messages, input at bottom

### Color & Visual System
- **Background colors:** Discord dark palette (#1e1f22 / #2b2d31) - softer dark gray, easier on eyes
- **Red accent:** Deep blood red (#991b1b) - darker, serious, elegant
- **Red usage:** Accent only - buttons, links, active states. Minimal red, mostly on interactive elements
- **Status colors:** Standard system (green=online, yellow=away, red=busy, gray=offline) - familiar, red matches theme for busy

### Animations & Transitions
- **Motion level:** Moderate polish - noticeable but not distracting, adds life to UI
- **Panel transitions:** Mixed - slides for navigation (sidebar switches), fades for content changes
- **Hover effects:** Red-tinted glow/shadow appears on hover
- **Message entrance:** Slide up + fade - new messages slide up smoothly into view

### Component Grouping
- **Settings organization:** Discord-style - left nav with categories, right panel shows settings content
- **Effect controls during calls:** Both - quick toggles in toolbar + expandable full panel. Icons for noise cancellation, filters, etc. in call controls, plus expand button for full controls
- **Call controls:** Center bottom bar (Discord/Zoom style) - mute, video, screen share, effects, end call in row
- **File transfers:** Both - inline preview in chat + dedicated panel for management. Chat shows mini progress, panel shows full details

### Claude's Discretion
- Exact spacing and typography scale
- Loading skeleton designs
- Error state styling
- Empty state illustrations
- Icon choices (library or custom)
- Exact animation timing curves
- Responsive breakpoints

</decisions>

<specifics>
## Specific Ideas

- Discord as primary reference - users familiar with this layout
- Deep blood red (#991b1b) for elegant, serious feel - not bright/playful
- Red-tinted glow on hover gives cohesive themed interaction
- Messages should feel alive with slide+fade entrance
- Effects panel should be easily accessible during calls without cluttering the view
- File transfers need visibility both in context (chat) and as overview (panel)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 10-ui-ux-redesign*
*Context gathered: 2026-02-02*
