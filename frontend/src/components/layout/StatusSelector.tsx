import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNetworkStore } from '@/stores/network';
import type { UserStatus } from '@/lib/pywebview';

const STATUS_OPTIONS: { value: UserStatus; label: string; color: string }[] = [
  { value: 'online', label: 'Online', color: 'bg-green-500' },
  { value: 'away', label: 'Away', color: 'bg-yellow-500' },
  { value: 'busy', label: 'Busy', color: 'bg-red-500' },
  { value: 'invisible', label: 'Invisible', color: 'bg-gray-500' },
];

function getStatusColor(status: UserStatus): string {
  const option = STATUS_OPTIONS.find((o) => o.value === status);
  return option?.color ?? 'bg-gray-500';
}

function getStatusLabel(status: UserStatus): string {
  const option = STATUS_OPTIONS.find((o) => o.value === status);
  return option?.label ?? status;
}

export function StatusSelector() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const userStatus = useNetworkStore((s) => s.userStatus);
  const updateUserStatus = useNetworkStore((s) => s.updateUserStatus);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleStatusChange = async (status: UserStatus) => {
    await updateUserStatus(status);
    setIsOpen(false);
  };

  return (
    <div ref={dropdownRef} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-2 py-1 rounded-md hover:bg-discord-bg-modifier-hover transition-colors"
      >
        <span className={`w-2.5 h-2.5 rounded-full ${getStatusColor(userStatus)}`} />
        <span className="text-sm text-discord-text-primary">{getStatusLabel(userStatus)}</span>
        <svg
          className={`w-4 h-4 text-discord-text-muted transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full left-0 mt-1 w-36 bg-discord-bg-secondary border border-discord-bg-tertiary rounded-md shadow-lg z-50"
          >
            {STATUS_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => handleStatusChange(option.value)}
                className={`w-full flex items-center gap-2 px-3 py-2 text-left text-sm hover:bg-discord-bg-modifier-hover transition-colors first:rounded-t-md last:rounded-b-md ${
                  userStatus === option.value ? 'text-accent-red-text' : 'text-discord-text-primary'
                }`}
              >
                <span className={`w-2.5 h-2.5 rounded-full ${option.color}`} />
                <span>{option.label}</span>
                {userStatus === option.value && (
                  <svg className="w-4 h-4 ml-auto" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
