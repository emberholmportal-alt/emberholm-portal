'use client';

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Image from 'next/image';
import { useSoundContextOptional } from '@/lib/SoundContext';

/**
 * RewardToast - Global notification system for rewards
 * Shows animated popups for EMBER, XP, and Aura gains
 */

interface Reward {
  id: string;
  type: 'ember' | 'xp' | 'aura' | 'item' | 'level' | 'success' | 'error';
  amount?: number;
  message?: string;
  itemName?: string;
}

interface RewardToastContextType {
  showReward: (reward: Omit<Reward, 'id'>) => void;
  showEmberReward: (amount: number) => void;
  showXPReward: (amount: number) => void;
  showAuraReward: (amount: number) => void;
  showLevelUp: (level: number) => void;
  showSuccess: (message: string) => void;
  showError: (message: string) => void;
}

const RewardToastContext = createContext<RewardToastContextType | null>(null);

interface RewardToastProviderProps {
  children: ReactNode;
}

export function RewardToastProvider({ children }: RewardToastProviderProps) {
  const [rewards, setRewards] = useState<Reward[]>([]);
  const soundContext = useSoundContextOptional();

  const showReward = useCallback((reward: Omit<Reward, 'id'>) => {
    const id = `${Date.now()}-${Math.random()}`;
    const newReward = { ...reward, id };

    // Play sound based on type
    if (soundContext) {
      if (reward.type === 'level') {
        soundContext.playLevelUp?.();
      } else if (reward.type === 'error') {
        soundContext.playError?.();
      } else if (reward.type === 'success' || reward.type === 'ember' || reward.type === 'xp') {
        soundContext.playReward?.();
      } else {
        soundContext.playSuccess?.();
      }
    }

    setRewards(prev => [...prev, newReward]);

    // Auto-remove after 3 seconds
    setTimeout(() => {
      setRewards(prev => prev.filter(r => r.id !== id));
    }, 3000);
  }, [soundContext]);

  const showEmberReward = useCallback((amount: number) => {
    showReward({ type: 'ember', amount });
  }, [showReward]);

  const showXPReward = useCallback((amount: number) => {
    showReward({ type: 'xp', amount });
  }, [showReward]);

  const showAuraReward = useCallback((amount: number) => {
    showReward({ type: 'aura', amount });
  }, [showReward]);

  const showLevelUp = useCallback((level: number) => {
    showReward({ type: 'level', amount: level, message: `Level ${level}` });
  }, [showReward]);

  const showSuccess = useCallback((message: string) => {
    showReward({ type: 'success', message });
  }, [showReward]);

  const showError = useCallback((message: string) => {
    showReward({ type: 'error', message });
  }, [showReward]);

  return (
    <RewardToastContext.Provider
      value={{
        showReward,
        showEmberReward,
        showXPReward,
        showAuraReward,
        showLevelUp,
        showSuccess,
        showError,
      }}
    >
      {children}
      <RewardToastContainer rewards={rewards} />
    </RewardToastContext.Provider>
  );
}

export function useRewardToast() {
  const context = useContext(RewardToastContext);
  if (!context) {
    throw new Error('useRewardToast must be used within RewardToastProvider');
  }
  return context;
}

// Optional hook that doesn't throw
export function useRewardToastOptional() {
  return useContext(RewardToastContext);
}

// Toast container component
function RewardToastContainer({ rewards }: { rewards: Reward[] }) {
  return (
    <div className="fixed top-20 left-0 right-0 z-50 pointer-events-none flex flex-col items-center gap-2">
      <AnimatePresence>
        {rewards.map(reward => (
          <RewardToastItem key={reward.id} reward={reward} />
        ))}
      </AnimatePresence>
    </div>
  );
}

// Individual toast item
function RewardToastItem({ reward }: { reward: Reward }) {
  const getConfig = () => {
    switch (reward.type) {
      case 'ember':
        return {
          icon: '/icons/fire.png',
          label: 'EMBER',
          color: 'text-amber-bright',
          bg: 'bg-amber/20',
          border: 'border-amber',
        };
      case 'xp':
        return {
          icon: '/icons/Sparkles.png',
          label: 'XP',
          color: 'text-green',
          bg: 'bg-green/20',
          border: 'border-green',
        };
      case 'aura':
        return {
          icon: '/icons/crystalball.png',
          label: 'AURA',
          color: 'text-cyan',
          bg: 'bg-cyan/20',
          border: 'border-cyan',
        };
      case 'level':
        return {
          icon: '/icons/trophy.png',
          label: 'LEVEL UP',
          color: 'text-amber-bright',
          bg: 'bg-amber/30',
          border: 'border-amber-bright',
        };
      case 'success':
        return {
          icon: '/icons/Sparkles.png',
          label: '',
          color: 'text-green',
          bg: 'bg-green/20',
          border: 'border-green',
        };
      case 'error':
        return {
          icon: '/icons/skull.png',
          label: '',
          color: 'text-red-400',
          bg: 'bg-red-400/20',
          border: 'border-red-400',
        };
      default:
        return {
          icon: '/icons/Sparkles.png',
          label: '',
          color: 'text-amber',
          bg: 'bg-amber/20',
          border: 'border-amber',
        };
    }
  };

  const config = getConfig();

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.8 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -10, scale: 0.9 }}
      transition={{ type: 'spring', duration: 0.4 }}
      className={`pointer-events-auto px-4 py-2 rounded-lg border ${config.bg} ${config.border}
                  flex items-center gap-2 shadow-lg backdrop-blur-sm`}
    >
      <Image
        src={config.icon}
        alt=""
        width={20}
        height={20}
        className="pixel-icon-original"
      />
      <span className={`font-semibold ${config.color}`}>
        {reward.type === 'level' ? (
          reward.message
        ) : reward.amount !== undefined ? (
          <>+{reward.amount.toLocaleString()} {config.label}</>
        ) : (
          reward.message
        )}
      </span>
    </motion.div>
  );
}

export default RewardToastProvider;
