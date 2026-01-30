'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Image from 'next/image';
import { Emissary } from '@/lib/api';

/**
 * VaultScreen - Tokens + Inventory
 * TABS: TOKENS | ITEMS | RUNES
 */

interface VaultScreenProps {
  wallet: string | null;
  emissaries: Emissary[];
  onBack: () => void;
}

type VaultTab = 'tokens' | 'items' | 'runes';

// Token balances interface
interface TokenBalances {
  ember: { balance: number; pending: number };
  ash: { balance: number };
}

// Item interface
interface VaultItem {
  id: string;
  name: string;
  type: 'weapon' | 'armor' | 'accessory';
  rarity: 'common' | 'uncommon' | 'rare' | 'epic' | 'legendary';
  icon: string;
  benefits: string;
  equippedTo: string | null; // Emissary token_id or null
}

// Rune interface
interface VaultRune {
  id: string;
  name: string;
  symbol: string;
  effect: string;
  rarity: 'common' | 'uncommon' | 'rare' | 'epic' | 'legendary';
  equippedTo: string | null;
  slot: 1 | 2 | 3;
}

// Rarity colors
const RARITY_COLORS: Record<string, string> = {
  common: 'text-gray-400',
  uncommon: 'text-green',
  rare: 'text-cyan',
  epic: 'text-purple-400',
  legendary: 'text-amber-bright',
};

export function VaultScreen({ wallet, emissaries, onBack }: VaultScreenProps) {
  const [activeTab, setActiveTab] = useState<VaultTab>('tokens');
  const [balances, setBalances] = useState<TokenBalances>({
    ember: { balance: 0, pending: 0 },
    ash: { balance: 0 },
  });
  const [items, setItems] = useState<VaultItem[]>([]);
  const [runes, setRunes] = useState<VaultRune[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [burnAmount, setBurnAmount] = useState('');
  const [showEquipModal, setShowEquipModal] = useState<string | null>(null);
  const [equipType, setEquipType] = useState<'item' | 'rune'>('item');

  // Load vault data
  useEffect(() => {
    if (!wallet) return;

    async function loadVaultData() {
      setIsLoading(true);
      try {
        // Mock data - replace with actual API calls
        setBalances({
          ember: { balance: 125.5, pending: 12.3 },
          ash: { balance: 45.2 },
        });

        setItems([
          {
            id: 'item-1',
            name: 'Flame Sword',
            type: 'weapon',
            rarity: 'rare',
            icon: '/icons/Swords.png',
            benefits: '+15 Power, +5% Crit',
            equippedTo: null,
          },
          {
            id: 'item-2',
            name: 'Shadow Cloak',
            type: 'armor',
            rarity: 'epic',
            icon: '/icons/Cloak.png',
            benefits: '+20 Defense, +10% Dodge',
            equippedTo: emissaries[0]?.token_id || null,
          },
          {
            id: 'item-3',
            name: 'Ember Ring',
            type: 'accessory',
            rarity: 'uncommon',
            icon: '/icons/Sparkles.png',
            benefits: '+5% $EMBER earned',
            equippedTo: null,
          },
        ]);

        setRunes([
          {
            id: 'rune-1',
            name: 'Rune of Vitality',
            symbol: '/icons/Lightning.png',
            effect: '+10 Max Energy',
            rarity: 'uncommon',
            equippedTo: null,
            slot: 1,
          },
          {
            id: 'rune-2',
            name: 'Rune of Fortune',
            symbol: '/icons/Sparkles.png',
            effect: '+5% Loot Chance',
            rarity: 'rare',
            equippedTo: emissaries[0]?.token_id || null,
            slot: 2,
          },
        ]);
      } catch (error) {
        console.error('Error loading vault:', error);
      } finally {
        setIsLoading(false);
      }
    }

    loadVaultData();
  }, [wallet, emissaries]);

  // Handle claim
  const handleClaim = async (token: 'ember') => {
    // API call to claim pending tokens
    // await claimTokens(wallet, token);
  };

  // Handle burn
  const handleBurn = async () => {
    if (!burnAmount || parseFloat(burnAmount) <= 0) return;
    // API call to burn EMBER for ASH
    // await burnEmber(wallet, parseFloat(burnAmount));
    setBurnAmount('');
  };

  // Handle equip/unequip
  const handleEquip = async (
    type: 'item' | 'rune',
    id: string,
    emissaryId: string | null
  ) => {
    // API call to equip/unequip item
    // await equipItem(wallet, id, emissaryId);
    setShowEquipModal(null);
  };

  // Calculate ASH from EMBER burn (1000:1 ratio)
  const ashPreview = burnAmount ? (parseFloat(burnAmount) / 1000).toFixed(4) : '0';

  const tabs: { id: VaultTab; label: string }[] = [
    { id: 'tokens', label: 'TOKENS' },
    { id: 'items', label: 'ITEMS' },
    { id: 'runes', label: 'RUNES' },
  ];

  return (
    <div className="screen-view flex flex-col min-h-screen">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-4 text-center"
      >
        <h1 className="title text-2xl">VAULT</h1>
        <p className="subtitle">Your treasures await</p>
      </motion.div>

      {/* Tabs */}
      <div className="flex border-b border-amber-dark/30 px-4">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 py-2 text-sm font-semibold transition-colors
                       ${activeTab === tab.id
                         ? 'text-amber-bright border-b-2 border-amber'
                         : 'text-amber-dim hover:text-amber'}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading ? (
          <div className="text-center py-8 text-amber-dim">Loading...</div>
        ) : (
          <AnimatePresence mode="wait">
            {activeTab === 'tokens' && (
              <motion.div
                key="tokens"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="space-y-4"
              >
                {/* $EMBER */}
                <div className="data-box">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-amber-bright font-semibold">$EMBER</span>
                    <span className="text-lg text-amber">
                      {balances.ember.balance.toFixed(2)}
                    </span>
                  </div>
                  {balances.ember.pending > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-amber-dim">
                        Pending: {balances.ember.pending.toFixed(2)}
                      </span>
                      <button onClick={() => handleClaim('ember')} className="btn small">
                        CLAIM
                      </button>
                    </div>
                  )}
                </div>

                {/* $ASH */}
                <div className="data-box">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-amber-bright font-semibold">$ASH</span>
                    <span className="text-lg text-amber">
                      {balances.ash.balance.toFixed(2)}
                    </span>
                  </div>
                  <div className="mt-3 pt-3 border-t border-amber-dark/30">
                    <div className="text-xs text-amber-dim mb-2">
                      Burn EMBER → ASH (1000:1 ratio)
                    </div>
                    <div className="flex gap-2">
                      <input
                        type="number"
                        value={burnAmount}
                        onChange={e => setBurnAmount(e.target.value)}
                        placeholder="Amount"
                        className="flex-1 bg-dark/50 border border-amber-dark/50 rounded px-2 py-1
                                 text-amber text-sm placeholder:text-amber-dark/50
                                 focus:outline-none focus:border-amber"
                      />
                      <button
                        onClick={handleBurn}
                        disabled={!burnAmount || parseFloat(burnAmount) <= 0}
                        className="btn small disabled:opacity-50"
                      >
                        BURN
                      </button>
                    </div>
                    {burnAmount && parseFloat(burnAmount) > 0 && (
                      <div className="text-xs text-cyan mt-2">
                        You will receive: {ashPreview} $ASH
                      </div>
                    )}
                  </div>
                </div>

              </motion.div>
            )}

            {activeTab === 'items' && (
              <motion.div
                key="items"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="space-y-3"
              >
                {items.length === 0 ? (
                  <div className="text-center py-8 text-amber-dim">
                    No items found. Complete missions to earn loot!
                  </div>
                ) : (
                  items.map(item => (
                    <div key={item.id} className="data-box">
                      <div className="flex items-start gap-3">
                        <Image src={item.icon} alt={item.name} width={32} height={32} className="pixel-icon" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className={`font-semibold ${RARITY_COLORS[item.rarity]}`}>
                              {item.name}
                            </span>
                            <span className="text-xs text-amber-dark uppercase">
                              {item.type}
                            </span>
                          </div>
                          <div className="text-xs text-amber-dim mt-1">
                            {item.benefits}
                          </div>
                          {item.equippedTo && (
                            <div className="text-xs text-cyan mt-1">
                              Equipped to: {emissaries.find(e => e.token_id === item.equippedTo)?.name || item.equippedTo}
                            </div>
                          )}
                        </div>
                        <button
                          onClick={() => {
                            if (item.equippedTo) {
                              handleEquip('item', item.id, null);
                            } else {
                              setEquipType('item');
                              setShowEquipModal(item.id);
                            }
                          }}
                          className="btn small"
                        >
                          {item.equippedTo ? 'UNEQUIP' : 'EQUIP'}
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </motion.div>
            )}

            {activeTab === 'runes' && (
              <motion.div
                key="runes"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="space-y-3"
              >
                {runes.length === 0 ? (
                  <div className="text-center py-8 text-amber-dim">
                    No runes found. Discover them in dangerous missions!
                  </div>
                ) : (
                  runes.map(rune => (
                    <div key={rune.id} className="data-box">
                      <div className="flex items-start gap-3">
                        <Image src={rune.symbol} alt={rune.name} width={32} height={32} className="pixel-icon" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className={`font-semibold ${RARITY_COLORS[rune.rarity]}`}>
                              {rune.name}
                            </span>
                            <span className="text-xs text-amber-dark">
                              Slot {rune.slot}
                            </span>
                          </div>
                          <div className="text-xs text-amber-dim mt-1">
                            {rune.effect}
                          </div>
                          {rune.equippedTo && (
                            <div className="text-xs text-cyan mt-1">
                              Equipped to: {emissaries.find(e => e.token_id === rune.equippedTo)?.name || rune.equippedTo}
                            </div>
                          )}
                        </div>
                        <button
                          onClick={() => {
                            if (rune.equippedTo) {
                              handleEquip('rune', rune.id, null);
                            } else {
                              setEquipType('rune');
                              setShowEquipModal(rune.id);
                            }
                          }}
                          className="btn small"
                        >
                          {rune.equippedTo ? 'UNEQUIP' : 'EQUIP'}
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </div>

      {/* Equip Modal */}
      <AnimatePresence>
        {showEquipModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-dark/90 flex items-center justify-center p-4 z-50"
            onClick={() => setShowEquipModal(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="portal-box w-full max-w-sm"
              onClick={e => e.stopPropagation()}
            >
              <h3 className="title text-lg mb-4">SELECT EMISSARY</h3>
              {emissaries.length === 0 ? (
                <div className="text-amber-dim text-center py-4">
                  No emissaries available
                </div>
              ) : (
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {emissaries.map(emissary => (
                    <button
                      key={emissary.token_id}
                      onClick={() => handleEquip(equipType, showEquipModal, emissary.token_id)}
                      className="w-full data-box text-left hover:border-amber transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        {emissary.image_url ? (
                          <img
                            src={emissary.image_url}
                            alt={emissary.name}
                            className="w-10 h-10 rounded border border-amber-dark"
                          />
                        ) : (
                          <div className="w-10 h-10 rounded bg-amber-dark/30 flex items-center justify-center">
                            ⚔️
                          </div>
                        )}
                        <div>
                          <div className="text-amber-bright font-semibold">
                            {emissary.name}
                          </div>
                          <div className="text-xs text-amber-dim">
                            Level {emissary.stats.level} • {emissary.guild}
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
              <button
                onClick={() => setShowEquipModal(null)}
                className="w-full mt-4 text-amber-dim text-sm hover:text-amber"
              >
                Cancel
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Back button */}
      <div className="p-4">
        <button onClick={onBack} className="back-btn">
          ← BACK
        </button>
      </div>
    </div>
  );
}

export default VaultScreen;
