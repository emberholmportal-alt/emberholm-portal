'use client';

import { ReactNode } from 'react';
import { motion } from 'framer-motion';

/**
 * DataBox - Reusable data display box
 * CRT-styled container with amber border and glow on hover
 */

interface DataBoxProps {
  title?: string;
  value?: string | number;
  subtitle?: string;
  icon?: string;
  children?: ReactNode;
  className?: string;
  onClick?: () => void;
  variant?: 'default' | 'highlight' | 'warning' | 'success' | 'error';
  animated?: boolean;
}

const VARIANT_STYLES = {
  default: 'border-amber-dark/50 hover:border-amber',
  highlight: 'border-amber hover:border-amber-bright',
  warning: 'border-amber-dark hover:border-amber',
  success: 'border-green/50 hover:border-green',
  error: 'border-red/50 hover:border-red',
};

const VARIANT_VALUE_COLORS = {
  default: 'text-amber',
  highlight: 'text-amber-bright',
  warning: 'text-amber',
  success: 'text-green',
  error: 'text-red',
};

export function DataBox({
  title,
  value,
  subtitle,
  icon,
  children,
  className = '',
  onClick,
  variant = 'default',
  animated = true,
}: DataBoxProps) {
  const Component = animated ? motion.div : 'div';
  const animationProps = animated
    ? {
        initial: { opacity: 0, y: 10 },
        animate: { opacity: 1, y: 0 },
        whileHover: onClick ? { scale: 1.02 } : undefined,
        whileTap: onClick ? { scale: 0.98 } : undefined,
      }
    : {};

  return (
    <Component
      {...animationProps}
      onClick={onClick}
      className={`
        bg-dark/50 border rounded-lg p-3
        transition-all duration-200
        ${VARIANT_STYLES[variant]}
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
    >
      {/* Header with title/value */}
      {(title || value || icon) && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {icon && <span className="text-lg">{icon}</span>}
            {title && (
              <span className="text-amber-dim text-sm font-medium">{title}</span>
            )}
          </div>
          {value !== undefined && (
            <span className={`font-semibold ${VARIANT_VALUE_COLORS[variant]}`}>
              {value}
            </span>
          )}
        </div>
      )}

      {/* Subtitle */}
      {subtitle && (
        <div className="text-xs text-amber-dark mt-1">{subtitle}</div>
      )}

      {/* Custom children */}
      {children}
    </Component>
  );
}

export default DataBox;
