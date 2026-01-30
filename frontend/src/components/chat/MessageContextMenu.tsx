/**
 * Context menu for message actions.
 *
 * Shows on right-click with options:
 * - Add Reaction (opens ReactionPicker)
 * - Copy
 * - Edit (own messages only)
 * - Delete (own messages only)
 */

import { useState } from 'react';
import { ReactionPicker } from './ReactionPicker';

interface MessageContextMenuProps {
  x: number;
  y: number;
  isOwn: boolean;
  onCopy: () => void;
  onReact: (emoji: string) => void;
  onEdit?: () => void;
  onDelete?: () => void;
  onClose: () => void;
}

// Inline SVG icons to match project pattern
function CopyIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
  );
}

function SmileIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <path d="M8 14s1.5 2 4 2 4-2 4-2" />
      <line x1="9" y1="9" x2="9.01" y2="9" />
      <line x1="15" y1="9" x2="15.01" y2="9" />
    </svg>
  );
}

function EditIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="3,6 5,6 21,6" />
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    </svg>
  );
}

export function MessageContextMenu({
  x,
  y,
  isOwn,
  onCopy,
  onReact,
  onEdit,
  onDelete,
  onClose,
}: MessageContextMenuProps) {
  const [showReactionPicker, setShowReactionPicker] = useState(false);

  const handleReactionSelect = (emoji: string) => {
    onReact(emoji);
    onClose();
  };

  const menuItems = [
    {
      label: 'Add Reaction',
      icon: <SmileIcon />,
      onClick: () => setShowReactionPicker(!showReactionPicker),
      show: true,
    },
    {
      label: 'Copy',
      icon: <CopyIcon />,
      onClick: () => {
        onCopy();
        onClose();
      },
      show: true,
    },
    {
      label: 'Edit',
      icon: <EditIcon />,
      onClick: () => {
        onEdit?.();
        onClose();
      },
      show: isOwn && !!onEdit,
    },
    {
      label: 'Delete',
      icon: <TrashIcon />,
      onClick: () => {
        onDelete?.();
        onClose();
      },
      show: isOwn && !!onDelete,
      danger: true,
    },
  ];

  // Adjust position to keep menu in viewport
  const adjustedX = Math.min(x, window.innerWidth - 200);
  const adjustedY = Math.min(y, window.innerHeight - 200);

  return (
    <>
      {/* Backdrop to capture clicks outside */}
      <div
        className="fixed inset-0 z-40"
        onClick={onClose}
        onContextMenu={(e) => {
          e.preventDefault();
          onClose();
        }}
      />

      {/* Context menu */}
      <div
        className="fixed z-50 min-w-[160px] py-1 bg-cosmic-elevated rounded-lg shadow-xl border border-cosmic-border"
        style={{ left: adjustedX, top: adjustedY }}
      >
        {showReactionPicker && (
          <div className="absolute bottom-full mb-2 left-0">
            <ReactionPicker onSelect={handleReactionSelect} onClose={onClose} />
          </div>
        )}

        {menuItems
          .filter((item) => item.show)
          .map((item) => (
            <button
              key={item.label}
              type="button"
              onClick={item.onClick}
              className={`w-full flex items-center gap-3 px-4 py-2 text-sm transition-colors ${
                item.danger
                  ? 'text-red-400 hover:bg-red-500/10'
                  : 'text-cosmic-text hover:bg-cosmic-hover'
              }`}
            >
              <span className="opacity-70">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
      </div>
    </>
  );
}
