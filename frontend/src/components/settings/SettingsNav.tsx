/**
 * Settings navigation sidebar component.
 *
 * Discord-style left navigation with categories.
 * Each category shows an icon and label.
 * Active category is highlighted.
 */

import {
  User,
  Wifi,
  Search,
  Mic,
  Video,
  Bell,
  Download,
  Users,
  AlertTriangle,
} from 'lucide-react';

const categories = [
  { id: 'identity', label: 'My Account', icon: User },
  { id: 'network', label: 'Network', icon: Wifi },
  { id: 'discovery', label: 'Discovery', icon: Search },
  { id: 'audio', label: 'Voice & Audio', icon: Mic },
  { id: 'video', label: 'Video', icon: Video },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'backup', label: 'Backup', icon: Download },
  { id: 'contacts', label: 'Contacts', icon: Users },
] as const;

const dangerCategory = { id: 'danger', label: 'Danger Zone', icon: AlertTriangle } as const;

interface SettingsNavProps {
  activeCategory: string;
  onCategoryChange: (category: string) => void;
}

export function SettingsNav({ activeCategory, onCategoryChange }: SettingsNavProps) {
  return (
    <nav className="w-52 h-full bg-discord-bg-secondary py-4 flex flex-col">
      {/* Main categories */}
      <div className="space-y-0.5">
        {categories.map((category) => {
          const Icon = category.icon;
          const isActive = activeCategory === category.id;

          return (
            <button
              key={category.id}
              onClick={() => onCategoryChange(category.id)}
              className={`
                w-full flex items-center gap-3 px-3 py-2 mx-2 rounded-md
                transition-colors duration-150
                ${isActive
                  ? 'bg-discord-bg-modifier-active text-discord-text-primary'
                  : 'text-discord-text-secondary hover:bg-discord-bg-modifier-hover hover:text-discord-text-primary'
                }
              `}
              style={{ width: 'calc(100% - 16px)' }}
            >
              <Icon size={20} />
              <span className="text-sm font-medium">{category.label}</span>
            </button>
          );
        })}
      </div>

      {/* Divider */}
      <div className="h-px bg-discord-bg-tertiary mx-4 my-4" />

      {/* Danger Zone - separate section */}
      <div>
        <button
          onClick={() => onCategoryChange(dangerCategory.id)}
          className={`
            w-full flex items-center gap-3 px-3 py-2 mx-2 rounded-md
            transition-colors duration-150
            ${activeCategory === dangerCategory.id
              ? 'bg-discord-bg-modifier-active text-discord-text-primary'
              : 'text-status-busy hover:bg-discord-bg-modifier-hover'
            }
          `}
          style={{ width: 'calc(100% - 16px)' }}
        >
          <dangerCategory.icon size={20} />
          <span className="text-sm font-medium">{dangerCategory.label}</span>
        </button>
      </div>
    </nav>
  );
}
