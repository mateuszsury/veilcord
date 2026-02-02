import { useState } from 'react';
import { StatusBadge, StatusType } from './Badge';

export interface AvatarProps {
  src?: string;
  name: string;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  status?: StatusType;
  className?: string;
}

const sizeStyles = {
  xs: 'w-6 h-6 text-xs',
  sm: 'w-8 h-8 text-sm',
  md: 'w-10 h-10 text-base',
  lg: 'w-12 h-12 text-lg',
};

const statusPositionStyles = {
  xs: 'bottom-0 right-0',
  sm: 'bottom-0 right-0',
  md: '-bottom-0.5 -right-0.5',
  lg: '-bottom-0.5 -right-0.5',
};

export const Avatar = ({
  src,
  name,
  size = 'md',
  status,
  className = '',
}: AvatarProps) => {
  const [imageError, setImageError] = useState(false);

  const initial = name.charAt(0).toUpperCase();
  const showImage = src && !imageError;

  return (
    <div className={`relative inline-flex ${className}`}>
      <div
        className={`
          ${sizeStyles[size]}
          rounded-full
          flex items-center justify-center
          font-medium
          overflow-hidden
          ${showImage ? '' : 'bg-accent-red/50 text-white'}
        `.trim().replace(/\s+/g, ' ')}
      >
        {showImage ? (
          <img
            src={src}
            alt={name}
            className="w-full h-full object-cover"
            onError={() => setImageError(true)}
          />
        ) : (
          <span>{initial}</span>
        )}
      </div>
      {status && (
        <div className={`absolute ${statusPositionStyles[size]}`}>
          <StatusBadge status={status} />
        </div>
      )}
    </div>
  );
};
