import { motion, HTMLMotionProps } from 'framer-motion';
import { forwardRef } from 'react';

export interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'children'> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}

const variantStyles = {
  primary: 'bg-accent-red text-white hover:bg-accent-red-hover',
  secondary: 'bg-discord-bg-tertiary text-discord-text-primary hover:bg-discord-bg-modifier-hover',
  ghost: 'bg-transparent text-discord-text-secondary hover:bg-discord-bg-modifier-hover hover:text-discord-text-primary',
  danger: 'bg-status-busy text-white hover:bg-status-busy/80',
};

const sizeStyles = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-lg',
};

const variantHoverEffects = {
  primary: {
    scale: 1.02,
    boxShadow: '0 0 20px var(--color-accent-red-glow)',
  },
  secondary: {
    scale: 1.02,
    boxShadow: '0 0 12px rgba(49, 51, 56, 0.5)',
  },
  ghost: {
    scale: 1.02,
  },
  danger: {
    scale: 1.02,
    boxShadow: '0 0 20px rgba(237, 66, 69, 0.3)',
  },
};

const LoadingSpinner = () => (
  <svg
    className="animate-spin -ml-1 mr-2 h-4 w-4"
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
  >
    <circle
      className="opacity-25"
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      strokeWidth="4"
    />
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    />
  </svg>
);

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      disabled,
      children,
      className = '',
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <motion.button
        ref={ref}
        className={`
          inline-flex items-center justify-center
          font-medium rounded-md
          transition-colors
          focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-red focus-visible:ring-offset-2 focus-visible:ring-offset-discord-bg-primary
          ${variantStyles[variant]}
          ${sizeStyles[size]}
          ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          ${className}
        `.trim().replace(/\s+/g, ' ')}
        disabled={isDisabled}
        whileHover={isDisabled ? undefined : variantHoverEffects[variant]}
        whileTap={isDisabled ? undefined : { scale: 0.98 }}
        transition={{ duration: 0.15 }}
        {...props}
      >
        {loading && <LoadingSpinner />}
        {children}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';
