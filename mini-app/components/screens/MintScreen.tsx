'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Image from 'next/image';
import { CONTRACT_CONFIG } from '@/lib/contracts';

/**
 * MintScreen - Mint new Emissary
 * Reads totalSupply from EmberholmPortal contract on Base
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
  isLoading: boolean;
}

interface MintedEmissary {
  token_id: string;
  name: string;
  guild: string;
  race_class: string;
  image_url: string;
}

export function MintScreen({ wallet, onMintSuccess, onBack }: MintScreenProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [stats, setStats] = useState<MintStats>({
    totalMinted: 0,
    maxSupply: CONTRACT_CONFIG.MAX_SUPPLY,
    priceEth: CONTRACT_CONFIG.MINT_PRICE_ETH,
    isLoading: true,
  });
  const [ethBalance, setEthBalance] = useState<number>(0);
  const [isLoadingBalance, setIsLoadingBalance] = useState(false);
  const [quantity, setQuantity] = useState(1);
  const [isMinting, setIsMinting] = useState(false);
  const [mintedEmissaries, setMintedEmissaries] = useState<MintedEmissary[]>([]);
  const [revealPhase, setRevealPhase] = useState<'idle' | 'minting' | 'video' | 'revealing' | 'complete'>('idle');
  const [error, setError] = useState<string | null>(null);

  // Load mint stats from contract
  const loadContractStats = useCallback(async () => {
    try {
      // Use JSON-RPC to call totalSupply on the contract
      const response = await fetch(CONTRACT_CONFIG.RPC_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: 1,
          method: 'eth_call',
          params: [{
            to: CONTRACT_CONFIG.CONTRACTS.EmberholmPortal,
            data: '0x18160ddd', // totalSupply() selector
          }, 'latest'],
        }),
      });

      const data = await response.json();
      if (data.result) {
        const totalMinted = parseInt(data.result, 16);
        setStats(prev => ({
          ...prev,
          totalMinted,
          isLoading: false,
        }));
      } else {
        setStats(prev => ({ ...prev, isLoading: false }));
      }
    } catch (err) {
      console.error('Failed to load contract stats:', err);
      setStats(prev => ({ ...prev, isLoading: false }));
    }
  }, []);

  // Load ETH balance
  const loadEthBalance = useCallback(async () => {
    if (!wallet || wallet === '0x0000000000000000000000000000000000000000') {
      setEthBalance(0);
      return;
    }

    setIsLoadingBalance(true);
    try {
      const response = await fetch(CONTRACT_CONFIG.RPC_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: 1,
          method: 'eth_getBalance',
          params: [wallet, 'latest'],
        }),
      });

      const data = await response.json();
      if (data.result) {
        const balanceWei = BigInt(data.result);
        const balanceEth = Number(balanceWei) / 1e18;
        setEthBalance(balanceEth);
      }
    } catch (err) {
      console.error('Failed to load ETH balance:', err);
    } finally {
      setIsLoadingBalance(false);
    }
  }, [wallet]);

  useEffect(() => {
    loadContractStats();
  }, [loadContractStats]);

  useEffect(() => {
    loadEthBalance();
  }, [loadEthBalance]);

  // Calculate total cost
  const totalCost = stats.priceEth * quantity;
  const canAfford = ethBalance >= totalCost;
  const remainingSupply = stats.maxSupply - stats.totalMinted;

  // Handle video end - proceed to reveal
  const handleVideoEnd = () => {
    setRevealPhase('revealing');

    // After reveal animation, show complete with minted emissaries
    setTimeout(async () => {
      // Generate minted emissary cards based on quantity
      const guilds = ['Forge Legion', 'Circle of Mist', 'Order of Dawn', 'Shadow Guild', 'Horizon Watch', 'Void Echoes'];
      const newEmissaries: MintedEmissary[] = [];

      for (let i = 0; i < quantity; i++) {
        const tokenId = stats.totalMinted + i + 1;
        newEmissaries.push({
          token_id: `${tokenId}`,
          name: `Emissary #${tokenId}`,
          guild: guilds[Math.floor(Math.random() * guilds.length)],
          race_class: 'Awaiting Reveal...',
          image_url: `${CONTRACT_CONFIG.IPFS_IMAGES_BASE}${tokenId}.png`,
        });
      }

      setMintedEmissaries(newEmissaries);
      setRevealPhase('complete');

      // Refresh contract stats to get updated totalMinted
      await loadContractStats();

      if (newEmissaries.length > 0) {
        onMintSuccess?.(newEmissaries[0].token_id);
      }
    }, 1500);
  };

  // Handle mint
  const handleMint = async () => {
    if (!wallet || !canAfford || quantity > remainingSupply) return;

    setIsMinting(true);
    setError(null);
    setRevealPhase('minting');

    try {
      // Check if we have access to ethereum provider
      const ethereum = (window as any).ethereum;
      if (!ethereum) {
        // Demo mode - simulate mint
        await new Promise(resolve => setTimeout(resolve, 2000));
        setRevealPhase('video');
        return;
      }

      // Calculate value in wei (price * quantity)
      const priceWei = BigInt(Math.floor(stats.priceEth * 1e18));
      const totalWei = priceWei * BigInt(quantity);
      const valueHex = '0x' + totalWei.toString(16);

      // Encode mint(quantity) function call
      // mint(uint256) selector = 0xa0712d68
      const quantityHex = quantity.toString(16).padStart(64, '0');
      const data = '0xa0712d68' + quantityHex;

      // Send transaction
      const txHash = await ethereum.request({
        method: 'eth_sendTransaction',
        params: [{
          from: wallet,
          to: CONTRACT_CONFIG.CONTRACTS.EmberholmPortal,
          value: valueHex,
          data: data,
        }],
      });

      // Wait for transaction confirmation (simplified - just wait a bit then show video)
      console.log('Mint transaction sent:', txHash);

      // Poll for transaction receipt
      let confirmed = false;
      for (let i = 0; i < 60; i++) {
        await new Promise(resolve => setTimeout(resolve, 2000));
        try {
          const receipt = await ethereum.request({
            method: 'eth_getTransactionReceipt',
            params: [txHash],
          });
          if (receipt && receipt.status === '0x1') {
            confirmed = true;
            break;
          } else if (receipt && receipt.status === '0x0') {
            throw new Error('Transaction failed');
          }
        } catch (e) {
          // Receipt not available yet, continue polling
        }
      }

      if (!confirmed) {
        // Still show video but warn
        console.warn('Transaction not confirmed yet, showing video anyway');
      }

      // Start video reveal
      setRevealPhase('video');
    } catch (err: any) {
      console.error('Mint error:', err);
      setError(err.message || 'Mint failed');
      setRevealPhase('idle');
      setIsMinting(false);
    }
  };

  // Reset to mint again
  const handleMintAgain = () => {
    setMintedEmissaries([]);
    setRevealPhase('idle');
    setQuantity(1);
    setIsMinting(false);
    loadContractStats();
    loadEthBalance();
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
                    {stats.isLoading ? (
                      <span className="animate-pulse">...</span>
                    ) : (
                      stats.totalMinted.toLocaleString()
                    )}
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
                className="mb-4"
              >
                <Image
                  src="/icons/fire.png"
                  alt=""
                  width={64}
                  height={64}
                  className="pixel-icon mx-auto"
                />
              </motion.div>
              <div className="text-amber-bright text-xl">Minting...</div>
              <div className="text-amber-dim text-sm mt-2">
                Confirm transaction in your wallet
              </div>
            </motion.div>
          )}

          {revealPhase === 'video' && (
            <motion.div
              key="video"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="relative w-full max-w-sm aspect-square rounded-lg overflow-hidden"
            >
              <video
                ref={videoRef}
                src="/videos/portal.mp4"
                autoPlay
                muted
                playsInline
                onEnded={handleVideoEnd}
                className="w-full h-full object-cover"
              />
              <div className="absolute bottom-4 left-0 right-0 text-center">
                <div className="text-amber-bright text-lg animate-pulse">
                  Opening the Portal...
                </div>
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
                className="mb-4"
              >
                <Image
                  src="/icons/Sparkles.png"
                  alt=""
                  width={64}
                  height={64}
                  className="pixel-icon mx-auto"
                />
              </motion.div>
              <div className="text-amber-bright text-xl">Revealing...</div>
              <div className="text-amber-dim text-sm mt-2">
                Your Emissary is being summoned
              </div>
            </motion.div>
          )}

          {revealPhase === 'complete' && mintedEmissaries.length > 0 && (
            <motion.div
              key="complete"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="text-center w-full max-w-sm"
            >
              <div className="portal-box mb-6">
                <div className="ornament mb-4">═══ ◈ ═══</div>

                {/* Emissary cards - scrollable if multiple */}
                <div className={`${mintedEmissaries.length > 1 ? 'max-h-64 overflow-y-auto' : ''}`}>
                  {mintedEmissaries.map((emissary, index) => (
                    <motion.div
                      key={emissary.token_id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.2 }}
                      className={index > 0 ? 'mt-4 pt-4 border-t border-amber-dark' : ''}
                    >
                      <div className="relative mx-auto w-40 h-40 mb-3 rounded-lg border-2 border-amber
                                    bg-gradient-to-b from-amber-dark/20 to-dark
                                    flex items-center justify-center overflow-hidden">
                        <img
                          src={emissary.image_url}
                          alt={emissary.name}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none';
                          }}
                        />
                      </div>

                      <h2 className="title text-lg mb-1">{emissary.name}</h2>
                      <div className="text-amber text-sm">{emissary.guild}</div>
                      <div className="text-amber-dim text-xs mt-1">
                        {emissary.race_class}
                      </div>
                    </motion.div>
                  ))}
                </div>

                <div className="ornament mt-4">═══ ◈ ═══</div>
              </div>

              <div className="text-green text-sm mb-4">
                Congratulations! {mintedEmissaries.length > 1
                  ? `${mintedEmissaries.length} Emissaries have joined Emberholm.`
                  : 'Your Emissary has joined Emberholm.'}
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
