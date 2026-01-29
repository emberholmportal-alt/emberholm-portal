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

/**
 * WalletContext - Unified wallet connection for Farcaster Mini App + Browser
 *
 * Priority:
 * 1. Farcaster Frame SDK (when running inside Warpcast)
 * 2. Injected wallet (MetaMask, Coinbase, etc.)
 * 3. Demo mode (for testing)
 */

interface WalletState {
  address: string | null;
  isConnected: boolean;
  isConnecting: boolean;
  isFarcaster: boolean;
  farcasterUser: {
    fid: number | null;
    username: string | null;
    displayName: string | null;
    pfpUrl: string | null;
  } | null;
  error: string | null;
}

interface WalletContextType extends WalletState {
  connect: () => Promise<void>;
  disconnect: () => void;
  isFrameReady: boolean;
}

const WalletContext = createContext<WalletContextType | null>(null);

export function WalletProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<WalletState>({
    address: null,
    isConnected: false,
    isConnecting: false,
    isFarcaster: false,
    farcasterUser: null,
    error: null,
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

  // Connect wallet
  const connect = useCallback(async () => {
    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    try {
      // Method 1: Farcaster Frame SDK
      if (isInFrame) {
        try {
          // Request wallet connection through Farcaster
          const result = await sdk.wallet.ethProvider.request({
            method: 'eth_requestAccounts',
          });

          if (result && result[0]) {
            const address = result[0].toLowerCase();
            localStorage.setItem('emberholm_wallet', address);
            setState(prev => ({
              ...prev,
              address,
              isConnected: true,
              isConnecting: false,
              isFarcaster: true,
            }));
            return;
          }
        } catch (frameError) {
          console.log('Farcaster wallet connection failed, trying browser wallet');
        }
      }

      // Method 2: Browser injected wallet (MetaMask, Coinbase, etc.)
      if (typeof window !== 'undefined' && (window as any).ethereum) {
        const accounts = await (window as any).ethereum.request({
          method: 'eth_requestAccounts',
        });

        if (accounts && accounts[0]) {
          const address = accounts[0].toLowerCase();
          localStorage.setItem('emberholm_wallet', address);
          setState(prev => ({
            ...prev,
            address,
            isConnected: true,
            isConnecting: false,
            isFarcaster: false,
          }));
          return;
        }
      }

      // Method 3: Demo mode (no wallet available)
      console.log('No wallet detected, using demo mode');
      const demoWallet = '0x0000000000000000000000000000000000000000';
      localStorage.setItem('emberholm_wallet', demoWallet);
      setState(prev => ({
        ...prev,
        address: demoWallet,
        isConnected: true,
        isConnecting: false,
        isFarcaster: false,
      }));

    } catch (error: any) {
      console.error('Wallet connection failed:', error);
      setState(prev => ({
        ...prev,
        isConnecting: false,
        error: error.message || 'Failed to connect wallet',
      }));
    }
  }, [isInFrame]);

  // Disconnect wallet
  const disconnect = useCallback(() => {
    localStorage.removeItem('emberholm_wallet');
    setState({
      address: null,
      isConnected: false,
      isConnecting: false,
      isFarcaster: false,
      farcasterUser: null,
      error: null,
    });
  }, []);

  return (
    <WalletContext.Provider
      value={{
        ...state,
        connect,
        disconnect,
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
