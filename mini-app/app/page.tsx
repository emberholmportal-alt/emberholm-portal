'use client';

import { useEffect, useCallback } from 'react';
import { CRTOverlay } from '@/components/CRTOverlay';
import { ImmersionBar } from '@/components/ImmersionBar';
import { WelcomeScreen } from '@/components/screens/WelcomeScreen';
import { BootSequence } from '@/components/screens/BootSequence';
import { CountrySelect } from '@/components/screens/CountrySelect';
import { PortalEntry } from '@/components/screens/PortalEntry';
import { MainMenu } from '@/components/screens/MainMenu';
import { EmissaryList } from '@/components/screens/EmissaryList';
import { MissionSelect } from '@/components/screens/MissionSelect';
import { MissionPlayer } from '@/components/screens/MissionPlayer';
import { useApp, actions, AppScreen, AppProvider } from '@/lib/store';
import {
  Emissary,
  MicroMission,
  getWalletEmissaries,
  getPyreBalance,
  getActiveMicroMission,
  updateProfile,
} from '@/lib/api';

/**
 * Main App Page
 * Handles navigation between screens using global store
 */

function AppContent() {
  const { state, dispatch } = useApp();

  // Check for existing wallet connection on mount
  useEffect(() => {
    const savedWallet = localStorage.getItem('emberholm_wallet');
    const savedCountry = localStorage.getItem('emberholm_country');
    const skipIntro = localStorage.getItem('emberholm_skip_intro');

    if (savedWallet) {
      dispatch(actions.setWallet(savedWallet));
    }

    // If returning user with saved data, skip to menu
    if (skipIntro === 'true' && savedCountry) {
      dispatch(actions.setScreen('menu'));
    }
  }, [dispatch]);

  // Load data when wallet is connected
  useEffect(() => {
    if (!state.wallet) return;

    async function loadData() {
      try {
        dispatch(actions.setLoading(true));

        // Load emissaries
        const emissaries = await getWalletEmissaries(state.wallet!);
        dispatch(actions.setEmissaries(emissaries));

        // Load PYRE balance
        const pyreData = await getPyreBalance(state.wallet!);
        dispatch(actions.setPyreBalance(
          pyreData.balance,
          pyreData.total_earned,
          pyreData.daily_available
        ));

        // Check for active micro-mission
        const activeMission = await getActiveMicroMission(state.wallet!);
        if (activeMission) {
          dispatch(actions.setActiveMission(activeMission));
        }
      } catch (error) {
        console.error('Failed to load data:', error);
        dispatch(actions.setError('Failed to load data'));
      } finally {
        dispatch(actions.setLoading(false));
      }
    }

    loadData();
  }, [state.wallet, dispatch]);

  // Wallet connection handler
  const handleConnect = useCallback(async () => {
    try {
      if (typeof window !== 'undefined' && (window as any).ethereum) {
        const accounts = await (window as any).ethereum.request({
          method: 'eth_requestAccounts',
        });
        if (accounts[0]) {
          const wallet = accounts[0].toLowerCase();
          dispatch(actions.setWallet(wallet));
          localStorage.setItem('emberholm_wallet', wallet);
        }
      } else {
        // Demo mode - use a placeholder wallet
        const demoWallet = '0x0000000000000000000000000000000000000000';
        dispatch(actions.setWallet(demoWallet));
        localStorage.setItem('emberholm_wallet', demoWallet);
      }
    } catch (error) {
      console.error('Failed to connect:', error);
      dispatch(actions.setError('Failed to connect wallet'));
    }
  }, [dispatch]);

  // Navigation handlers
  const handleNavigate = (screen: AppScreen) => {
    dispatch(actions.setScreen(screen));
  };

  const handleBack = () => {
    dispatch(actions.goBack());
  };

  // Intro flow handlers
  const handleWelcomeEnter = () => {
    dispatch(actions.setScreen('country-select'));
  };

  const handleBootComplete = () => {
    dispatch(actions.setScreen('country-select'));
  };

  const handleCountrySelect = async (countryCode: string) => {
    dispatch(actions.selectCountry(countryCode));

    // Update profile with country if wallet is connected
    if (state.wallet) {
      try {
        await updateProfile({
          wallet: state.wallet,
          country_code: countryCode,
        });
      } catch (error) {
        console.error('Failed to update profile:', error);
      }
    }

    dispatch(actions.setScreen('portal-entry'));
  };

  const handlePortalEnter = () => {
    dispatch(actions.setScreen('menu'));
    dispatch(actions.resetHistory());
  };

  // Emissary handlers
  const handleSelectEmissary = (emissary: Emissary) => {
    dispatch(actions.selectEmissary(emissary));
    dispatch(actions.setScreen('mission-select'));
  };

  // Mission handlers
  const handleSelectMission = (mission: MicroMission) => {
    if (!state.selectedEmissary) {
      dispatch(actions.setScreen('emissary-detail'));
      return;
    }
    dispatch(actions.selectMission(mission.id));
    dispatch(actions.setScreen('timer'));
  };

  const handleMissionComplete = async (rewards: { pyre: number; xp: number; aura: number }) => {
    // Update PYRE balance
    dispatch(actions.setPyreBalance(state.pyreBalance + rewards.pyre));

    // Refresh emissary data
    if (state.wallet) {
      const emissaries = await getWalletEmissaries(state.wallet);
      dispatch(actions.setEmissaries(emissaries));
    }

    // Clear mission state and go back to menu
    dispatch(actions.setActiveMission(null));
    dispatch(actions.selectMission(null));
    dispatch(actions.setScreen('menu'));
  };

  // Determine which screens should show the top bar
  const showTopBar = !['welcome', 'country-select', 'portal-entry'].includes(state.currentScreen);

  return (
    <main className="crt-screen relative">
      {/* CRT Effects */}
      <CRTOverlay />

      {/* Top Bar (Immersion Bar) - only on main screens */}
      {showTopBar && <ImmersionBar />}

      {/* Screen Content */}
      <div className="screen-content">
        {/* Intro Flow */}
        {state.currentScreen === 'welcome' && (
          <WelcomeScreen onEnter={handleWelcomeEnter} />
        )}

        {state.currentScreen === 'country-select' && (
          <CountrySelect
            onSelect={handleCountrySelect}
            onBack={handleBack}
          />
        )}

        {state.currentScreen === 'portal-entry' && (
          <PortalEntry
            onEnter={handlePortalEnter}
            onBack={handleBack}
          />
        )}

        {/* Main Menu */}
        {state.currentScreen === 'menu' && (
          <MainMenu
            pyreBalance={state.pyreBalance}
            emissaryCount={state.emissaries.length}
            unreadMessages={state.unreadCount}
            onNavigate={handleNavigate}
          />
        )}

        {/* Play Section */}
        {state.currentScreen === 'play' && (
          <EmissaryList
            emissaries={state.emissaries}
            onSelect={handleSelectEmissary}
            onBack={handleBack}
            isLoading={state.isLoading}
          />
        )}

        {state.currentScreen === 'micro-missions' && (
          <MissionSelect
            selectedEmissary={state.selectedEmissary}
            onSelectMission={handleSelectMission}
            onBack={handleBack}
            onSelectEmissary={() => handleNavigate('play')}
          />
        )}

        {state.currentScreen === 'timer' && state.selectedMissionId && state.selectedEmissary && state.wallet && (
          <MissionPlayer
            mission={{ id: state.selectedMissionId } as MicroMission}
            emissary={state.selectedEmissary}
            wallet={state.wallet}
            onComplete={handleMissionComplete}
            onCancel={handleBack}
          />
        )}

        {/* Placeholder screens - to be implemented */}
        {state.currentScreen === 'mint' && (
          <PlaceholderScreen title="MINT EMISSARY" onBack={handleBack} />
        )}

        {state.currentScreen === 'vault' && (
          <PlaceholderScreen title="VAULT" onBack={handleBack} />
        )}

        {state.currentScreen === 'events' && (
          <PlaceholderScreen title="EVENTS" onBack={handleBack} />
        )}

        {state.currentScreen === 'lore' && (
          <PlaceholderScreen title="LORE" onBack={handleBack} />
        )}

        {state.currentScreen === 'tutorial' && (
          <PlaceholderScreen title="TUTORIAL" onBack={handleBack} />
        )}

        {state.currentScreen === 'social-globe' && (
          <PlaceholderScreen title="WORLD MAP" onBack={handleBack} />
        )}

        {state.currentScreen === 'social-users' && (
          <PlaceholderScreen title="USERS" onBack={handleBack} />
        )}

        {state.currentScreen === 'chat' && (
          <PlaceholderScreen title="CHAT" onBack={handleBack} />
        )}

        {state.currentScreen === 'leaderboard' && (
          <PlaceholderScreen title="LEADERBOARD" onBack={handleBack} />
        )}

        {state.currentScreen === 'pyre-guide' && (
          <PlaceholderScreen title="$PYRE GUIDE" onBack={handleBack} />
        )}
      </div>
    </main>
  );
}

// Placeholder component for screens not yet implemented
function PlaceholderScreen({ title, onBack }: { title: string; onBack: () => void }) {
  return (
    <div className="screen-view flex flex-col min-h-screen p-4">
      <div className="flex-1 flex items-center justify-center">
        <div className="portal-box">
          <div className="ornament">═══ ◈ ═══</div>
          <h2 className="title text-xl my-6">{title}</h2>
          <p className="text-amber-dim text-sm">Coming soon...</p>
          <div className="ornament mt-4">═══ ◈ ═══</div>
        </div>
      </div>
      <button onClick={onBack} className="back-btn">
        ← BACK
      </button>
    </div>
  );
}

// Wrap with AppProvider
export default function Home() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}
