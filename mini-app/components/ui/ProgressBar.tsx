'use client';

import { motion } from 'framer-motion';

/**
 * ProgressBar - Animated progress bar
 * CRT-styled with multiple color variants
 */

interface ProgressBarProps {
  current: number;
  max: number;
  color?: 'amber' | 'green' | 'red' | 'cyan' | 'purple';
  showLabel?: boolean;
  labelFormat?: 'percentage' | 'fraction' | 'value';
  height?: 'sm' | 'md' | 'lg';
  animated?: boolean;
  className?: string;
}

const COLOR_CLASSES = {
  amber: 'bg-gradient-to-r from-amber-dark to-amber',
  green: 'bg-gradient-to-r from-green/70 to-green',
  red: 'bg-gradient-to-r from-red/70 to-red',
  cyan: 'bg-gradient-to-r from-cyan/70 to-cyan',
  purple: 'bg-gradient-to-r from-purple-500/70 to-purple-400',
};

const HEIGHT_CLASSES = {
  sm: 'h-1',
  md: 'h-2',
  lg: 'h-3',
};

export function ProgressBar({
  current,
  max,
  color = 'amber',
  showLabel = false,
  labelFormat = 'percentage',
  height = 'md',
  animated = true,
  className = '',
}: ProgressBarProps) {
  const percentage = max > 0 ? Math.min(100, Math.max(0, (current / max) * 100)) : 0;

  const formatLabel = (): string => {
    switch (labelFormat) {
      case 'percentage':
        return `${Math.round(percentage)}%`;
      case 'fraction':
        return `${current}/${max}`;
      case 'value':
        return `${current}`;
      default:
        return `${Math.round(percentage)}%`;
    }
  };

  return (
    <div className={className}>
      {/* Label above bar */}
      {showLabel && (
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-amber-dim">{formatLabel()}</span>
        </div>
      )}

      {/* Progress bar container */}
      <div className={`w-full bg-dark rounded-full overflow-hidden ${HEIGHT_CLASSES[height]}`}>
        <motion.div
          initial={animated ? { width: 0 } : false}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className={`h-full rounded-full ${COLOR_CLASSES[color]}`}
        />
      </div>
    </div>
  );
}

export default ProgressBar;
