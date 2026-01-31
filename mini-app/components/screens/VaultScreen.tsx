'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { createPublicClient, http, parseAbi } from 'viem';
import { base } from 'viem/chains';
import { Emissary, getEmberBalance } from '@/lib/api';
import { CONTRACT_CONFIG } from '@/lib/contracts';

/**
 * VaultScreen - Tokens + Inventory (Real blockchain data)
 * TABS: TOKENS | ITEMS | RUNES
 *
 * Fetches Items/Runes from blockchain using tokensOfOwner()
 * Then loads metadata from IPFS
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

// Item interface (from IPFS metadata)
interface VaultItem {
  id: string;
  tokenId: string;
  name: string;
  type: string;
  rarity: string;
  image: string;
  attributes: Record<string, string>;
  equippedTo: string | null;
}

// Rune interface (from IPFS metadata)
interface VaultRune {
  id: string;
  tokenId: string;
  name: string;
  image: string;
  rarity: string;
  attributes: Record<string, string>;
  equippedTo: string | null;
}

// Rarity colors
const RARITY_COLORS: Record<string, string> = {
  common: 'text-gray-400',
  uncommon: 'text-green',
  rare: 'text-cyan',
  epic: 'text-purple-400',
  legendary: 'text-amber-bright',
  mythic: 'text-red-400',
};

// Viem public client for blockchain queries
const publicClient = createPublicClient({
  chain: base,
  transport: http(CONTRACT_CONFIG.RPC_URL),
});

// ABI for tokensOfOwner
const NFT_ABI = parseAbi([
  'function tokensOfOwner(address owner) view returns (uint256[])',
  'function balanceOf(address owner) view returns (uint256)',
]);

// Fetch metadata from IPFS
async function fetchIPFSMetadata(
  type: 'item' | 'rune',
  tokenId: string
): Promise<any> {
  const paddedId = tokenId.padStart(5, '0');
  const cid = type === 'item'
    ? CONTRACT_CONFIG.IPFS.ITEMS_METADATA_CID
    : CONTRACT_CONFIG.IPFS.RUNES_METADATA_CID;

  const url = `${CONTRACT_CONFIG.IPFS.GATEWAY}${cid}/${paddedId}.json`;

  try {
    const response = await fetch(url, { next: { revalidate: 3600 } });
    if (!response.ok) {
      console.warn(`[IPFS] Failed to fetch ${type} #${paddedId}: ${response.status}`);
      return null;
    }

    const metadata = await response.json();

    // Convert ipfs:// URLs to https://
    if (metadata.image?.startsWith('ipfs://')) {
      metadata.image = metadata.image.replace('ipfs://', CONTRACT_CONFIG.IPFS.GATEWAY);
    }

    // Fallback image if missing
    if (!metadata.image) {
      const imagesCid = type === 'item'
        ? CONTRACT_CONFIG.IPFS.ITEMS_IMAGES_CID
        : CONTRACT_CONFIG.IPFS.RUNES_IMAGES_CID;
      metadata.image = `${CONTRACT_CONFIG.IPFS.GATEWAY}${imagesCid}/${paddedId}.png`;
    }

    return metadata;
  } catch (error) {
    console.error(`[IPFS] Error fetching ${type} #${paddedId}:`, error);
    return null;
  }
}

// Extract attribute value from NFT metadata
function getAttribute(attributes: any[], traitType: string): string {
  if (!Array.isArray(attributes)) return 'Unknown';
  const attr = attributes.find((a: any) => a.trait_type === traitType);
  return attr?.value || 'Unknown';
}

export function VaultScreen({ wallet, emissaries, onBack }: VaultScreenProps) {
  const [activeTab, setActiveTab] = useState<VaultTab>('tokens');
  const [balances, setBalances] = useState<TokenBalances>({
    ember: { balance: 0, pending: 0 },
    ash: { balance: 0 },
  });
  const [items, setItems] = useState<VaultItem[]>([]);
  const [runes, setRunes] = useState<VaultRune[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadingStatus, setLoadingStatus] = useState('');
  const [burnAmount, setBurnAmount] = useState('');
  const [showEquipModal, setShowEquipModal] = useState<string | null>(null);
  const [equipType, setEquipType] = useState<'item' | 'rune'>('item');

  // Load Items from blockchain + IPFS
  const loadItems = useCallback(async (walletAddress: string): Promise<VaultItem[]> => {
    console.log('[Vault] Loading items from blockchain...');
    setLoadingStatus('Querying Items contract...');

    try {
      const tokenIds = await publicClient.readContract({
        address: CONTRACT_CONFIG.CONTRACTS.EmberItems as `0x${string}`,
        abi: NFT_ABI,
        functionName: 'tokensOfOwner',
        args: [walletAddress as `0x${string}`],
      });

      const tokenIdStrings = (tokenIds as bigint[]).map(id => id.toString());
      console.log(`[Vault] Found ${tokenIdStrings.length} items on blockchain`);

      if (tokenIdStrings.length === 0) return [];

      setLoadingStatus(`Loading ${tokenIdStrings.length} items from IPFS...`);

      // Fetch metadata for each item (in parallel, max 5 concurrent)
      const loadedItems: VaultItem[] = [];

      for (let i = 0; i < tokenIdStrings.length; i += 5) {
        const batch = tokenIdStrings.slice(i, i + 5);
        const metadataPromises = batch.map(id => fetchIPFSMetadata('item', id));
        const metadataResults = await Promise.all(metadataPromises);

        metadataResults.forEach((metadata, idx) => {
          const tokenId = batch[idx];
          if (metadata) {
            loadedItems.push({
              id: `item-${tokenId}`,
              tokenId,
              name: metadata.name || `Item #${tokenId}`,
              type: getAttribute(metadata.attributes, 'Type'),
              rarity: getAttribute(metadata.attributes, 'Rarity').toLowerCase(),
              image: metadata.image || '',
              attributes: metadata.attributes?.reduce((acc: any, attr: any) => {
                acc[attr.trait_type] = attr.value;
                return acc;
              }, {}) || {},
              equippedTo: null, // TODO: Get from backend
            });
          }
        });

        setLoadingStatus(`Loaded ${loadedItems.length}/${tokenIdStrings.length} items...`);
      }

      return loadedItems;
    } catch (error) {
      console.error('[Vault] Error loading items:', error);
      return [];
    }
  }, []);

  // Load Runes from blockchain + IPFS
  const loadRunes = useCallback(async (walletAddress: string): Promise<VaultRune[]> => {
    console.log('[Vault] Loading runes from blockchain...');
    setLoadingStatus('Querying Runes contract...');

    try {
      const tokenIds = await publicClient.readContract({
        address: CONTRACT_CONFIG.CONTRACTS.EmberRunes as `0x${string}`,
        abi: NFT_ABI,
        functionName: 'tokensOfOwner',
        args: [walletAddress as `0x${string}`],
      });

      const tokenIdStrings = (tokenIds as bigint[]).map(id => id.toString());
      console.log(`[Vault] Found ${tokenIdStrings.length} runes on blockchain`);

      if (tokenIdStrings.length === 0) return [];

      setLoadingStatus(`Loading ${tokenIdStrings.length} runes from IPFS...`);

      // Fetch metadata for each rune (in parallel, max 5 concurrent)
      const loadedRunes: VaultRune[] = [];

      for (let i = 0; i < tokenIdStrings.length; i += 5) {
        const batch = tokenIdStrings.slice(i, i + 5);
        const metadataPromises = batch.map(id => fetchIPFSMetadata('rune', id));
        const metadataResults = await Promise.all(metadataPromises);

        metadataResults.forEach((metadata, idx) => {
          const tokenId = batch[idx];
          if (metadata) {
            loadedRunes.push({
              id: `rune-${tokenId}`,
              tokenId,
              name: metadata.name || `Rune #${tokenId}`,
              image: metadata.image || '',
              rarity: getAttribute(metadata.attributes, 'Rarity').toLowerCase(),
              attributes: metadata.attributes?.reduce((acc: any, attr: any) => {
                acc[attr.trait_type] = attr.value;
                return acc;
              }, {}) || {},
              equippedTo: null, // TODO: Get from backend
            });
          }
        });

        setLoadingStatus(`Loaded ${loadedRunes.length}/${tokenIdStrings.length} runes...`);
      }

      return loadedRunes;
    } catch (error) {
      console.error('[Vault] Error loading runes:', error);
      return [];
    }
  }, []);

  // Load vault data
  useEffect(() => {
    if (!wallet || wallet === '0x0000000000000000000000000000000000000000') {
      setIsLoading(false);
      return;
    }

    async function loadVaultData() {
      setIsLoading(true);
      setLoadingStatus('Connecting to blockchain...');

      try {
        // Load balances from API
        const emberData = await getEmberBalance(wallet!);
        setBalances({
          ember: { balance: emberData.balance || 0, pending: emberData.pending || 0 },
          ash: { balance: 0 }, // ASH balance from separate endpoint if needed
        });
        console.log(`[Vault] Loaded EMBER balance: ${emberData.balance}`);

        // Load Items and Runes in parallel from blockchain
        const [loadedItems, loadedRunes] = await Promise.all([
          loadItems(wallet!),
          loadRunes(wallet!),
        ]);

        setItems(loadedItems);
        setRunes(loadedRunes);

        console.log(`[Vault] Loaded ${loadedItems.length} items and ${loadedRunes.length} runes`);
      } catch (error) {
        console.error('[Vault] Error loading vault:', error);
      } finally {
        setIsLoading(false);
        setLoadingStatus('');
      }
    }

    loadVaultData();
  }, [wallet, loadItems, loadRunes]);

  // Handle claim
  const handleClaim = async () => {
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

  const tabs: { id: VaultTab; label: string; count?: number }[] = [
    { id: 'tokens', label: 'TOKENS' },
    { id: 'items', label: 'ITEMS', count: items.length },
    { id: 'runes', label: 'RUNES', count: runes.length },
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
            {tab.count !== undefined && tab.count > 0 && (
              <span className="ml-1 text-xs text-amber-dim">({tab.count})</span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading ? (
          <div className="text-center py-8">
            <div className="text-amber-dim mb-2">Loading...</div>
            {loadingStatus && (
              <div className="text-xs text-amber-dark">{loadingStatus}</div>
            )}
          </div>
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
                      <button onClick={handleClaim} className="btn tiny">
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
                        className="btn tiny disabled:opacity-50"
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
                  <div className="grid grid-cols-2 gap-3">
                    {items.map(item => (
                      <div key={item.id} className="data-box flex flex-col">
                        {/* Image */}
                        <div className="relative w-full aspect-square mb-2 bg-dark/50 rounded overflow-hidden">
                          {item.image ? (
                            <img
                              src={item.image}
                              alt={item.name}
                              className="w-full h-full object-contain"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = '/icons/Swords.png';
                              }}
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-4xl">
                              ⚔️
                            </div>
                          )}
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <div className={`font-semibold text-sm truncate ${RARITY_COLORS[item.rarity] || 'text-amber'}`}>
                            {item.name}
                          </div>
                          <div className="text-xs text-amber-dark uppercase">
                            {item.type}
                          </div>
                          {item.equippedTo && (
                            <div className="text-xs text-cyan mt-1 truncate">
                              → {emissaries.find(e => e.token_id === item.equippedTo)?.name || `#${item.equippedTo}`}
                            </div>
                          )}
                        </div>

                        {/* Equip Button */}
                        <button
                          onClick={() => {
                            if (item.equippedTo) {
                              handleEquip('item', item.id, null);
                            } else {
                              setEquipType('item');
                              setShowEquipModal(item.id);
                            }
                          }}
                          className="btn tiny w-full mt-2"
                        >
                          {item.equippedTo ? 'UNEQUIP' : 'EQUIP'}
                        </button>
                      </div>
                    ))}
                  </div>
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
                  <div className="grid grid-cols-2 gap-3">
                    {runes.map(rune => (
                      <div key={rune.id} className="data-box flex flex-col">
                        {/* Image */}
                        <div className="relative w-full aspect-square mb-2 bg-dark/50 rounded overflow-hidden">
                          {rune.image ? (
                            <img
                              src={rune.image}
                              alt={rune.name}
                              className="w-full h-full object-contain"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = '/icons/Sparkles.png';
                              }}
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-4xl">
                              🔮
                            </div>
                          )}
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <div className={`font-semibold text-sm truncate ${RARITY_COLORS[rune.rarity] || 'text-amber'}`}>
                            {rune.name}
                          </div>
                          <div className="text-xs text-amber-dark">
                            {rune.attributes['Effect'] || 'Mysterious power'}
                          </div>
                          {rune.equippedTo && (
                            <div className="text-xs text-cyan mt-1 truncate">
                              → {emissaries.find(e => e.token_id === rune.equippedTo)?.name || `#${rune.equippedTo}`}
                            </div>
                          )}
                        </div>

                        {/* Equip Button */}
                        <button
                          onClick={() => {
                            if (rune.equippedTo) {
                              handleEquip('rune', rune.id, null);
                            } else {
                              setEquipType('rune');
                              setShowEquipModal(rune.id);
                            }
                          }}
                          className="btn tiny w-full mt-2"
                        >
                          {rune.equippedTo ? 'UNEQUIP' : 'EQUIP'}
                        </button>
                      </div>
                    ))}
                  </div>
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
