'use client';

import { motion } from 'framer-motion';
import { AppScreen } from '@/lib/store';

/**
 * MainMenu - Main dashboard / command center
 * Shows: Title, 7 menu buttons, bottom stats
 * Buttons: PLAY, MINT EMISSARY, SOCIAL, VAULT, EVENTS, LORE, TUTORIAL
 */

interface MenuItem {
  id: AppScreen;
  title: string;
  icon: string;
  badge?: number;
}

interface MainMenuProps {
  pyreBalance?: number;
  emissaryCount?: number;
  unreadMessages?: number;
  onNavigate: (screen: AppScreen) => void;
}

export function MainMenu({
  pyreBalance = 0,
  emissaryCount = 0,
  unreadMessages = 0,
  onNavigate,
}: MainMenuProps) {
  const menuItems: MenuItem[] = [
    {
      id: 'play',
      title: 'PLAY',
      icon: '▶',
    },
    {
      id: 'mint',
      title: 'MINT EMISSARY',
      icon: '◈',
    },
    {
      id: 'social-globe',
      title: 'SOCIAL',
      icon: '🌍',
      badge: unreadMessages,
    },
    {
      id: 'vault',
      title: 'VAULT',
      icon: '🏦',
    },
    {
      id: 'events',
      title: 'EVENTS',
      icon: '📅',
    },
    {
      id: 'lore',
      title: 'LORE',
      icon: '📜',
    },
    {
      id: 'tutorial',
      title: 'TUTORIAL',
      icon: '❓',
    },
  ];

  return (
    <div className="screen-view flex flex-col min-h-screen p-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-4"
      >
        <h1 className="title text-3xl">EMBERHOLM</h1>
        <p className="subtitle">PORTAL</p>
      </motion.div>

      {/* Menu buttons */}
      <div className="menu-container">
        {menuItems.map((item, index) => (
          <motion.button
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.05 * index }}
            onClick={() => onNavigate(item.id)}
            className={`menu-btn ${index === 0 ? 'selected' : ''}`}
          >
            <span className="icon">{item.icon}</span>
            <span className="flex-1 text-left">{item.title}</span>
            {item.badge && item.badge > 0 && (
              <span className="notif-badge">{item.badge}</span>
            )}
          </motion.button>
        ))}
      </div>

      {/* Stats footer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="stats-footer"
      >
        <div className="stat-item">
          <div className="stat-value">{emissaryCount}</div>
          <div className="stat-label">EMISSARIES</div>
        </div>
        <div className="stat-item">
          <div className="stat-value cyan">{pyreBalance.toLocaleString()}</div>
          <div className="stat-label">◈ PYRE</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">0</div>
          <div className="stat-label">🔥 EMBER</div>
        </div>
      </motion.div>
    </div>
  );
}
