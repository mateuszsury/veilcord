export type StatusType = 'online' | 'away' | 'busy' | 'offline';

export interface BadgeProps {
  variant?: 'default' | 'accent' | 'success' | 'warning' | 'error';
  children: React.ReactNode;
  className?: string;
}

export interface StatusBadgeProps {
  status: StatusType;
  className?: string;
}

const badgeVariantStyles = {
  default: 'bg-discord-bg-tertiary text-discord-text-secondary',
  accent: 'bg-accent-red text-white',
  success: 'bg-status-online text-white',
  warning: 'bg-status-away text-black',
  error: 'bg-status-busy text-white',
};

const statusStyles = {
  online: 'bg-status-online',
  away: 'bg-status-away',
  busy: 'bg-status-busy',
  offline: 'bg-status-offline',
};

export const Badge = ({
  variant = 'default',
  children,
  className = '',
}: BadgeProps) => {
  return (
    <span
      className={`
        inline-flex items-center justify-center
        px-2 py-0.5
        text-xs font-medium
        rounded-full
        ${badgeVariantStyles[variant]}
        ${className}
      `.trim().replace(/\s+/g, ' ')}
    >
      {children}
    </span>
  );
};

export const StatusBadge = ({ status, className = '' }: StatusBadgeProps) => {
  return (
    <span
      className={`
        block
        w-3 h-3
        rounded-full
        border-2 border-discord-bg-secondary
        ${statusStyles[status]}
        ${className}
      `.trim().replace(/\s+/g, ' ')}
      aria-label={`Status: ${status}`}
    />
  );
};
