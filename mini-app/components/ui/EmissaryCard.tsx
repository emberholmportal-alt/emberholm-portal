'use client';

import { motion } from 'framer-motion';
import { Emissary } from '@/lib/api';

/**
 * EmissaryCard - Reusable Emissary display card
 * Shows image, name, level, guild, and state
 */

interface EmissaryCardProps {
  emissary: Emissary;
  onClick?: () => void;
  showActions?: boolean;
  onStartMission?: () => void;
  onStartMicroMission?: () => void;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

// State styles
const STATE_STYLES: Record<string, { color: string; label: string; icon: string }> = {
  READY: { color: 'text-green', label: 'IDLE', icon: '●' },
  ON_MISSION: { color: 'text-cyan', label: 'ON MISSION', icon: '◐' },
  ON_MICRO_MISSION: { color: 'text-amber-bright', label: 'MICRO-MISSION', icon: '◐' },
  FALLEN: { color: 'text-red', label: 'DEAD', icon: '✖' },
  CLAIMING: { color: 'text-purple-400', label: 'CLAIMING', icon: '◎' },
};

export function EmissaryCard({
  emissary,
  onClick,
  showActions = false,
  onStartMission,
  onStartMicroMission,
  size = 'md',
  className = '',
}: EmissaryCardProps) {
  const state = emissary.current_state || 'READY';
  const stateStyle = STATE_STYLES[state] || STATE_STYLES.READY;
  const isReady = state === 'READY';
  const isFallen = state === 'FALLEN';

  const sizeClasses = {
    sm: {
      container: 'p-2',
      image: 'w-10 h-10',
      title: 'text-sm',
      subtitle: 'text-xs',
    },
    md: {
      container: 'p-3',
      image: 'w-14 h-14',
      title: 'text-base',
      subtitle: 'text-xs',
    },
    lg: {
      container: 'p-4',
      image: 'w-20 h-20',
      title: 'text-lg',
      subtitle: 'text-sm',
    },
  };

  const sizes = sizeClasses[size];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={onClick ? { scale: 1.02 } : undefined}
      whileTap={onClick ? { scale: 0.98 } : undefined}
      onClick={onClick}
      className={`
        bg-dark/50 border border-amber-dark/50 rounded-lg ${sizes.container}
        transition-all duration-200 hover:border-amber
        ${onClick ? 'cursor-pointer' : ''}
        ${isFallen ? 'opacity-60' : ''}
        ${className}
      `}
    >
      <div className="flex items-center gap-3">
        {/* Image */}
        <div className={`${sizes.image} rounded-lg overflow-hidden border border-amber-dark flex-shrink-0`}>
          {emissary.image_url ? (
            <img
              src={emissary.image_url}
              alt={emissary.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full bg-amber-dark/30 flex items-center justify-center text-amber">
              ⚔️
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h3 className={`text-amber-bright font-semibold truncate ${sizes.title}`}>
              {emissary.name}
            </h3>
            {/* State indicator */}
            <span className={`${stateStyle.color} ${sizes.subtitle} flex items-center gap-1 flex-shrink-0`}>
              <span className={state !== 'READY' && state !== 'FALLEN' ? 'animate-pulse' : ''}>
                {stateStyle.icon}
              </span>
              <span className="hidden sm:inline">{stateStyle.label}</span>
            </span>
          </div>

          <div className={`${sizes.subtitle} text-amber-dim mt-0.5`}>
            Level {emissary.stats.level} • {emissary.guild}
          </div>

          {/* Stats row */}
          <div className={`flex items-center gap-3 mt-1 ${sizes.subtitle} text-amber-dark`}>
            <span>⚡ {emissary.stats.energy_current}/{emissary.stats.energy_max}</span>
            <span>💪 {emissary.stats.power}</span>
            {emissary.stats.death_count > 0 && (
              <span className="text-red">💀 {emissary.stats.death_count}</span>
            )}
          </div>
        </div>
      </div>

      {/* Actions */}
      {showActions && isReady && (
        <div className="flex gap-2 mt-3 pt-3 border-t border-amber-dark/30">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onStartMission?.();
            }}
            className="flex-1 btn small"
          >
            MISSION
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onStartMicroMission?.();
            }}
            className="flex-1 btn small"
          >
            MICRO
          </button>
        </div>
      )}
    </motion.div>
  );
}

export default EmissaryCard;
