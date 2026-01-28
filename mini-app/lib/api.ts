/**
 * EMBERHOLM MINI APP - API Client
 * Connects to Flask backend endpoints
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

// =========================================
// Types
// =========================================

export interface RealmStatus {
  date: string;
  time: string;
  era: string;
  year: number;
  weather: {
    name: string;
    icon: string;
    description: string;
  };
  flame: {
    name: string;
    color: string;
    description: string;
  };
}

export interface SparkBalance {
  wallet: string;
  balance: number;
  total_earned: number;
  total_spent: number;
  daily_streak: number;
  daily_available: boolean;
}

export interface MicroMission {
  id: string;
  name: string;
  description: string;
  difficulty: 'EASY' | 'MEDIUM' | 'HARD';
  duration_seconds: number;
  energy_cost: number;
  spark_reward: { min: number; max: number };
  xp_reward: { min: number; max: number };
  aura_chance: number;
  narrative_intro: string;
  cooldown_minutes: number;
}

export interface MicroMissionDetail extends MicroMission {
  narrative_choices: {
    id: string;
    text: string;
    icon?: string;
  }[];
  narrative_outcomes: Record<string, {
    type: string;
    text: string;
    spark_modifier: number;
    xp_modifier: number;
  }>;
}

export interface ActiveMicroMission {
  active_id: number;
  emissary_token_id: string;
  mission_id: string;
  started_at: string;
  ends_at: string;
  remaining_seconds: number;
  status: string;
  choice_made: string | null;
  name: string;
  narrative_intro: string;
  choices: { id: string; text: string; icon?: string }[];
}

export interface Emissary {
  token_id: string;
  name: string;
  guild: string;
  race_class: string;
  owner: string;
  image_url: string;
  stats: {
    level: number;
    xp_total: number;
    aura_level: number;
    energy_current: number;
    energy_max: number;
    power: number;
    death_count: number;
  };
  current_state: 'READY' | 'ON_MISSION' | 'ON_MICRO_MISSION' | 'FALLEN' | 'CLAIMING';
  active_mission: any | null;
  active_micro_mission: any | null;
  equipment: Record<string, string | null>;
  chronicle: {
    total_missions: number;
    total_deaths: number;
    items_found: number;
    runes_found: number;
  };
}

export interface MissionRewards {
  spark: number;
  xp: number;
  aura: number;
}

// =========================================
// API Functions
// =========================================

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || `API Error: ${response.status}`);
  }

  return response.json();
}

// =========================================
// Realm Status
// =========================================

export async function getRealmStatus(): Promise<RealmStatus> {
  const data = await fetchAPI<{ success: boolean; realm: RealmStatus }>('/api/realm-status');
  return data.realm;
}

// =========================================
// $SPARK
// =========================================

export async function getSparkBalance(wallet: string): Promise<SparkBalance> {
  const data = await fetchAPI<{ success: boolean } & SparkBalance>(`/api/spark/${wallet}`);
  return data;
}

// =========================================
// Micro-Missions
// =========================================

export async function getMicroMissions(): Promise<MicroMission[]> {
  const data = await fetchAPI<{ success: boolean; missions: MicroMission[] }>('/api/micro-missions');
  return data.missions;
}

export async function getMicroMissionDetail(id: string): Promise<MicroMissionDetail> {
  const data = await fetchAPI<{ success: boolean; mission: MicroMissionDetail }>(`/api/micro-mission/${id}`);
  return data.mission;
}

export async function startMicroMission(
  wallet: string,
  emissaryTokenId: string,
  microMissionId: string
): Promise<{
  active_micro_mission_id: number;
  mission: { id: string; name: string; narrative_intro: string; choices: any[] };
  started_at: string;
  ends_at: string;
}> {
  const data = await fetchAPI<any>('/api/micro-mission/start', {
    method: 'POST',
    body: JSON.stringify({
      wallet,
      emissary_token_id: emissaryTokenId,
      micro_mission_id: microMissionId,
    }),
  });
  return data;
}

export async function submitMicroMissionChoice(
  wallet: string,
  activeMicroMissionId: number,
  choice: string
): Promise<{ choice: string; outcome_preview: string }> {
  const data = await fetchAPI<any>('/api/micro-mission/choice', {
    method: 'POST',
    body: JSON.stringify({
      wallet,
      active_micro_mission_id: activeMicroMissionId,
      choice,
    }),
  });
  return data;
}

export async function completeMicroMission(
  wallet: string,
  activeMicroMissionId: number
): Promise<{
  rewards: MissionRewards;
  mission_name: string;
  outcome_text: string;
  choice_made: string;
}> {
  const data = await fetchAPI<any>('/api/micro-mission/complete', {
    method: 'POST',
    body: JSON.stringify({
      wallet,
      active_micro_mission_id: activeMicroMissionId,
    }),
  });
  return data;
}

export async function getActiveMicroMission(wallet: string): Promise<ActiveMicroMission | null> {
  const data = await fetchAPI<{ success: boolean; active: boolean; micro_mission?: ActiveMicroMission }>(
    `/api/micro-mission/active/${wallet}`
  );
  return data.active ? data.micro_mission! : null;
}

// =========================================
// Emissaries
// =========================================

export async function getEmissaryFullStatus(tokenId: string): Promise<Emissary> {
  const data = await fetchAPI<{ success: boolean; emissary: Emissary }>(`/api/emissary/${tokenId}/full-status`);
  return data.emissary;
}

// Note: This endpoint needs to exist in the backend
export async function getWalletEmissaries(wallet: string): Promise<Emissary[]> {
  // For now, we'll use the player endpoint and transform
  try {
    const data = await fetchAPI<any>(`/api/player/${wallet}`);
    const heroes = data.player?.heroes || [];

    // Transform heroes to Emissary format
    return heroes.map((hero: any) => ({
      token_id: hero.token_id,
      name: hero.name || `Emissary #${hero.token_id}`,
      guild: hero.guild || 'Unknown',
      race_class: hero.race_class || 'Unknown',
      owner: wallet,
      image_url: hero.image_url || '',
      stats: {
        level: hero.dynamic_state?.xp_level || 1,
        xp_total: hero.dynamic_state?.xp_total || 0,
        aura_level: hero.dynamic_state?.aura_level || 0,
        energy_current: hero.dynamic_state?.energy_current || 100,
        energy_max: hero.dynamic_state?.energy_max || 100,
        power: hero.dynamic_state?.power_current || 10,
        death_count: hero.dynamic_state?.death_count || 0,
      },
      current_state: hero.dynamic_state?.state || 'READY',
      active_mission: null,
      active_micro_mission: null,
      equipment: {},
      chronicle: {
        total_missions: hero.dynamic_state?.total_missions_completed || 0,
        total_deaths: hero.dynamic_state?.death_count || 0,
        items_found: hero.dynamic_state?.items_found || 0,
        runes_found: hero.dynamic_state?.runes_found || 0,
      },
    }));
  } catch (error) {
    console.error('Error fetching emissaries:', error);
    return [];
  }
}
