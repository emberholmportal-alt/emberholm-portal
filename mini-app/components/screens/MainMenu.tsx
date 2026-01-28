'use client';

import { motion } from 'framer-motion';

/**
 * MainMenu - Main dashboard / command center
 * Shows: $SPARK balance, quick actions, navigation
 */

interface MainMenuProps {
  sparkBalance: number;
  emissaryCount: number;
  onNavigate: (screen: 'emissaries' | 'mission-select' | 'vault') => void;
  onConnect?: () => void;
  isConnected: boolean;
}

export function MainMenu({
  sparkBalance,
  emissaryCount,
  onNavigate,
  onConnect,
  isConnected,
}: MainMenuProps) {
  const menuItems = [
    {
      id: 'emissaries',
      title: 'EMISSARIES',
      subtitle: `${emissaryCount} Active`,
      icon: '⚔️',
      description: 'View and manage your Emissaries',
    },
    {
      id: 'mission-select',
      title: 'MICRO-MISSIONS',
      subtitle: 'Quick Adventures',
      icon: '🗺️',
      description: 'Short quests for $SPARK rewards',
    },
    {
      id: 'vault',
      title: 'VAULT',
      subtitle: 'Tokens & Items',
      icon: '💎',
      description: 'Check your $SPARK, $EMBER, items',
    },
  ];

  return (
    <div className="flex flex-col min-h-screen p-4 pt-12">
      {/* Header with SPARK balance */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-6"
      >
        <h1 className="font-alagard text-2xl text-ember-400 text-glow mb-1">
          COMMAND CENTER
        </h1>
        {isConnected ? (
          <div className="flex items-center justify-center gap-2 text-spark">
            <span className="text-xl">◈</span>
            <span className="text-xl font-bold">{sparkBalance.toLocaleString()}</span>
            <span className="text-sm opacity-70">$SPARK</span>
          </div>
        ) : (
          <p className="text-ember-400/60 text-sm">Connect wallet to continue</p>
        )}
      </motion.div>

      {/* Connect wallet button (if not connected) */}
      {!isConnected && onConnect && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mb-6"
        >
          <button
            onClick={onConnect}
            className="w-full btn-ember-primary py-3 text-center"
          >
            🔗 CONNECT WALLET
          </button>
        </motion.div>
      )}

      {/* Menu items */}
      <div className="flex-1 space-y-3">
        {menuItems.map((item, index) => (
          <motion.button
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 * (index + 1) }}
            onClick={() => onNavigate(item.id as any)}
            disabled={!isConnected && item.id !== 'vault'}
            className="w-full panel p-4 text-left transition-all duration-200
                       hover:border-ember-400/50 hover:shadow-ember
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl">{item.icon}</span>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h3 className="font-pixel text-ember-400 font-semibold">
                    {item.title}
                  </h3>
                  <span className="text-xs text-ember-400/50">
                    {item.subtitle}
                  </span>
                </div>
                <p className="text-xs text-ember-400/60 mt-1">
                  {item.description}
                </p>
              </div>
              <span className="text-ember-400/30">›</span>
            </div>
          </motion.button>
        ))}
      </div>

      {/* Footer links */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.6 }}
        transition={{ delay: 0.5 }}
        className="pt-4 pb-2 text-center text-xs text-ember-400/50 space-y-2"
      >
        <p>
          Full portal:{' '}
          <a
            href="https://emberholmportal.xyz"
            target="_blank"
            rel="noopener noreferrer"
            className="text-ember-400/70 underline"
          >
            emberholmportal.xyz
          </a>
        </p>
        <p className="text-[10px]">
          Era of the Flame · Year 1978
        </p>
      </motion.div>
    </div>
  );
}
