'use client';

import { useState, useEffect, useCallback } from 'react';
import { CRTOverlay } from '@/components/CRTOverlay';
import { ImmersionBar } from '@/components/ImmersionBar';
import { EnterPortal } from '@/components/screens/EnterPortal';
import { WelcomeOperator } from '@/components/screens/WelcomeOperator';
import { MainMenu } from '@/components/screens/MainMenu';
import { EmissaryList } from '@/components/screens/EmissaryList';
import { MissionSelect } from '@/components/screens/MissionSelect';
import { MissionPlayer } from '@/components/screens/MissionPlayer';
import {
  Emissary,
  MicroMission,
  getWalletEmissaries,
  getSparkBalance,
  getActiveMicroMission,
} from '@/lib/api';

/**
 * Main App Page
 * Handles navigation between screens and state management
 */

type Screen = 'intro' | 'welcome' | 'menu' | 'emissaries' | 'mission-select' | 'mission-play';

export default function Home() {
  // Navigation
  const [currentScreen, setCurrentScreen] = useState<Screen>('intro');

  // Wallet (simplified - in production use wagmi)
  const [wallet, setWallet] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  // Data
  const [emissaries, setEmissaries] = useState<Emissary[]>([]);
  const [selectedEmissary, setSelectedEmissary] = useState<Emissary | null>(null);
  const [selectedMission, setSelectedMission] = useState<MicroMission | null>(null);
  const [sparkBalance, setSparkBalance] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  // Check for existing wallet connection
  useEffect(() => {
    // In production, this would check wagmi/rainbow kit state
    const savedWallet = localStorage.getItem('emberholm_wallet');
    if (savedWallet) {
      setWallet(savedWallet);
      setIsConnected(true);
    }
  }, []);

  // Load data when wallet is connected
  useEffect(() => {
    if (!wallet) return;

    async function loadData() {
      try {
        setIsLoading(true);

        // Load emissaries
        const emissariesData = await getWalletEmissaries(wallet);
        setEmissaries(emissariesData);

        // Load spark balance
        const sparkData = await getSparkBalance(wallet);
        setSparkBalance(sparkData.balance);

        // Check for active micro-mission
        const activeMission = await getActiveMicroMission(wallet);
        if (activeMission) {
          // If there's an active mission, we could restore that state
          console.log('Active mission found:', activeMission);
        }
      } catch (error) {
        console.error('Failed to load data:', error);
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, [wallet]);

  // Simulated wallet connect (in production use wagmi)
  const handleConnect = useCallback(async () => {
    try {
      // Check if window.ethereum exists
      if (typeof window !== 'undefined' && (window as any).ethereum) {
        const accounts = await (window as any).ethereum.request({
          method: 'eth_requestAccounts',
        });
        if (accounts[0]) {
          setWallet(accounts[0].toLowerCase());
          setIsConnected(true);
          localStorage.setItem('emberholm_wallet', accounts[0].toLowerCase());
        }
      } else {
        // Demo mode - use a placeholder wallet
        const demoWallet = '0x0000000000000000000000000000000000000000';
        setWallet(demoWallet);
        setIsConnected(true);
        localStorage.setItem('emberholm_wallet', demoWallet);
      }
    } catch (error) {
      console.error('Failed to connect:', error);
    }
  }, []);

  // Navigation handlers
  const handleEnterPortal = () => setCurrentScreen('welcome');
  const handleWelcomeComplete = () => setCurrentScreen('menu');

  const handleNavigate = (screen: 'emissaries' | 'mission-select' | 'vault') => {
    if (screen === 'vault') {
      // TODO: Implement vault screen
      alert('Vault coming soon!');
      return;
    }
    setCurrentScreen(screen);
  };

  const handleSelectEmissary = (emissary: Emissary) => {
    setSelectedEmissary(emissary);
    setCurrentScreen('mission-select');
  };

  const handleSelectMission = (mission: MicroMission) => {
    if (!selectedEmissary) {
      setCurrentScreen('emissaries');
      return;
    }
    setSelectedMission(mission);
    setCurrentScreen('mission-play');
  };

  const handleMissionComplete = async (rewards: { spark: number; xp: number; aura: number }) => {
    // Update spark balance
    setSparkBalance((prev) => prev + rewards.spark);

    // Refresh emissary data
    if (wallet) {
      const emissariesData = await getWalletEmissaries(wallet);
      setEmissaries(emissariesData);
    }

    // Go back to menu
    setSelectedMission(null);
    setCurrentScreen('menu');
  };

  const handleBack = () => {
    switch (currentScreen) {
      case 'emissaries':
      case 'mission-select':
        setCurrentScreen('menu');
        break;
      case 'mission-play':
        setSelectedMission(null);
        setCurrentScreen('mission-select');
        break;
      default:
        setCurrentScreen('menu');
    }
  };

  // Show immersion bar on all screens except intro
  const showImmersionBar = currentScreen !== 'intro' && currentScreen !== 'welcome';

  return (
    <main className="app-container relative">
      {/* CRT Effects */}
      <CRTOverlay />

      {/* Immersion Bar */}
      {showImmersionBar && <ImmersionBar />}

      {/* Screens */}
      {currentScreen === 'intro' && (
        <EnterPortal onEnter={handleEnterPortal} />
      )}

      {currentScreen === 'welcome' && (
        <WelcomeOperator onComplete={handleWelcomeComplete} />
      )}

      {currentScreen === 'menu' && (
        <MainMenu
          sparkBalance={sparkBalance}
          emissaryCount={emissaries.length}
          onNavigate={handleNavigate}
          onConnect={handleConnect}
          isConnected={isConnected}
        />
      )}

      {currentScreen === 'emissaries' && (
        <EmissaryList
          emissaries={emissaries}
          onSelect={handleSelectEmissary}
          onBack={handleBack}
          isLoading={isLoading}
        />
      )}

      {currentScreen === 'mission-select' && (
        <MissionSelect
          selectedEmissary={selectedEmissary}
          onSelectMission={handleSelectMission}
          onBack={handleBack}
          onSelectEmissary={() => setCurrentScreen('emissaries')}
        />
      )}

      {currentScreen === 'mission-play' && selectedMission && selectedEmissary && wallet && (
        <MissionPlayer
          mission={selectedMission}
          emissary={selectedEmissary}
          wallet={wallet}
          onComplete={handleMissionComplete}
          onCancel={handleBack}
        />
      )}
    </main>
  );
}
