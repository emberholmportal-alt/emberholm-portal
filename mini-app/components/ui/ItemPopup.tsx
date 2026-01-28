'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Emissary } from '@/lib/api';

/**
 * ItemPopup - Modal for item/rune details and equipping
 */

interface Item {
  id: string;
  name: string;
  type: string;
  rarity: 'common' | 'uncommon' | 'rare' | 'epic' | 'legendary';
  icon: string;
  description?: string;
  benefits: string;
  equippedTo: string | null;
}

interface ItemPopupProps {
  item: Item | null;
  emissaries: Emissary[];
  onEquip: (itemId: string, emissaryId: string) => void;
  onUnequip: (itemId: string) => void;
  onClose: () => void;
}

// Rarity styles
const RARITY_STYLES: Record<string, { color: string; bg: string; border: string }> = {
  common: { color: 'text-gray-400', bg: 'bg-gray-500/10', border: 'border-gray-500/30' },
  uncommon: { color: 'text-green', bg: 'bg-green/10', border: 'border-green/30' },
  rare: { color: 'text-cyan', bg: 'bg-cyan/10', border: 'border-cyan/30' },
  epic: { color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/30' },
  legendary: { color: 'text-amber-bright', bg: 'bg-amber/10', border: 'border-amber/30' },
};

export function ItemPopup({
  item,
  emissaries,
  onEquip,
  onUnequip,
  onClose,
}: ItemPopupProps) {
  const [selectedEmissary, setSelectedEmissary] = useState<string | null>(null);
  const [confirmAction, setConfirmAction] = useState<'equip' | 'unequip' | null>(null);

  if (!item) return null;

  const rarityStyle = RARITY_STYLES[item.rarity] || RARITY_STYLES.common;
  const isEquipped = item.equippedTo !== null;
  const equippedEmissary = isEquipped
    ? emissaries.find(e => e.token_id === item.equippedTo)
    : null;

  const handleEquip = () => {
    if (selectedEmissary) {
      onEquip(item.id, selectedEmissary);
      onClose();
    }
  };

  const handleUnequip = () => {
    onUnequip(item.id);
    onClose();
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Overlay */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-dark/90 backdrop-blur-sm"
        />

        {/* Popup content */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          onClick={e => e.stopPropagation()}
          className={`
            relative w-full max-w-sm
            bg-dark border ${rarityStyle.border} rounded-lg
            shadow-lg overflow-hidden
          `}
        >
          {/* Header with item info */}
          <div className={`${rarityStyle.bg} p-4`}>
            <div className="flex items-start gap-3">
              <div className={`text-4xl ${rarityStyle.color}`}>{item.icon}</div>
              <div className="flex-1">
                <h3 className={`${rarityStyle.color} font-bold text-lg`}>{item.name}</h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-xs uppercase ${rarityStyle.color}`}>
                    {item.rarity}
                  </span>
                  <span className="text-xs text-amber-dim">•</span>
                  <span className="text-xs text-amber-dim uppercase">{item.type}</span>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-amber-dim hover:text-amber transition-colors"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Body */}
          <div className="p-4 space-y-4">
            {/* Description */}
            {item.description && (
              <p className="text-amber-dim text-sm italic">{item.description}</p>
            )}

            {/* Benefits */}
            <div>
              <div className="text-xs text-amber-dark uppercase mb-1">Benefits</div>
              <div className="text-amber text-sm">{item.benefits}</div>
            </div>

            {/* Equipped status */}
            {isEquipped && equippedEmissary && (
              <div className="data-box">
                <div className="text-xs text-amber-dark uppercase mb-1">Equipped to</div>
                <div className="flex items-center gap-2">
                  {equippedEmissary.image_url ? (
                    <img
                      src={equippedEmissary.image_url}
                      alt={equippedEmissary.name}
                      className="w-8 h-8 rounded border border-amber-dark"
                    />
                  ) : (
                    <div className="w-8 h-8 rounded bg-amber-dark/30 flex items-center justify-center">
                      ⚔️
                    </div>
                  )}
                  <span className="text-amber-bright">{equippedEmissary.name}</span>
                </div>
              </div>
            )}

            {/* Equip selector (if not equipped) */}
            {!isEquipped && (
              <div>
                <div className="text-xs text-amber-dark uppercase mb-2">Equip to Emissary</div>
                {emissaries.length === 0 ? (
                  <div className="text-amber-dim text-sm text-center py-2">
                    No emissaries available
                  </div>
                ) : (
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {emissaries.filter(e => e.current_state === 'READY').map(emissary => (
                      <button
                        key={emissary.token_id}
                        onClick={() => setSelectedEmissary(emissary.token_id)}
                        className={`
                          w-full flex items-center gap-2 p-2 rounded border
                          transition-all duration-200
                          ${selectedEmissary === emissary.token_id
                            ? 'border-amber bg-amber/10'
                            : 'border-amber-dark/30 hover:border-amber-dark'
                          }
                        `}
                      >
                        {emissary.image_url ? (
                          <img
                            src={emissary.image_url}
                            alt={emissary.name}
                            className="w-8 h-8 rounded border border-amber-dark"
                          />
                        ) : (
                          <div className="w-8 h-8 rounded bg-amber-dark/30 flex items-center justify-center text-sm">
                            ⚔️
                          </div>
                        )}
                        <div className="text-left">
                          <div className="text-amber-bright text-sm">{emissary.name}</div>
                          <div className="text-xs text-amber-dim">
                            Lv.{emissary.stats.level} • {emissary.guild}
                          </div>
                        </div>
                        {selectedEmissary === emissary.token_id && (
                          <span className="ml-auto text-amber">✓</span>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="p-4 pt-0 flex gap-2">
            {isEquipped ? (
              <>
                {confirmAction === 'unequip' ? (
                  <>
                    <button onClick={onClose} className="flex-1 btn secondary">
                      Cancel
                    </button>
                    <button onClick={handleUnequip} className="flex-1 btn">
                      Confirm
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setConfirmAction('unequip')}
                    className="w-full btn"
                  >
                    UNEQUIP
                  </button>
                )}
              </>
            ) : (
              <button
                onClick={handleEquip}
                disabled={!selectedEmissary}
                className="w-full btn disabled:opacity-50 disabled:cursor-not-allowed"
              >
                EQUIP
              </button>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

export default ItemPopup;
