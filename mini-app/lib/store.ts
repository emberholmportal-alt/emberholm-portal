/**
 * EMBERHOLM MINI APP - Global State Store
 * Simple React context-based store for app state
 */

import { createContext, useContext, useReducer, ReactNode } from 'react';
import { Emissary, RealmStatus, ActiveMicroMission } from './api';

// =========================================
// State Types
// =========================================

export type AppScreen =
  | 'intro'
  | 'welcome'
  | 'menu'
  | 'emissaries'
  | 'mission-select'
  | 'mission-play'
  | 'mission-complete'
  | 'vault';

export interface AppState {
  // Navigation
  currentScreen: AppScreen;
  previousScreen: AppScreen | null;

  // User
  wallet: string | null;
  isConnected: boolean;

  // Realm
  realmStatus: RealmStatus | null;

  // Emissaries
  emissaries: Emissary[];
  selectedEmissary: Emissary | null;

  // $SPARK
  sparkBalance: number;

  // Active Mission
  activeMission: ActiveMicroMission | null;
  selectedMissionId: string | null;

  // UI State
  isLoading: boolean;
  error: string | null;
  introComplete: boolean;
}

// =========================================
// Actions
// =========================================

type AppAction =
  | { type: 'SET_SCREEN'; screen: AppScreen }
  | { type: 'SET_WALLET'; wallet: string | null }
  | { type: 'SET_CONNECTED'; isConnected: boolean }
  | { type: 'SET_REALM_STATUS'; status: RealmStatus }
  | { type: 'SET_EMISSARIES'; emissaries: Emissary[] }
  | { type: 'SELECT_EMISSARY'; emissary: Emissary | null }
  | { type: 'SET_SPARK_BALANCE'; balance: number }
  | { type: 'SET_ACTIVE_MISSION'; mission: ActiveMicroMission | null }
  | { type: 'SELECT_MISSION'; missionId: string | null }
  | { type: 'SET_LOADING'; isLoading: boolean }
  | { type: 'SET_ERROR'; error: string | null }
  | { type: 'COMPLETE_INTRO' }
  | { type: 'RESET' };

// =========================================
// Initial State
// =========================================

const initialState: AppState = {
  currentScreen: 'intro',
  previousScreen: null,
  wallet: null,
  isConnected: false,
  realmStatus: null,
  emissaries: [],
  selectedEmissary: null,
  sparkBalance: 0,
  activeMission: null,
  selectedMissionId: null,
  isLoading: false,
  error: null,
  introComplete: false,
};

// =========================================
// Reducer
// =========================================

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_SCREEN':
      return {
        ...state,
        previousScreen: state.currentScreen,
        currentScreen: action.screen,
      };

    case 'SET_WALLET':
      return {
        ...state,
        wallet: action.wallet,
        isConnected: !!action.wallet,
      };

    case 'SET_CONNECTED':
      return {
        ...state,
        isConnected: action.isConnected,
      };

    case 'SET_REALM_STATUS':
      return {
        ...state,
        realmStatus: action.status,
      };

    case 'SET_EMISSARIES':
      return {
        ...state,
        emissaries: action.emissaries,
      };

    case 'SELECT_EMISSARY':
      return {
        ...state,
        selectedEmissary: action.emissary,
      };

    case 'SET_SPARK_BALANCE':
      return {
        ...state,
        sparkBalance: action.balance,
      };

    case 'SET_ACTIVE_MISSION':
      return {
        ...state,
        activeMission: action.mission,
      };

    case 'SELECT_MISSION':
      return {
        ...state,
        selectedMissionId: action.missionId,
      };

    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.isLoading,
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.error,
      };

    case 'COMPLETE_INTRO':
      return {
        ...state,
        introComplete: true,
        currentScreen: 'welcome',
      };

    case 'RESET':
      return {
        ...initialState,
        realmStatus: state.realmStatus, // Keep realm status
      };

    default:
      return state;
  }
}

// =========================================
// Context
// =========================================

interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// =========================================
// Provider
// =========================================

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

// =========================================
// Hook
// =========================================

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
}

// =========================================
// Action Helpers
// =========================================

export const actions = {
  setScreen: (screen: AppScreen): AppAction => ({ type: 'SET_SCREEN', screen }),
  setWallet: (wallet: string | null): AppAction => ({ type: 'SET_WALLET', wallet }),
  setConnected: (isConnected: boolean): AppAction => ({ type: 'SET_CONNECTED', isConnected }),
  setRealmStatus: (status: RealmStatus): AppAction => ({ type: 'SET_REALM_STATUS', status }),
  setEmissaries: (emissaries: Emissary[]): AppAction => ({ type: 'SET_EMISSARIES', emissaries }),
  selectEmissary: (emissary: Emissary | null): AppAction => ({ type: 'SELECT_EMISSARY', emissary }),
  setSparkBalance: (balance: number): AppAction => ({ type: 'SET_SPARK_BALANCE', balance }),
  setActiveMission: (mission: ActiveMicroMission | null): AppAction => ({ type: 'SET_ACTIVE_MISSION', mission }),
  selectMission: (missionId: string | null): AppAction => ({ type: 'SELECT_MISSION', missionId }),
  setLoading: (isLoading: boolean): AppAction => ({ type: 'SET_LOADING', isLoading }),
  setError: (error: string | null): AppAction => ({ type: 'SET_ERROR', error }),
  completeIntro: (): AppAction => ({ type: 'COMPLETE_INTRO' }),
  reset: (): AppAction => ({ type: 'RESET' }),
};
