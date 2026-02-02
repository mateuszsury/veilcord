# Phase 10: UI/UX Redesign - Research

**Researched:** 2026-02-02
**Domain:** React TypeScript UI/UX with Tailwind CSS v4, Discord-inspired layouts
**Confidence:** HIGH

## Summary

This research covers building a production-grade Discord-inspired interface using React 19, TypeScript, Tailwind CSS v4, Zustand for state management, and Framer Motion for animations. The existing application already has these core libraries installed and a cosmic-themed UI that needs to be redesigned with Discord's dark palette (#1e1f22, #2b2d31) and deep blood red accents (#991b1b).

The standard approach for Discord-style layouts involves a CSS Grid-based structure with a narrow icon sidebar (80px), wider channel/chat list panel (200-240px), and flexible main content area. Tailwind CSS v4's new `@theme` directive provides a CSS-first configuration approach that's ideal for design systems, allowing all theme values to be defined as CSS custom properties that can be dynamically adjusted. Framer Motion remains the industry-standard animation library for React, with built-in support for layout animations, reduced motion preferences, and performant transforms.

**Primary recommendation:** Use CSS Grid for the dual-sidebar layout structure, define all design tokens in `@theme` with semantic naming, implement component-level skeleton loading states, use Framer Motion's `motion` components with `prefers-reduced-motion` support, and apply virtual scrolling for message lists using TanStack Virtual.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.0.0+ | UI framework | Current stable version with improved concurrent rendering, already installed |
| TypeScript | 5.7.0+ | Type safety | Industry standard for React projects, provides compile-time error detection |
| Tailwind CSS | 4.0.0+ | Styling framework | New CSS-first configuration with `@theme`, 3-180x faster builds, already installed |
| Zustand | 5.0.0+ | State management | Lightweight (3KB), hook-based, no boilerplate, already installed |
| Framer Motion | 12.0.0+ | Animation library | Industry standard for React animations, tree-shakable, already installed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| TanStack Virtual | 3.x | Virtual scrolling | For message lists with 1000+ messages, handles dynamic heights |
| Lucide React | 0.x | Icon library | 1,500+ icons, tree-shakable, stroke-based design matches Discord aesthetic |
| react-loading-skeleton | 3.x | Loading states | Automatic sizing, component-level skeletons that match content structure |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| TanStack Virtual | React Window | TanStack Virtual has better dynamic height handling, React Window is lighter but less flexible |
| Lucide | Heroicons | Heroicons has only 300 icons but is from Tailwind team, Lucide offers more variety |
| Framer Motion | React Spring | React Spring uses spring physics, Framer Motion has simpler API and better layout animations |

**Installation:**
```bash
npm install @tanstack/react-virtual lucide-react react-loading-skeleton
```

## Architecture Patterns

### Recommended Project Structure
```
src/frontend/
├── components/
│   ├── layout/           # AppLayout, Sidebar, IconBar, ChannelList, MainPanel
│   ├── ui/               # Reusable UI primitives (Button, Avatar, Badge, Tooltip)
│   ├── chat/             # Message components (existing)
│   ├── call/             # Call components (existing)
│   ├── groups/           # Group components (existing)
│   └── settings/         # Settings panels
├── stores/               # Zustand stores (existing)
├── hooks/                # Custom hooks (useVirtualScroll, useAnimation)
├── lib/                  # Utilities (existing)
└── index.css             # Theme definitions with @theme directive
```

### Pattern 1: CSS Grid Layout Structure
**What:** Three-column layout with fixed icon bar, flexible channel list, and main content
**When to use:** Discord-style dual sidebar layouts with icon navigation
**Example:**
```css
/* Source: Modern CSS Layout Techniques guide */
.app-layout {
  display: grid;
  grid-template-columns: 80px 240px 1fr;
  height: 100vh;
  overflow: hidden;
}

.icon-bar {
  grid-column: 1;
  position: sticky;
  top: 0;
  height: 100vh;
}
```

### Pattern 2: Tailwind v4 @theme Design System
**What:** Define all design tokens as CSS custom properties using `@theme` directive
**When to use:** For consistent color, spacing, animation values across entire app
**Example:**
```css
/* Source: Tailwind CSS v4 official blog */
@import "tailwindcss";

@theme {
  /* Discord dark colors */
  --color-discord-bg-primary: #1e1f22;
  --color-discord-bg-secondary: #2b2d31;
  --color-discord-bg-tertiary: #313338;
  --color-discord-text-primary: #f2f3f5;
  --color-discord-text-secondary: #b5bac1;

  /* Blood red accent */
  --color-accent-red: #991b1b;
  --color-accent-red-hover: #b91c1c;
  --color-accent-red-glow: rgba(153, 27, 27, 0.3);

  /* Animation easings */
  --ease-smooth: cubic-bezier(0.3, 0, 0, 1);
  --ease-snappy: cubic-bezier(0.2, 0, 0, 1);

  /* Status colors */
  --color-status-online: #23a55a;
  --color-status-away: #f0b232;
  --color-status-busy: #f23f42;
  --color-status-offline: #80848e;
}
```

### Pattern 3: Zustand Store Organization
**What:** Separate stores by domain with custom hooks for selective subscriptions
**When to use:** Global state management without boilerplate
**Example:**
```typescript
/* Source: Zustand GitHub best practices */
// Store definition
export const useUIStore = create<UIState>((set, get) => ({
  // State
  activeSection: 'home',
  showSettings: false,
  sidebarCollapsed: false,

  // Actions object (never changes, no re-render)
  actions: {
    setActiveSection: (section) => set({ activeSection: section }),
    toggleSettings: () => set({ showSettings: !get().showSettings }),
    toggleSidebar: () => set({ sidebarCollapsed: !get().sidebarCollapsed }),
  },
}));

// Custom hooks with selectors
export const useActiveSection = () => useUIStore(s => s.activeSection);
export const useUIActions = () => useUIStore(s => s.actions);
```

### Pattern 4: Framer Motion Layout Animations
**What:** Use `layout` prop for automatic smooth transitions when layout changes
**When to use:** Panel switches, expanding/collapsing sections, reordering
**Example:**
```typescript
/* Source: Framer Motion documentation & best practices */
import { motion, AnimatePresence } from 'framer-motion';

// Panel transition
<AnimatePresence mode="wait">
  <motion.div
    key={activePanel}
    layout
    initial={{ opacity: 0, x: 20 }}
    animate={{ opacity: 1, x: 0 }}
    exit={{ opacity: 0, x: -20 }}
    transition={{ duration: 0.2, ease: [0.3, 0, 0, 1] }}
  >
    {content}
  </motion.div>
</AnimatePresence>

// Hover effect with red glow
<motion.button
  whileHover={{
    scale: 1.02,
    boxShadow: '0 0 20px var(--color-accent-red-glow)'
  }}
  whileTap={{ scale: 0.98 }}
  transition={{ duration: 0.15 }}
>
```

### Pattern 5: Virtual Scrolling for Message Lists
**What:** Only render visible messages in viewport using TanStack Virtual
**When to use:** Message lists with 100+ messages, variable message heights
**Example:**
```typescript
/* Source: TanStack Virtual documentation */
import { useVirtualizer } from '@tanstack/react-virtual';

function MessageList({ messages }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 60, // Estimate message height
    overscan: 5, // Render 5 extra items for smooth scrolling
  });

  return (
    <div ref={parentRef} className="h-full overflow-auto">
      <div style={{ height: `${virtualizer.getTotalSize()}px` }}>
        {virtualizer.getVirtualItems().map(virtualRow => (
          <div
            key={virtualRow.key}
            data-index={virtualRow.index}
            ref={virtualizer.measureElement}
          >
            <Message message={messages[virtualRow.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Pattern 6: Accessible Animations with prefers-reduced-motion
**What:** Respect user's motion preferences, disable/simplify animations
**When to use:** All animations must support reduced motion for accessibility
**Example:**
```typescript
/* Source: WCAG guidelines and Framer Motion docs */
import { useReducedMotion } from 'framer-motion';

function AnimatedComponent() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      animate={{ opacity: 1 }}
      transition={{
        duration: shouldReduceMotion ? 0 : 0.3,
        ease: 'easeOut'
      }}
    />
  );
}

// CSS approach
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Pattern 7: Component-Level Skeleton Loading
**What:** Each component has a skeleton variant that matches its structure
**When to use:** Initial loads, data fetching, lazy loading sections
**Example:**
```typescript
/* Source: React Loading Skeleton best practices */
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';

function MessageSkeleton() {
  return (
    <div className="flex gap-3 p-4">
      <Skeleton circle width={40} height={40} />
      <div className="flex-1">
        <Skeleton width="30%" height={16} />
        <Skeleton count={2} height={14} className="mt-2" />
      </div>
    </div>
  );
}

// Conditional rendering
function MessageList({ messages, loading }) {
  if (loading) {
    return Array(5).fill(0).map((_, i) => <MessageSkeleton key={i} />);
  }
  return messages.map(msg => <Message key={msg.id} {...msg} />);
}
```

### Anti-Patterns to Avoid
- **Global CSS classes over Tailwind utilities:** Undermines Tailwind's utility-first approach, creates maintenance burden
- **Inline animation timing values:** Use `@theme` custom properties for consistency across app
- **Non-semantic color variable names:** Use `--color-bg-primary` not `--color-gray-900`, enables theme switching
- **Re-rendering entire lists:** Always use virtual scrolling or windowing for lists over 100 items
- **Ignoring layout shift:** Use skeleton loaders that match final content dimensions to prevent CLS
- **Setting arbitrary `z-index` values:** Define z-index scale in `@theme` (e.g., `--z-dropdown: 1000`)

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Virtual scrolling | Custom viewport calculations, manual DOM recycling | TanStack Virtual or React Window | Dynamic heights, overscan, measurement observers, scroll restoration are complex |
| Loading skeletons | Div boxes with gray backgrounds | react-loading-skeleton | Automatic sizing, shimmer effect, accessibility attributes built-in |
| Animation orchestration | setTimeout chains, CSS class toggling | Framer Motion | Layout animations, gesture recognition, exit animations, stagger children |
| Icon components | SVG files, sprite sheets | Lucide React | Tree-shaking, consistent sizing, stroke-width control, 1500+ icons |
| Focus management | Manual focus() calls | Roving tabindex pattern | Keyboard navigation, screen reader support, composite widget patterns |
| Color manipulation | String parsing, RGB math | Tailwind's color-mix() or native oklch() | Perceptual color mixing, automatic contrast, GPU-accelerated |
| Responsive sidebar | useEffect with window.innerWidth | CSS Container Queries (@container) | No JS, no re-renders, more granular than media queries |

**Key insight:** UI/UX patterns have solved edge cases accumulated over years of production use. Discord-style layouts especially have well-documented interaction patterns (hover states, focus rings, keyboard navigation) that are complex to replicate correctly. Use established libraries that handle accessibility, performance, and cross-browser compatibility.

## Common Pitfalls

### Pitfall 1: Layout Shift During Loading
**What goes wrong:** Content jumps when skeletons are replaced with real data, causing poor perceived performance and CLS (Cumulative Layout Shift) metric issues
**Why it happens:** Skeleton dimensions don't match final content, missing height reservations, images without width/height
**How to avoid:**
- Use `react-loading-skeleton` with exact dimensions matching final content
- Reserve space with min-height on container elements
- Provide aspect ratios for images/videos
**Warning signs:** Visible content jumping, scrollbar appearing/disappearing, buttons moving position

### Pitfall 2: Animation Performance with Large Lists
**What goes wrong:** Animating 1000+ list items causes janky scrolling, dropped frames, high CPU usage
**Why it happens:** All items render and animate simultaneously, transform/opacity not GPU-accelerated when combined with other properties
**How to avoid:**
- Only animate visible items (use virtual scrolling first)
- Stick to `transform` and `opacity` for animations (GPU-accelerated)
- Use `will-change: transform` sparingly (only during animation)
- Keep animation duration under 300ms
**Warning signs:** Scroll stuttering, CPU spikes in DevTools, frame rate drops below 60fps

### Pitfall 3: Inconsistent Theme Values
**What goes wrong:** Same color appears different (#2b2d31 vs rgb(43, 45, 49)), spacing inconsistency (12px vs 0.75rem), mismatched animation timing
**Why it happens:** Mixing CSS custom properties, Tailwind utilities, and hardcoded values throughout codebase
**How to avoid:**
- Define ALL values in `@theme` directive once
- Use Tailwind utilities (bg-discord-bg-primary) not inline styles
- Create utility classes for custom animations referencing theme values
- Document theme variables in storybook/documentation
**Warning signs:** Colors look "off," designers complain about inconsistency, duplicate color definitions

### Pitfall 4: Broken Keyboard Navigation
**What goes wrong:** Tab order skips elements, focus invisible, Escape doesn't close modals, arrow keys don't work in lists
**Why it happens:** Missing `tabIndex`, removed focus outlines, no keyboard event handlers, poor DOM order
**How to avoid:**
- Always style `:focus-visible` (never remove outlines without replacement)
- Use semantic HTML (`<button>` not `<div onClick>`)
- Implement roving tabindex for composite widgets (icon bar, settings nav)
- Test with keyboard only (Tab, Enter, Escape, Arrow keys)
**Warning signs:** Keyboard users can't navigate, accessibility audit failures, invisible focus state

### Pitfall 5: Overusing Framer Motion
**What goes wrong:** Every element animates, bundle size increases 50KB+, animations conflict with each other
**Why it happens:** Wrapping every component in `<motion.div>`, not tree-shaking, motion on layout AND children
**How to avoid:**
- Only animate what needs user feedback (hovers, transitions, new messages)
- Import components individually: `import { motion } from 'framer-motion'`
- Use CSS transitions for simple hover effects
- Never animate layout AND all children simultaneously
**Warning signs:** Large bundle size, animation "fights," motion sickness reports

### Pitfall 6: CSS Grid vs Flexbox Confusion
**What goes wrong:** Using flexbox for main layout causes resizing issues, grid for single-axis alignment is overkill
**Why it happens:** Not understanding when to use which layout system
**How to avoid:**
- **Grid:** Page layout (icon bar | channel list | main content), template-based
- **Flexbox:** Component internals (button with icon + text), single-axis alignment
- Rule of thumb: Grid for structure, Flexbox for components
**Warning signs:** `flex-shrink: 0` everywhere, grid with one column/row

### Pitfall 7: Color Contrast Failures
**What goes wrong:** Red text (#991b1b) on dark background (#1e1f22) fails WCAG AA, disabled state invisible
**Why it happens:** Not testing contrast ratios, assuming dark theme is accessible by default
**How to avoid:**
- Test all color combinations with contrast checker (minimum 4.5:1 for normal text)
- Lighten text colors: use #dc2626 instead of #991b1b for text
- Add borders/backgrounds to low-contrast elements
- Use status colors (green/yellow/red/gray) that meet contrast requirements
**Warning signs:** Accessibility audit failures, hard to read text, user complaints

### Pitfall 8: Not Testing with Real Data
**What goes wrong:** Layout breaks with long usernames, message timestamps overlap, scroll behavior incorrect
**Why it happens:** Testing with "John Doe" and "Hello," not "Гро́мовая Шлю́ха-Ци́кло́да" and 10-paragraph messages
**How to avoid:**
- Test with max-length strings (250+ character usernames)
- Test with emoji, RTL languages, accents
- Test with 1000+ messages in list
- Test with slow network (throttle to 3G)
**Warning signs:** Text overflow, broken layouts, missing scrollbars

## Code Examples

Verified patterns from official sources:

### Discord-Style Icon Bar with Zustand State
```typescript
// Source: Zustand patterns + Discord layout research
import { motion } from 'framer-motion';
import { Home, Users, Settings } from 'lucide-react';
import { useUIStore } from '@/stores/ui';

const sections = [
  { id: 'home', icon: Home, label: 'Home' },
  { id: 'contacts', icon: Users, label: 'Contacts' },
  { id: 'groups', icon: Users, label: 'Groups' },
  { id: 'settings', icon: Settings, label: 'Settings' },
] as const;

export function IconBar() {
  const activeSection = useUIStore(s => s.activeSection);
  const { setActiveSection } = useUIStore(s => s.actions);

  return (
    <nav className="w-20 bg-discord-bg-primary flex flex-col items-center py-3 gap-2">
      {sections.map(({ id, icon: Icon, label }) => (
        <motion.button
          key={id}
          onClick={() => setActiveSection(id)}
          className="w-12 h-12 rounded-full flex items-center justify-center relative"
          aria-label={label}
          aria-current={activeSection === id ? 'page' : undefined}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          transition={{ duration: 0.15 }}
        >
          <Icon
            className={activeSection === id ? 'text-accent-red' : 'text-discord-text-secondary'}
            size={24}
            strokeWidth={2}
          />
          {activeSection === id && (
            <motion.div
              layoutId="activeIndicator"
              className="absolute left-0 w-1 h-8 bg-accent-red rounded-r-full"
              transition={{ type: 'spring', stiffness: 500, damping: 30 }}
            />
          )}
        </motion.button>
      ))}
    </nav>
  );
}
```

### Message List with Virtual Scrolling
```typescript
// Source: TanStack Virtual examples
import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface MessageListProps {
  messages: Message[];
  loading?: boolean;
}

export function MessageList({ messages, loading }: MessageListProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80,
    overscan: 10,
  });

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (messages.length > 0) {
      virtualizer.scrollToIndex(messages.length - 1, {
        align: 'end',
        behavior: 'smooth',
      });
    }
  }, [messages.length]);

  if (loading) {
    return (
      <div className="flex-1 overflow-hidden">
        {Array(5).fill(0).map((_, i) => <MessageSkeleton key={i} />)}
      </div>
    );
  }

  return (
    <div ref={parentRef} className="flex-1 overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map(virtualRow => {
          const message = messages[virtualRow.index];
          return (
            <motion.div
              key={message.id}
              data-index={virtualRow.index}
              ref={virtualizer.measureElement}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualRow.start}px)`,
              }}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              <Message message={message} />
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
```

### Responsive Hover Effects with Red Glow
```typescript
// Source: Framer Motion docs + Discord theming research
import { motion } from 'framer-motion';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
}

export function Button({ children, onClick, variant = 'primary' }: ButtonProps) {
  return (
    <motion.button
      onClick={onClick}
      className={`
        px-4 py-2 rounded-lg font-medium
        ${variant === 'primary'
          ? 'bg-accent-red text-white'
          : 'bg-discord-bg-tertiary text-discord-text-primary'}
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-red
      `}
      whileHover={{
        scale: 1.02,
        boxShadow: variant === 'primary'
          ? '0 0 20px var(--color-accent-red-glow)'
          : '0 0 10px rgba(255, 255, 255, 0.1)',
        transition: { duration: 0.15 }
      }}
      whileTap={{ scale: 0.98 }}
    >
      {children}
    </motion.button>
  );
}
```

### Accessible Focus States
```css
/* Source: WCAG focus-visible guidelines */
/* Define in index.css */
@theme {
  --color-focus-ring: #dc2626; /* Lighter red for contrast */
  --ring-width: 2px;
  --ring-offset: 2px;
}

/* Global focus styles */
*:focus-visible {
  outline: var(--ring-width) solid var(--color-focus-ring);
  outline-offset: var(--ring-offset);
}

/* Remove outline for mouse users, keep for keyboard */
*:focus:not(:focus-visible) {
  outline: none;
}

/* Buttons inherit focus from parent but add background */
button:focus-visible {
  outline: var(--ring-width) solid var(--color-focus-ring);
  outline-offset: var(--ring-offset);
  background-color: rgba(220, 38, 38, 0.1);
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| JavaScript config file (tailwind.config.js) | CSS-first config with `@theme` | Tailwind v4.0 (2024) | 3-180x faster builds, runtime theme access, simpler setup |
| Class components | Function components with hooks | React 16.8+ (2019) | Simpler code, better composition, required for modern libraries |
| Redux for all state | Zustand for global, Context for local | 2022-2025 | 90% less boilerplate, smaller bundles, easier to learn |
| rgb() colors | oklch() colors | CSS Color 4 (2023) | More vibrant colors, perceptual uniformity, better gradients |
| Media queries only | Container queries (@container) | CSS Container Queries (2023) | Component-level responsive, no JS, more granular |
| Feather Icons | Lucide React | Lucide fork (2021+) | More icons (1500+), active maintenance, better tree-shaking |
| @keyframes in CSS | Framer Motion layout animations | Framer Motion v2+ | Automatic layout transitions, no manual FLIP animations |

**Deprecated/outdated:**
- **react-spring:** Still works but Framer Motion has better docs, simpler API, and better React 18+ support
- **CSS Modules:** Tailwind v4 makes CSS Modules unnecessary, `@theme` provides scoping
- **Styled Components:** Adds runtime cost, Tailwind utilities are faster and more maintainable
- **Flat design:** 2026 trend is toward subtle depth, shadows, glows (like Discord's hover states)

## Open Questions

Things that couldn't be fully resolved:

1. **Icon Library Choice: Lucide vs Custom SVGs**
   - What we know: Lucide has 1500+ icons, tree-shakable, consistent style
   - What's unclear: Whether custom SVGs for Home/Groups icons would better match Discord aesthetic
   - Recommendation: Start with Lucide, create custom icons only if specific Discord-style icon missing. Lucide's stroke-based design is close to Discord's style.

2. **Virtual Scrolling Threshold**
   - What we know: TanStack Virtual recommended for 100+ messages
   - What's unclear: Exact message count where performance degrades without virtualization
   - Recommendation: Implement virtual scrolling from start for message lists. It's easier than retrofitting, and handles edge cases (10,000+ message history).

3. **Animation Complexity Level**
   - What we know: User wants "moderate polish" animations, not distracting
   - What's unclear: Exact threshold between "polished" and "overdone"
   - Recommendation: Animate state changes (hover, focus, panel switch, new messages) but not static content. Use 150-250ms durations. Get user feedback on first animation pass.

4. **Responsive Breakpoints Strategy**
   - What we know: Discord is primarily desktop app, but needs responsive design
   - What's unclear: Mobile strategy - hide sidebars, collapse to tabs, or different layout entirely?
   - Recommendation: Desktop-first approach (matches Discord), use container queries to collapse sidebars on narrow screens (<1024px). Test mobile as secondary priority.

5. **Loading State Strategy**
   - What we know: Skeleton loaders match content structure, prevent layout shift
   - What's unclear: Should skeletons be separate components or variants of main components?
   - Recommendation: Separate skeleton components per domain (MessageSkeleton, ContactSkeleton) for maintainability. Easier to update independently of main components.

## Sources

### Primary (HIGH confidence)
- [Tailwind CSS v4.0 Official Blog](https://tailwindcss.com/blog/tailwindcss-v4) - @theme directive, CSS-first config, performance improvements
- [Framer Motion Official Documentation](https://motion.dev/docs/react) - Animation patterns, layout animations, accessibility
- [Zustand GitHub Repository](https://github.com/pmndrs/zustand) - State management patterns, selector usage
- [TanStack Virtual Documentation](https://tanstack.com/virtual/latest) - Virtual scrolling implementation
- [WCAG 2.1 Success Criterion 2.3.3](https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions.html) - Animation accessibility requirements
- [W3C Success Criterion 2.4.7](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html) - Focus visible requirements
- [MDN :focus-visible Documentation](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion) - Browser behavior and implementation

### Secondary (MEDIUM confidence)
- [GetStream Discord Clone Tutorial Series](https://getstream.io/blog/discord-clone/) - Discord layout patterns
- [Modern CSS Layout Techniques Guide](https://www.frontendtools.tech/blog/modern-css-layout-techniques-flexbox-grid-subgrid-2025) - CSS Grid vs Flexbox usage
- [Building Ultimate Design System for 2026](https://medium.com/@padmacnu/building-the-ultimate-design-system-a-complete-architecture-guide-for-2026-6dfcab0e9999) - Design system architecture
- [React Architecture Patterns 2026](https://www.geeksforgeeks.org/reactjs/react-architecture-pattern-and-best-practices/) - Component organization
- [BetterDiscord CSS Variables](https://docs.betterdiscord.app/discord/variables) - Discord's actual CSS variable names
- [Lucide vs Heroicons Comparison](https://www.shadcndesign.com/blog/comparing-icon-libraries-shadcn-ui) - Icon library tradeoffs
- [React Loading Skeleton Documentation](https://www.npmjs.com/package/react-loading-skeleton) - Skeleton loader patterns
- [State Management Trends 2025](https://makersden.io/blog/react-state-management-in-2025) - When to use Zustand vs alternatives

### Tertiary (LOW confidence)
- [Discord Color Codes Guide 2025](https://color-wheel-artist.com/discord-color-codes) - Discord hex values (should verify with DevTools)
- [7 UI Pitfalls Mobile Developers Should Avoid 2026](https://www.webpronews.com/7-ui-pitfalls-mobile-app-developers-should-avoid-in-2026/) - General UI mistakes
- [Common UI Redesign Mistakes 2026](https://digitalvolcanoes.com/blogs/dont-make-these-common-website-redesign-mistakes-in-2026) - Strategic planning errors
- Community Discord clones on GitHub - Implementation examples (quality varies)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries officially documented, actively maintained, already installed in project
- Architecture: HIGH - Patterns verified with official docs (Tailwind, Framer Motion, TanStack), Discord layout well-documented
- Pitfalls: MEDIUM - Based on industry articles and best practices, but specific to this use case requires testing
- Code examples: HIGH - All examples from official documentation or verified sources
- Discord color values: MEDIUM - Community sources need verification with DevTools on actual Discord app

**Research date:** 2026-02-02
**Valid until:** 2026-03-02 (30 days - stable domain, but fast-moving ecosystem)

**Notes:**
- Existing cosmic theme (#0a0a0f, #6366f1 accent) will be completely replaced with Discord dark theme
- All existing components (chat, call, groups) remain functional, only visual redesign
- User decisions from CONTEXT.md are locked: Discord dual sidebar, blood red accent, moderate animations
- Focus on production-grade quality: accessibility, performance, consistent design system
