'use client';

import { motion } from 'framer-motion';

/**
 * TabBar - Reusable tab navigation
 * CRT-styled with active indicator
 */

interface Tab {
  id: string;
  label: string;
  icon?: string;
  badge?: number;
}

interface TabBarProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (tabId: string) => void;
  variant?: 'default' | 'pills' | 'underline';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function TabBar({
  tabs,
  activeTab,
  onChange,
  variant = 'underline',
  size = 'md',
  className = '',
}: TabBarProps) {
  const sizeClasses = {
    sm: 'text-xs py-1',
    md: 'text-sm py-2',
    lg: 'text-base py-3',
  };

  const renderTab = (tab: Tab) => {
    const isActive = tab.id === activeTab;

    if (variant === 'pills') {
      return (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`
            relative flex-1 flex items-center justify-center gap-1.5
            ${sizeClasses[size]} px-3 rounded-lg font-medium
            transition-all duration-200
            ${isActive
              ? 'bg-amber/20 text-amber-bright'
              : 'text-amber-dim hover:text-amber hover:bg-amber-dark/20'
            }
          `}
        >
          {tab.icon && <span>{tab.icon}</span>}
          <span>{tab.label}</span>
          {tab.badge !== undefined && tab.badge > 0 && (
            <span className="ml-1 px-1.5 py-0.5 text-xs bg-amber text-dark rounded-full">
              {tab.badge}
            </span>
          )}
        </button>
      );
    }

    // Default: underline variant
    return (
      <button
        key={tab.id}
        onClick={() => onChange(tab.id)}
        className={`
          relative flex-1 flex items-center justify-center gap-1.5
          ${sizeClasses[size]} font-medium
          transition-colors duration-200
          ${isActive
            ? 'text-amber-bright'
            : 'text-amber-dim hover:text-amber'
          }
        `}
      >
        {tab.icon && <span>{tab.icon}</span>}
        <span>{tab.label}</span>
        {tab.badge !== undefined && tab.badge > 0 && (
          <span className="ml-1 px-1.5 py-0.5 text-xs bg-amber text-dark rounded-full">
            {tab.badge}
          </span>
        )}

        {/* Active indicator */}
        {isActive && (
          <motion.div
            layoutId="tab-indicator"
            className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber"
            transition={{ type: 'spring', stiffness: 500, damping: 30 }}
          />
        )}
      </button>
    );
  };

  return (
    <div
      className={`
        flex
        ${variant === 'underline' ? 'border-b border-amber-dark/30' : 'gap-1'}
        ${className}
      `}
    >
      {tabs.map(renderTab)}
    </div>
  );
}

export default TabBar;
