'use client';

import { motion } from 'framer-motion';

/**
 * StatDisplay - Grid of stats with icons
 * CRT-styled with glowing icons
 */

interface Stat {
  label: string;
  value: string | number;
  icon?: string;
  color?: 'amber' | 'green' | 'red' | 'cyan' | 'purple';
}

interface StatDisplayProps {
  stats: Stat[];
  columns?: 2 | 3 | 4;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'compact' | 'card';
  className?: string;
}

const COLOR_CLASSES = {
  amber: 'text-amber',
  green: 'text-green',
  red: 'text-red',
  cyan: 'text-cyan',
  purple: 'text-purple-400',
};

export function StatDisplay({
  stats,
  columns = 2,
  size = 'md',
  variant = 'default',
  className = '',
}: StatDisplayProps) {
  const columnClasses = {
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
  };

  const sizeClasses = {
    sm: { icon: 'text-lg', value: 'text-sm', label: 'text-xs' },
    md: { icon: 'text-xl', value: 'text-base', label: 'text-xs' },
    lg: { icon: 'text-2xl', value: 'text-lg', label: 'text-sm' },
  };

  const sizes = sizeClasses[size];

  if (variant === 'compact') {
    return (
      <div className={`flex flex-wrap gap-3 ${className}`}>
        {stats.map((stat, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
            className="flex items-center gap-1.5"
          >
            {stat.icon && (
              <span className={`${sizes.icon} ${COLOR_CLASSES[stat.color || 'amber']}`}>
                {stat.icon}
              </span>
            )}
            <span className={`${sizes.value} font-semibold ${COLOR_CLASSES[stat.color || 'amber']}`}>
              {stat.value}
            </span>
            <span className={`${sizes.label} text-amber-dim`}>{stat.label}</span>
          </motion.div>
        ))}
      </div>
    );
  }

  if (variant === 'card') {
    return (
      <div className={`grid ${columnClasses[columns]} gap-2 ${className}`}>
        {stats.map((stat, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="bg-dark/50 border border-amber-dark/30 rounded-lg p-3 text-center"
          >
            {stat.icon && (
              <div className={`${sizes.icon} mb-1 ${COLOR_CLASSES[stat.color || 'amber']}`}>
                {stat.icon}
              </div>
            )}
            <div className={`${sizes.value} font-bold ${COLOR_CLASSES[stat.color || 'amber']}`}>
              {stat.value}
            </div>
            <div className={`${sizes.label} text-amber-dim mt-0.5`}>{stat.label}</div>
          </motion.div>
        ))}
      </div>
    );
  }

  // Default variant
  return (
    <div className={`grid ${columnClasses[columns]} gap-3 ${className}`}>
      {stats.map((stat, index) => (
        <motion.div
          key={index}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.05 }}
          className="flex items-center gap-2"
        >
          {stat.icon && (
            <span
              className={`
                ${sizes.icon} ${COLOR_CLASSES[stat.color || 'amber']}
                drop-shadow-[0_0_4px_currentColor]
              `}
            >
              {stat.icon}
            </span>
          )}
          <div>
            <div className={`${sizes.value} font-semibold ${COLOR_CLASSES[stat.color || 'amber']}`}>
              {stat.value}
            </div>
            <div className={`${sizes.label} text-amber-dim`}>{stat.label}</div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

export default StatDisplay;
