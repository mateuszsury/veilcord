/**
 * File upload button component.
 *
 * Features:
 * - Paperclip button that opens native file dialog
 * - Disabled when not connected
 */

import { useTransferStore } from '@/stores/transfers';

interface FileUploadProps {
  contactId: number;
  disabled?: boolean;
}

export function FileUpload({ contactId, disabled = false }: FileUploadProps) {
  const sendFile = useTransferStore((state) => state.sendFile);

  const handleClick = () => {
    if (disabled) return;
    sendFile(contactId);
  };

  return (
    <button
      onClick={handleClick}
      disabled={disabled}
      className="p-3 rounded-xl text-discord-text-muted hover:text-accent-red-text hover:bg-discord-bg-secondary
                 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      title="Send file"
    >
      {/* Paperclip icon */}
      <svg
        className="w-5 h-5"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
        />
      </svg>
    </button>
  );
}
