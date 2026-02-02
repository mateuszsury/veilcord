/**
 * IconBar - Discord-style narrow icon sidebar (80px width)
 *
 * Provides primary navigation between sections:
 * - Home: Welcome/branding panel
 * - Contacts: Contact list
 * - Groups: Group list
 * - Settings: Settings panel
 *
 * Features:
 * - Active indicator pill with smooth layoutId animation
 * - Hover/tap animations using Framer Motion
 * - Accessibility: aria-label, aria-current, focus-visible ring
 * - UserPanel at bottom with avatar and audio controls
 */

import { motion } from 'framer-motion';
import { Home, Users, MessageSquare, Settings, type LucideIcon } from 'lucide-react';
import { useUIStore } from '@/stores/ui';
import { UserPanel } from './UserPanel';

type Section = 'home' | 'contacts' | 'groups' | 'settings';

interface SectionConfig {
  id: Section;
  icon: LucideIcon;
  label: string;
}

const sections: readonly SectionConfig[] = [
  { id: 'home', icon: Home, label: 'Home' },
  { id: 'contacts', icon: Users, label: 'Contacts' },
  { id: 'groups', icon: MessageSquare, label: 'Groups' },
  { id: 'settings', icon: Settings, label: 'Settings' },
];

/**
 * Spring animation config for the active indicator pill
 * Uses high stiffness for snappy feel, moderate damping to prevent overshoot
 */
const indicatorSpring = {
  type: 'spring' as const,
  stiffness: 500,
  damping: 30,
};

/**
 * Scale animations for icon buttons
 */
const buttonAnimations = {
  hover: { scale: 1.1 },
  tap: { scale: 0.95 },
};

export function IconBar() {
  const activeSection = useUIStore((s) => s.activeSection);
  const setActiveSection = useUIStore((s) => s.setActiveSection);

  return (
    <nav className="w-20 h-full bg-discord-bg-primary flex flex-col items-center py-3 gap-2">
      {sections.map(({ id, icon: Icon, label }) => {
        const isActive = activeSection === id;

        return (
          <div key={id} className="relative flex items-center justify-center">
            {/* Active indicator pill on left */}
            {/* Active indicator pill - animates between icons using layoutId */}
            {isActive && (
              <motion.div
                layoutId="activeIndicator"
                className="absolute left-0 w-1 h-8 bg-accent-red rounded-r-full"
                transition={indicatorSpring}
              />
            )}

            {/* Icon button with hover/tap animations */}
            <motion.button
              onClick={() => setActiveSection(id)}
              className={`
                w-12 h-12
                flex items-center justify-center
                rounded-2xl
                transition-colors
                focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-red focus-visible:ring-offset-2 focus-visible:ring-offset-discord-bg-primary
                ${
                  isActive
                    ? 'bg-accent-red text-white'
                    : 'text-discord-text-secondary hover:bg-discord-bg-tertiary hover:text-discord-text-primary'
                }
              `.trim().replace(/\s+/g, ' ')}
              whileHover={buttonAnimations.hover}
              whileTap={buttonAnimations.tap}
              aria-label={label}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon className="w-6 h-6" />
            </motion.button>
          </div>
        );
      })}

      {/* Spacer to push UserPanel to bottom */}
      <div className="flex-1" />

      {/* UserPanel at bottom */}
      <UserPanel />
    </nav>
  );
}
