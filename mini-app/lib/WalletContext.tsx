'use client';

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  ReactNode,
} from 'react';
import sdk from '@farcaster/miniapp-sdk';
import { createPublicClient, http, parseAbi } from 'viem';
import { base } from 'viem/chains';
import { registerWalletNFTs } from './api';
import { CONTRACT_CONFIG } from './contracts';

/**
 * WalletContext - Unified wallet connection for Farcaster Mini App + Browser
 *
 * Priority:
 * 1. Farcaster Frame SDK (when running inside Warpcast)
 * 2. Injected wallet (MetaMask, Coinbase, etc.)
 * 3. Demo mode (for testing)
 *
 * CRITICAL: After connection, queries blockchain for NFTs and syncs to backend
 */

// Public client for reading blockchain data
const publicClient = createPublicClient({
  chain: base,
  transport: http(CONTRACT_CONFIG.RPC_URL),
});

// ABI for tokensOfOwner
const EMISSARY_ABI = parseAbi([
  'function tokensOfOwner(address owner) view returns (uint256[])',
  'function totalSupply() view returns (uint256)',
]);

interface WalletState {
  address: string | null;
  isConnected: boolean;
  isConnecting: boolean;
  isSyncing: boolean;
  isFarcaster: boolean;
  farcasterUser: {
    fid: number | null;
    username: string | null;
    displayName: string | null;
    pfpUrl: string | null;
  } | null;
  error: string | null;
  nftCount: number;
}

interface WalletContextType extends WalletState {
  connect: () => Promise<void>;
  disconnect: () => void;
  syncNFTs: () => Promise<void>;
  isFrameReady: boolean;
}

const WalletContext = createContext<WalletContextType | null>(null);

/**
 * Query blockchain for wallet's NFTs and sync to backend
 * Replicates portal web flow: tokensOfOwner() -> POST /api/player
 */
async function syncWalletNFTs(address: string): Promise<{ tokenIds: string[]; totalSupply: number }> {
  console.log(`[syncWalletNFTs] Querying blockchain for ${address.slice(0, 8)}...`);

  try {
    // Query tokensOfOwner from EmberholmPortal contract
    const [tokenIds, totalSupply] = await Promise.all([
      publicClient.readContract({
        address: CONTRACT_CONFIG.CONTRACTS.EmberholmPortal as `0x${string}`,
        abi: EMISSARY_ABI,
        functionName: 'tokensOfOwner',
        args: [address as `0x${string}`],
      }),
      publicClient.readContract({
        address: CONTRACT_CONFIG.CONTRACTS.EmberholmPortal as `0x${string}`,
        abi: EMISSARY_ABI,
        functionName: 'totalSupply',
      }),
    ]);

    // Convert BigInt[] to padded string[] (format: "00001", "00002", etc.)
    const tokenIdStrings = (tokenIds as bigint[]).map(id =>
      id.toString().padStart(5, '0')
    );

    console.log(`[syncWalletNFTs] Found ${tokenIdStrings.length} NFTs on blockchain`);
    console.log(`[syncWalletNFTs] Token IDs: ${tokenIdStrings.join(', ')}`);
    console.log(`[syncWalletNFTs] Total supply: ${totalSupply}`);

    // POST to backend to register NFTs (critical step!)
    if (tokenIdStrings.length > 0) {
      const result = await registerWalletNFTs(
        address,
        tokenIdStrings,
        Number(totalSupply)
      );
      console.log(`[syncWalletNFTs] Backend sync result:`, result);
    }

    return {
      tokenIds: tokenIdStrings,
      totalSupply: Number(totalSupply),
    };
  } catch (error) {
    console.error('[syncWalletNFTs] Blockchain query failed:', error);
    return { tokenIds: [], totalSupply: 0 };
  }
}

export function WalletProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<WalletState>({
    address: null,
    isConnected: false,
    isConnecting: false,
    isSyncing: false,
    isFarcaster: false,
    farcasterUser: null,
    error: null,
    nftCount: 0,
  });
  const [isFrameReady, setIsFrameReady] = useState(false);
  const [isInFrame, setIsInFrame] = useState(false);

  // Initialize - detect if we're in a Farcaster frame
  useEffect(() => {
    async function initFrame() {
      try {
        // Check if we're in a Farcaster frame context
        const context = await sdk.context;

        if (context) {
          setIsInFrame(true);

          // Get user info from Farcaster
          if (context.user) {
            setState(prev => ({
              ...prev,
              isFarcaster: true,
              farcasterUser: {
                fid: context.user?.fid || null,
                username: context.user?.username || null,
                displayName: context.user?.displayName || null,
                pfpUrl: context.user?.pfpUrl || null,
              },
            }));
          }

          // Mark frame as ready (shows the UI in Warpcast)
          await sdk.actions.ready();
        }

        setIsFrameReady(true);
      } catch (error) {
        console.log('Not in Farcaster frame, using browser wallet mode');
        setIsFrameReady(true);
      }
    }

    // Check for saved wallet on mount
    const savedWallet = localStorage.getItem('emberholm_wallet');
    if (savedWallet) {
      setState(prev => ({
        ...prev,
        address: savedWallet,
        isConnected: true,
      }));
    }

    initFrame();
  }, []);

  // Helper to sync NFTs after connection
  const performNFTSync = useCallback(async (address: string) => {
    if (address === '0x0000000000000000000000000000000000000000') {
      console.log('[performNFTSync] Demo mode - skipping blockchain sync');
      return;
    }

    setState(prev => ({ ...prev, isSyncing: true }));

    try {
      const { tokenIds } = await syncWalletNFTs(address);
      setState(prev => ({
        ...prev,
        isSyncing: false,
        nftCount: tokenIds.length,
      }));
    } catch (error) {
      console.error('[performNFTSync] Error:', error);
      setState(prev => ({ ...prev, isSyncing: false }));
    }
  }, []);

  // Public sync function (can be called manually to refresh)
  const syncNFTs = useCallback(async () => {
    if (state.address && state.address !== '0x0000000000000000000000000000000000000000') {
      await performNFTSync(state.address);
    }
  }, [state.address, performNFTSync]);

  // Connect wallet
  const connect = useCallback(async () => {
    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    let connectedAddress: string | null = null;
    let isFarcasterConnection = false;

    try {
      // Method 1: Farcaster Frame SDK
      if (isInFrame) {
        try {
          // Request wallet connection through Farcaster
          const result = await sdk.wallet.ethProvider.request({
            method: 'eth_requestAccounts',
          });

          if (result && result[0]) {
            connectedAddress = result[0].toLowerCase();
            isFarcasterConnection = true;
          }
        } catch (frameError) {
          console.log('Farcaster wallet connection failed, trying browser wallet');
        }
      }

      // Method 2: Browser injected wallet (MetaMask, Coinbase, etc.)
      if (!connectedAddress && typeof window !== 'undefined' && (window as any).ethereum) {
        const accounts = await (window as any).ethereum.request({
          method: 'eth_requestAccounts',
        });

        if (accounts && accounts[0]) {
          connectedAddress = accounts[0].toLowerCase();
          isFarcasterConnection = false;
        }
      }

      // Method 3: Demo mode (no wallet available)
      if (!connectedAddress) {
        console.log('No wallet detected, using demo mode');
        connectedAddress = '0x0000000000000000000000000000000000000000';
        isFarcasterConnection = false;
      }

      // Save and update state
      localStorage.setItem('emberholm_wallet', connectedAddress);
      setState(prev => ({
        ...prev,
        address: connectedAddress,
        isConnected: true,
        isConnecting: false,
        isFarcaster: isFarcasterConnection,
      }));

      // CRITICAL: Sync NFTs to backend after successful connection
      // This replicates the portal web flow: connect -> query blockchain -> POST token_ids
      await performNFTSync(connectedAddress);

    } catch (error: any) {
      console.error('Wallet connection failed:', error);
      setState(prev => ({
        ...prev,
        isConnecting: false,
        error: error.message || 'Failed to connect wallet',
      }));
    }
  }, [isInFrame, performNFTSync]);

  // Disconnect wallet
  const disconnect = useCallback(() => {
    localStorage.removeItem('emberholm_wallet');
    setState({
      address: null,
      isConnected: false,
      isConnecting: false,
      isSyncing: false,
      isFarcaster: false,
      farcasterUser: null,
      error: null,
      nftCount: 0,
    });
  }, []);

  // Auto-sync NFTs when wallet is restored from localStorage
  useEffect(() => {
    if (state.address && state.isConnected && !state.isSyncing && state.nftCount === 0) {
      // Only sync if we have an address and haven't synced yet
      if (state.address !== '0x0000000000000000000000000000000000000000') {
        console.log('[WalletContext] Auto-syncing NFTs for restored wallet');
        performNFTSync(state.address);
      }
    }
  }, [state.address, state.isConnected, state.isSyncing, state.nftCount, performNFTSync]);

  return (
    <WalletContext.Provider
      value={{
        ...state,
        connect,
        disconnect,
        syncNFTs,
        isFrameReady,
      }}
    >
      {children}
    </WalletContext.Provider>
  );
}

export function useWallet() {
  const context = useContext(WalletContext);
  if (!context) {
    throw new Error('useWallet must be used within WalletProvider');
  }
  return context;
}

export default WalletContext;
