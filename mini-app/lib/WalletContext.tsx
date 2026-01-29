'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

/**
 * WalletContext - Unified wallet connection for Emberholm Portal
 * Supports:
 * 1. Farcaster Frame SDK (when running as a miniapp)
 * 2. Browser wallets (MetaMask, Coinbase Wallet, etc.)
 * 3. Demo mode for testing
 */

export type WalletType = 'farcaster' | 'metamask' | 'coinbase' | 'other' | null;

interface WalletState {
  address: string | null;
  isConnected: boolean;
  isConnecting: boolean;
  isFarcaster: boolean;
  walletType: WalletType;
  farcasterUser: FarcasterUser | null;
  error: string | null;
}

interface FarcasterUser {
  fid: number;
  username: string | null;
  displayName: string | null;
  pfpUrl: string | null;
}

interface WalletContextType extends WalletState {
  connect: () => Promise<void>;
  disconnect: () => void;
  enableDemoMode: () => void;
}

const WalletContext = createContext<WalletContextType | undefined>(undefined);

// Farcaster Frame SDK types (simplified)
interface FarcasterSDK {
  context?: {
    user?: {
      fid: number;
      username?: string;
      displayName?: string;
      pfpUrl?: string;
    };
  };
  actions?: {
    ready: () => void;
    openUrl: (url: string) => void;
  };
  wallet?: {
    ethProvider?: {
      request: (args: { method: string; params?: any[] }) => Promise<any>;
    };
  };
}

declare global {
  interface Window {
    ethereum?: {
      request: (args: { method: string; params?: any[] }) => Promise<any>;
      on: (event: string, callback: (...args: any[]) => void) => void;
      removeListener: (event: string, callback: (...args: any[]) => void) => void;
      isMetaMask?: boolean;
      isCoinbaseWallet?: boolean;
    };
    farcaster?: FarcasterSDK;
  }
}

interface WalletProviderProps {
  children: ReactNode;
}

export function WalletProvider({ children }: WalletProviderProps) {
  const [state, setState] = useState<WalletState>({
    address: null,
    isConnected: false,
    isConnecting: false,
    isFarcaster: false,
    walletType: null,
    farcasterUser: null,
    error: null,
  });

  // Check if running in Farcaster Frame
  const checkFarcasterContext = useCallback(async () => {
    try {
      // Try to import the Farcaster miniapp SDK dynamically
      // This allows the app to work even if the SDK is not available
      const sdk = window.farcaster;

      if (sdk?.context?.user) {
        const user = sdk.context.user;

        // Get wallet address from Farcaster
        let address: string | null = null;
        if (sdk.wallet?.ethProvider) {
          try {
            const accounts = await sdk.wallet.ethProvider.request({
              method: 'eth_requestAccounts',
            });
            address = accounts[0] || null;
          } catch (err) {
            console.warn('Failed to get Farcaster wallet:', err);
          }
        }

        setState(prev => ({
          ...prev,
          address,
          isConnected: !!address,
          isFarcaster: true,
          walletType: 'farcaster',
          farcasterUser: {
            fid: user.fid,
            username: user.username || null,
            displayName: user.displayName || null,
            pfpUrl: user.pfpUrl || null,
          },
        }));

        // Signal ready to Farcaster
        sdk.actions?.ready();
        return true;
      }
    } catch (err) {
      console.warn('Not running in Farcaster context:', err);
    }
    return false;
  }, []);

  // Detect wallet type from browser provider
  const detectWalletType = useCallback((): WalletType => {
    if (!window.ethereum) return null;
    if (window.ethereum.isCoinbaseWallet) return 'coinbase';
    if (window.ethereum.isMetaMask) return 'metamask';
    return 'other';
  }, []);

  // Connect to browser wallet
  const connectBrowserWallet = useCallback(async () => {
    if (!window.ethereum) {
      throw new Error('No wallet detected. Please install MetaMask or another wallet.');
    }

    const accounts = await window.ethereum.request({
      method: 'eth_requestAccounts',
    });

    if (accounts[0]) {
      const detectedWalletType = detectWalletType();
      setState(prev => ({
        ...prev,
        address: accounts[0],
        isConnected: true,
        isFarcaster: false,
        walletType: detectedWalletType,
        error: null,
      }));
    } else {
      throw new Error('No accounts found');
    }
  }, [detectWalletType]);

  // Main connect function
  const connect = useCallback(async () => {
    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    try {
      // First, try Farcaster
      const isFarcaster = await checkFarcasterContext();
      if (isFarcaster && state.isConnected) {
        setState(prev => ({ ...prev, isConnecting: false }));
        return;
      }

      // Fall back to browser wallet
      await connectBrowserWallet();
    } catch (err: any) {
      setState(prev => ({
        ...prev,
        error: err.message || 'Failed to connect wallet',
      }));
    } finally {
      setState(prev => ({ ...prev, isConnecting: false }));
    }
  }, [checkFarcasterContext, connectBrowserWallet, state.isConnected]);

  // Disconnect
  const disconnect = useCallback(() => {
    setState({
      address: null,
      isConnected: false,
      isConnecting: false,
      isFarcaster: false,
      walletType: null,
      farcasterUser: null,
      error: null,
    });
  }, []);

  // Enable demo mode for testing
  const enableDemoMode = useCallback(() => {
    const demoAddress = '0xDEMO' + Math.random().toString(16).slice(2, 10).toUpperCase().padEnd(36, '0');
    setState({
      address: demoAddress,
      isConnected: true,
      isConnecting: false,
      isFarcaster: false,
      walletType: 'other',
      farcasterUser: null,
      error: null,
    });
  }, []);

  // Listen for account changes
  useEffect(() => {
    const handleAccountsChanged = (accounts: string[]) => {
      if (accounts.length === 0) {
        disconnect();
      } else if (accounts[0] !== state.address) {
        setState(prev => ({
          ...prev,
          address: accounts[0],
          isConnected: true,
        }));
      }
    };

    if (window.ethereum) {
      window.ethereum.on('accountsChanged', handleAccountsChanged);
      return () => {
        window.ethereum?.removeListener('accountsChanged', handleAccountsChanged);
      };
    }
  }, [state.address, disconnect]);

  // Auto-connect on mount
  useEffect(() => {
    // Check Farcaster context on mount
    checkFarcasterContext();
  }, [checkFarcasterContext]);

  const value: WalletContextType = {
    ...state,
    connect,
    disconnect,
    enableDemoMode,
  };

  return (
    <WalletContext.Provider value={value}>
      {children}
    </WalletContext.Provider>
  );
}

// Hook for using wallet context
export function useWallet(): WalletContextType {
  const context = useContext(WalletContext);
  if (context === undefined) {
    throw new Error('useWallet must be used within a WalletProvider');
  }
  return context;
}

// Export types (WalletType is already exported at the top)
export type { WalletState, FarcasterUser, WalletContextType };
