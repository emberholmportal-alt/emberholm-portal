'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FireIcon, SwordsIcon, SparkleIcon } from '@/components/ui/Icons';

/**
 * MintScreen - Mint new Emissary
 */

interface MintScreenProps {
  wallet: string | null;
  onMintSuccess?: (tokenId: string) => void;
  onBack: () => void;
}

interface MintStats {
  totalMinted: number;
  maxSupply: number;
  priceEth: number;
}

interface MintedEmissary {
  token_id: string;
  name: string;
  guild: string;
  race_class: string;
  image_url: string;
}

export function MintScreen({ wallet, onMintSuccess, onBack }: MintScreenProps) {
  const [stats, setStats] = useState<MintStats>({
    totalMinted: 12847,
    maxSupply: 35000,
    priceEth: 0.0011,
  });
  const [ethBalance, setEthBalance] = useState<number>(0.05);
  const [quantity, setQuantity] = useState(1);
  const [isMinting, setIsMinting] = useState(false);
  const [mintedEmissary, setMintedEmissary] = useState<MintedEmissary | null>(null);
  const [revealPhase, setRevealPhase] = useState<'idle' | 'minting' | 'revealing' | 'complete'>('idle');
  const [error, setError] = useState<string | null>(null);

  // Load mint stats
  useEffect(() => {
    // TODO: Fetch actual stats from contract
  }, []);

  // Load ETH balance
  useEffect(() => {
    if (!wallet) return;
    // TODO: Fetch actual ETH balance
  }, [wallet]);

  // Calculate total cost
  const totalCost = stats.priceEth * quantity;
  const canAfford = ethBalance >= totalCost;
  const remainingSupply = stats.maxSupply - stats.totalMinted;

  // Handle mint
  const handleMint = async () => {
    if (!wallet || !canAfford || quantity > remainingSupply) return;

    setIsMinting(true);
    setError(null);
    setRevealPhase('minting');

    try {
      // Simulate minting delay
      await new Promise(resolve => setTimeout(resolve, 2000));

      setRevealPhase('revealing');

      // Simulate reveal delay
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Mock minted emissary
      const minted: MintedEmissary = {
        token_id: `${stats.totalMinted + 1}`,
        name: `Emissary #${stats.totalMinted + 1}`,
        guild: ['Pyreguard', 'Ashwalkers', 'Embercourt', 'Cinderkin', 'Flamekeepers', 'Scorchlords'][
          Math.floor(Math.random() * 6)
        ],
        race_class: 'Human Warrior',
        image_url: '',
      };

      setMintedEmissary(minted);
      setRevealPhase('complete');
      setStats(prev => ({ ...prev, totalMinted: prev.totalMinted + quantity }));

      onMintSuccess?.(minted.token_id);
    } catch (err: any) {
      setError(err.message || 'Mint failed');
      setRevealPhase('idle');
    } finally {
      setIsMinting(false);
    }
  };

  // Reset to mint again
  const handleMintAgain = () => {
    setMintedEmissary(null);
    setRevealPhase('idle');
    setQuantity(1);
  };

  // Progress percentage
  const mintProgress = (stats.totalMinted / stats.maxSupply) * 100;

  return (
    <div className="screen-view flex flex-col min-h-screen p-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-6"
      >
        <h1 className="title text-2xl">MINT EMISSARY</h1>
        <p className="subtitle">Join the ranks of Emberholm</p>
      </motion.div>

      {/* Main content */}
      <div className="flex-1 flex flex-col items-center justify-center">
        <AnimatePresence mode="wait">
          {revealPhase === 'idle' && (
            <motion.div
              key="mint-form"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-sm"
            >
              {/* Supply counter */}
              <div className="portal-box mb-6">
                <div className="text-center mb-4">
                  <div className="text-3xl text-amber-bright font-bold">
                    {stats.totalMinted.toLocaleString()}
                  </div>
                  <div className="text-amber-dim text-sm">
                    / {stats.maxSupply.toLocaleString()} EMISSARIES MINTED
                  </div>
                </div>

                {/* Progress bar */}
                <div className="w-full h-2 bg-dark rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${mintProgress}%` }}
                    transition={{ duration: 1, ease: 'easeOut' }}
                    className="h-full bg-gradient-to-r from-amber-dark to-amber"
                  />
                </div>
                <div className="text-xs text-amber-dark text-center mt-2">
                  {remainingSupply.toLocaleString()} remaining
                </div>
              </div>

              {/* Price and balance */}
              <div className="data-box mb-4">
                <div className="flex justify-between items-center mb-3">
                  <span className="text-amber-dim">Price per Emissary</span>
                  <span className="text-amber-bright font-semibold">
                    {stats.priceEth} ETH
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-amber-dim">Your Balance</span>
                  <span className={ethBalance < stats.priceEth ? 'text-red' : 'text-green'}>
                    {ethBalance.toFixed(4)} ETH
                  </span>
                </div>
              </div>

              {/* Quantity selector */}
              <div className="data-box mb-4">
                <div className="text-amber-dim text-sm mb-2">Quantity</div>
                <div className="flex items-center justify-center gap-4">
                  <button
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    disabled={quantity <= 1}
                    className="w-10 h-10 rounded border border-amber-dark text-amber
                             hover:border-amber disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    -
                  </button>
                  <span className="text-2xl text-amber-bright font-bold w-12 text-center">
                    {quantity}
                  </span>
                  <button
                    onClick={() => setQuantity(Math.min(10, quantity + 1))}
                    disabled={quantity >= 10 || quantity >= remainingSupply}
                    className="w-10 h-10 rounded border border-amber-dark text-amber
                             hover:border-amber disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    +
                  </button>
                </div>
                <div className="text-center mt-3">
                  <span className="text-amber-dim text-sm">Total: </span>
                  <span className="text-amber-bright font-semibold">
                    {totalCost.toFixed(4)} ETH
                  </span>
                </div>
              </div>

              {/* Error message */}
              {error && (
                <div className="text-red text-sm text-center mb-4">{error}</div>
              )}

              {/* Mint button */}
              <button
                onClick={handleMint}
                disabled={!wallet || !canAfford || isMinting || remainingSupply === 0}
                className="w-full btn large disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {!wallet
                  ? 'CONNECT WALLET'
                  : !canAfford
                  ? 'INSUFFICIENT ETH'
                  : remainingSupply === 0
                  ? 'SOLD OUT'
                  : `MINT ${quantity} EMISSARY${quantity > 1 ? 'S' : ''}`}
              </button>
            </motion.div>
          )}

          {revealPhase === 'minting' && (
            <motion.div
              key="minting"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center"
            >
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                className="mb-4 flex justify-center"
              >
                <FireIcon size={64} className="text-amber" />
              </motion.div>
              <div className="text-amber-bright text-xl">Minting...</div>
              <div className="text-amber-dim text-sm mt-2">
                Confirm transaction in your wallet
              </div>
            </motion.div>
          )}

          {revealPhase === 'revealing' && (
            <motion.div
              key="revealing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center"
            >
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 0.5, repeat: Infinity }}
                className="mb-4 flex justify-center"
              >
                <SparkleIcon size={64} className="text-cyan" />
              </motion.div>
              <div className="text-amber-bright text-xl">Revealing...</div>
              <div className="text-amber-dim text-sm mt-2">
                Your Emissary is being summoned
              </div>
            </motion.div>
          )}

          {revealPhase === 'complete' && mintedEmissary && (
            <motion.div
              key="complete"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="text-center w-full max-w-sm"
            >
              <div className="portal-box mb-6">
                <div className="ornament mb-4">═══ ◈ ═══</div>

                {/* Emissary card */}
                <div className="relative mx-auto w-48 h-48 mb-4 rounded-lg border-2 border-amber
                              bg-gradient-to-b from-amber-dark/20 to-dark
                              flex items-center justify-center">
                  {mintedEmissary.image_url ? (
                    <img
                      src={mintedEmissary.image_url}
                      alt={mintedEmissary.name}
                      className="w-full h-full object-cover rounded-lg"
                    />
                  ) : (
                    <SwordsIcon size={64} className="text-amber" />
                  )}
                </div>

                <h2 className="title text-xl mb-2">{mintedEmissary.name}</h2>
                <div className="text-amber text-sm">{mintedEmissary.guild}</div>
                <div className="text-amber-dim text-xs mt-1">
                  {mintedEmissary.race_class}
                </div>

                <div className="ornament mt-4">═══ ◈ ═══</div>
              </div>

              <div className="text-green text-sm mb-4">
                Congratulations! Your Emissary has joined Emberholm.
              </div>

              <div className="space-y-2">
                <button onClick={handleMintAgain} className="w-full btn">
                  MINT ANOTHER
                </button>
                <button onClick={onBack} className="w-full btn secondary">
                  VIEW IN MENU
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Back button (only in idle state) */}
      {revealPhase === 'idle' && (
        <button onClick={onBack} className="back-btn mt-4">
          ← BACK
        </button>
      )}
    </div>
  );
}

export default MintScreen;
