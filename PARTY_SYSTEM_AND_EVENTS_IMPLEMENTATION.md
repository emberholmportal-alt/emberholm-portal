# 🎮 PARTY SYSTEM & EVENTS - Implementation Guide

## 📋 Overview

This document outlines the implementation of two major features:
1. **Party System**: Missions that require exactly 5 heroes working together
2. **Events System**: Temporary special missions with higher rewards

---

## ✅ COMPLETED (Phase 1)

### 1. Configuration Files Updated

#### `data/missions_config.json`
- ✅ Added `party_size: 5` to missions 003, 006, 009
- ✅ Added `party_bonus_multiplier: 1.2` (20% bonus)
- ✅ Updated descriptions to indicate [PARTY MISSION - 5 HEROES REQUIRED]

#### `data/events_config.json`
- ✅ Created new file with events structure
- ✅ Added EVENT_001: "Festival of the Eternal Flame"
  - Difficulty: EASY
  - Rewards: 150 XP, 15 Aura (2.5x normal easy mission)
  - Duration: 6 hours
  - Dates: Jan 20-27, 2025

### 2. Backend - Events System

#### `app.py`
- ✅ Added `load_events_config()` function (line 80-87)
- ✅ Initialized EVENTS, EVENT_SETTINGS variables (line 95-98, 1007-1010)
- ✅ Added `/api/events` endpoint (line 1083-1119)
  - Filters events by date (available_from/available_until)
  - Returns only active events
  - Calculates time_remaining_hours for each event

---

## 🔄 IN PROGRESS (Phase 2)

### 3. Backend - Party System

#### Modifications needed in `app.py`:

##### A. Modify `/api/mission/start` (line 1537+)

**Current behavior:** Accepts single `hero_id`
**New behavior:** Accept either `hero_id` OR `hero_ids` array

```python
@app.route("/api/mission/start", methods=["POST"])
def api_mission_start():
    data = request.get_json(force=True)
    wallet = data.get("wallet")
    hero_id = data.get("hero_id")  # Single hero (existing)
    hero_ids = data.get("hero_ids")  # Party of 5 (new)
    mission_id = data.get("mission_id")

    # Detect party mission
    is_party = hero_ids is not None and len(hero_ids) > 0

    if is_party:
        # PARTY MISSION LOGIC (NEW)
        return handle_party_mission_start(wallet, hero_ids, mission_id, data)
    else:
        # SOLO MISSION LOGIC (EXISTING - DON'T MODIFY)
        # ... current code continues as-is ...
```

##### B. Create `handle_party_mission_start()` function

```python
def handle_party_mission_start(wallet, hero_ids, mission_id, data):
    """
    Handle party mission start (5 heroes required)
    """
    # Validate party size
    if len(hero_ids) != 5:
        abort(400, f"Party missions require exactly 5 heroes. Received: {len(hero_ids)}")

    # Find mission
    mission = None
    for m in MISSIONS:
        if m["id"] == mission_id:
            mission = m
            break

    if mission is None:
        # Check if it's an event
        for e in EVENTS:
            if e["id"] == mission_id:
                mission = e
                break

    if mission is None:
        abort(400, "Mission not found")

    # Verify it's a party mission
    if mission.get("party_size") != 5:
        abort(400, "This mission is not a party mission")

    # Load player data
    wallet = wallet.lower()
    stats_obj = load_json(STATS_PATH, {...})
    player_obj, players_all = ensure_player(wallet)
    player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)

    # Validate all 5 heroes
    heroes = []
    for hero_id in hero_ids:
        hero = None
        for h in player_obj.get("heroes", []):
            if h.get("token_id") == hero_id:
                hero = h
                break

        if hero is None:
            abort(404, f"Hero {hero_id} not found")

        ds = hero["dynamic_state"]

        # Validations
        if ds.get("state") == "FALLEN":
            abort(400, f"Hero {hero_id} is fallen. Perform reinvocation ritual first.")

        if ds.get("state") == "ON_MISSION":
            abort(400, f"Hero {hero_id} is already on a mission")

        # Check energy
        cost_energy = mission["energy_cost"]
        energy_current = ds.get("energy_current", 0)
        if energy_current < cost_energy:
            abort(400, f"Hero {hero_id} doesn't have enough energy. Required: {cost_energy}, Available: {energy_current}")

        # Check mission cooldown (72h)
        mission_hist = ds.get("mission_history", {})
        last_run_ts = mission_hist.get(mission_id)
        if last_run_ts and hours_since(last_run_ts) < ROTATION_HOURS:
            hours_left = ROTATION_HOURS - hours_since(last_run_ts)
            abort(400, f"Hero {hero_id} has mission cooldown. {hours_left:.1f} hours remaining. This emissary already completed this mission. Try a different mission or wait.")

        heroes.append(hero)

    # All validations passed - start mission for all 5 heroes
    now_utc = now_utc_str()

    for hero in heroes:
        ds = hero["dynamic_state"]

        # Deduct energy
        ds["energy_current"] = max(0, ds["energy_current"] - mission["energy_cost"])

        # Set hero state to ON_MISSION
        ds["state"] = "ON_MISSION"
        ds["mission_start_time"] = now_utc
        ds["current_mission_id"] = mission_id
        ds["last_update"] = now_utc

        # Update NFT dynamic state in database
        update_nft_dynamic_state(hero["token_id"], ds)

    # Track active mission (party format)
    active_missions = load_json(ACTIVE_MISSIONS_PATH, {})
    mission_key = f"{wallet}_{mission_id}_party"
    active_missions[mission_key] = {
        "wallet": wallet,
        "hero_ids": hero_ids,
        "mission_id": mission_id,
        "start_time": now_utc,
        "duration_hours": mission["duration_hours"],
        "is_party": True
    }

    save_json(ACTIVE_MISSIONS_PATH, active_missions)

    # Save player data
    players_all[wallet] = player_obj
    save_json(PLAYERS_PATH, players_all)
    save_json(STATS_PATH, stats_obj)

    # Calculate success rate (average of all 5 heroes)
    total_success_rate = 0
    for hero in heroes:
        success_rate, bonus = calculate_mission_success_rate(hero, mission)
        total_success_rate += success_rate

    avg_success_rate = total_success_rate / 5

    return jsonify({
        "success": True,
        "party": True,
        "hero_ids": hero_ids,
        "mission_id": mission_id,
        "mission_name": mission["name"],
        "energy_spent": mission["energy_cost"] * 5,
        "duration_hours": mission["duration_hours"],
        "estimated_success_rate": round(avg_success_rate, 2),
        "message": f"Party of 5 heroes embarked on {mission['name']}!"
    })
```

##### C. Modify `/api/mission/complete` (line 1636+)

**Current behavior:** Completes single hero mission
**New behavior:** Detect and complete party missions

```python
@app.route("/api/mission/complete", methods=["POST"])
def api_mission_complete():
    data = request.get_json(force=True)
    wallet = data.get("wallet")
    hero_id = data.get("hero_id")
    mission_key_override = data.get("mission_key")  # For party missions

    wallet = wallet.lower()

    # Check if this is a party mission
    active_missions = load_json(ACTIVE_MISSIONS_PATH, {})

    # Look for party mission
    party_mission = None
    for key, mission_data in active_missions.items():
        if mission_data.get("is_party") and mission_data.get("wallet") == wallet:
            if hero_id in mission_data.get("hero_ids", []):
                party_mission = mission_data
                party_mission["mission_key"] = key
                break

    if party_mission:
        # PARTY MISSION COMPLETION (NEW)
        return handle_party_mission_complete(wallet, party_mission, data)
    else:
        # SOLO MISSION COMPLETION (EXISTING - DON'T MODIFY)
        # ... current code continues as-is ...
```

##### D. Create `handle_party_mission_complete()` function

```python
def handle_party_mission_complete(wallet, party_mission, data):
    """
    Complete party mission (process all 5 heroes individually)
    """
    hero_ids = party_mission["hero_ids"]
    mission_id = party_mission["mission_id"]
    mission_key = party_mission["mission_key"]

    # Find mission
    mission = None
    for m in MISSIONS:
        if m["id"] == mission_id:
            mission = m
            break

    if mission is None:
        # Check events
        for e in EVENTS:
            if e["id"] == mission_id:
                mission = e
                break

    if mission is None:
        abort(400, "Mission not found")

    # Load player data
    stats_obj = load_json(STATS_PATH, {...})
    player_obj, players_all = ensure_player(wallet)
    player_obj, stats_obj = apply_passive_and_regen(player_obj, stats_obj)

    # Check if mission is ready to complete
    start_time_str = party_mission.get("start_time")
    if not start_time_str:
        abort(400, "Mission start time not found")

    hours_elapsed = hours_since(start_time_str)
    duration_required = mission["duration_hours"]

    if hours_elapsed < duration_required:
        hours_remaining = duration_required - hours_elapsed
        abort(400, f"Mission not ready. {hours_remaining:.1f} hours remaining")

    # Process each hero individually
    results = []
    total_xp = 0
    total_aura = 0
    party_bonus_multiplier = mission.get("party_bonus_multiplier", 1.2)

    for hero_id in hero_ids:
        # Find hero
        hero = None
        for h in player_obj.get("heroes", []):
            if h.get("token_id") == hero_id:
                hero = h
                break

        if hero is None:
            continue

        ds = hero["dynamic_state"]

        # Check if hero is on this mission
        if ds.get("state") != "ON_MISSION" or ds.get("current_mission_id") != mission_id:
            continue

        # Roll outcome for THIS SPECIFIC HERO
        outcome, xp_gain, aura_gain, xp_loss = roll_mission_outcome(hero, mission)

        # Apply party bonus if success
        if outcome == "SUCCESS":
            xp_gain = int(xp_gain * party_bonus_multiplier)
            aura_gain = int(aura_gain * party_bonus_multiplier)

            ds["xp_total"] = ds.get("xp_total", 0) + xp_gain
            ds["aura_level"] = ds.get("aura_level", 0) + aura_gain
            ds["state"] = "READY"
            ds["total_missions_completed"] = ds.get("total_missions_completed", 0) + 1

            # Update mission history
            if "mission_history" not in ds:
                ds["mission_history"] = {}
            ds["mission_history"][mission_id] = now_utc_str()

            # Update stats
            stats_obj["missions_completed"] = stats_obj.get("missions_completed", 0) + 1
            stats_obj["total_exp_collected"] = stats_obj.get("total_exp_collected", 0) + xp_gain
            stats_obj["total_aura_collected"] = stats_obj.get("total_aura_collected", 0) + aura_gain

            total_xp += xp_gain
            total_aura += aura_gain

        elif outcome == "FAILURE":
            ds["xp_total"] = max(0, ds.get("xp_total", 0) - xp_loss)
            ds["state"] = "READY"
            ds["total_missions_failed"] = ds.get("total_missions_failed", 0) + 1
            stats_obj["missions_failed"] = stats_obj.get("missions_failed", 0) + 1

        elif outcome == "DEATH":
            ds["xp_total"] = max(0, ds.get("xp_total", 0) - xp_loss)
            ds["state"] = "FALLEN"
            ds["death_count"] = ds.get("death_count", 0) + 1
            ds["total_missions_failed"] = ds.get("total_missions_failed", 0) + 1
            stats_obj["missions_failed"] = stats_obj.get("missions_failed", 0) + 1

        # Clear mission state
        ds["mission_start_time"] = None
        ds["current_mission_id"] = None
        ds["last_update"] = now_utc_str()

        # Update NFT dynamic state in database
        update_nft_dynamic_state(hero_id, ds)

        results.append({
            "hero_id": hero_id,
            "hero_name": hero.get("name"),
            "outcome": outcome,
            "xp_gain": xp_gain if outcome == "SUCCESS" else 0,
            "aura_gain": aura_gain if outcome == "SUCCESS" else 0,
            "xp_loss": xp_loss if outcome != "SUCCESS" else 0
        })

    # Remove from active missions
    active_missions = load_json(ACTIVE_MISSIONS_PATH, {})
    if mission_key in active_missions:
        del active_missions[mission_key]
        save_json(ACTIVE_MISSIONS_PATH, active_missions)

    # Save player data
    players_all[wallet] = player_obj
    save_json(PLAYERS_PATH, players_all)
    save_json(STATS_PATH, stats_obj)

    # Calculate summary
    successes = len([r for r in results if r["outcome"] == "SUCCESS"])
    failures = len([r for r in results if r["outcome"] == "FAILURE"])
    deaths = len([r for r in results if r["outcome"] == "DEATH"])

    return jsonify({
        "success": True,
        "party": True,
        "mission_name": mission["name"],
        "results": results,
        "summary": {
            "successes": successes,
            "failures": failures,
            "deaths": deaths,
            "total_xp": total_xp,
            "total_aura": total_aura,
            "party_bonus": f"+{int((party_bonus_multiplier - 1) * 100)}%"
        }
    })
```

---

## 📱 FRONTEND (Phase 3)

### 4. Events Section

#### Create `templates/events.html` or add to `index.html`

```html
<!-- EVENTS SECTION -->
<div id="events-section" class="section">
    <h2>> ACTIVE EVENTS</h2>
    <div id="events-list">
        <!-- Populated by JavaScript -->
    </div>
</div>
```

#### JavaScript for Events

```javascript
// Fetch and display events
async function loadEvents() {
    const response = await fetch('/api/events');
    const data = await response.json();
    const events = data.events;

    const eventsContainer = document.getElementById('events-list');

    if (events.length === 0) {
        eventsContainer.innerHTML = '<p>No active events at this time.</p>';
        return;
    }

    eventsContainer.innerHTML = events.map(event => `
        <div class="event-card" data-event-id="${event.id}">
            <h3>[EVENT] ${event.name}</h3>
            <p>${event.description}</p>
            <div class="event-details">
                <span>Difficulty: ${event.difficulty}</span>
                <span>Duration: ${event.duration_hours}h</span>
                <span>Rewards: ${event.reward_xp} XP, ${event.reward_aura} Aura</span>
                <span class="time-remaining">Time Remaining: ${event.time_remaining_hours}h</span>
            </div>
            <button onclick="startMission('${event.id}', false)">START EVENT</button>
        </div>
    `).join('');
}

// Call on page load
loadEvents();
```

### 5. Party Selection UI

#### Add Party Selection to Missions

```javascript
function showPartySelector(missionId) {
    const modal = document.getElementById('party-selector-modal');
    modal.style.display = 'block';

    // Load user's heroes
    const heroes = getUserHeroes(); // From wallet data

    const heroList = document.getElementById('party-hero-list');
    heroList.innerHTML = heroes.map(hero => {
        const canSelect = hero.state === 'READY' && hero.energy_current >= mission.energy_cost;

        return `
            <div class="hero-selector ${canSelect ? '' : 'disabled'}">
                <input type="checkbox"
                       id="hero-${hero.token_id}"
                       value="${hero.token_id}"
                       ${canSelect ? '' : 'disabled'}
                       onchange="updatePartySelection()">
                <label for="hero-${hero.token_id}">
                    #${hero.token_id} - ${hero.name}
                    <span class="hero-status">${hero.state}</span>
                    <span class="hero-energy">Energy: ${hero.energy_current}/${hero.energy_max}</span>
                </label>
            </div>
        `;
    }).join('');
}

function updatePartySelection() {
    const checkboxes = document.querySelectorAll('.hero-selector input:checked');
    const selectedCount = checkboxes.length;
    const submitButton = document.getElementById('party-submit');

    submitButton.disabled = selectedCount !== 5;
    submitButton.textContent = `SELECT 5 HEROES (${selectedCount}/5)`;
}

async function submitPartyMission(missionId) {
    const checkboxes = document.querySelectorAll('.hero-selector input:checked');
    const heroIds = Array.from(checkboxes).map(cb => cb.value);

    if (heroIds.length !== 5) {
        alert('You must select exactly 5 heroes');
        return;
    }

    const response = await fetch('/api/mission/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            wallet: userWallet,
            hero_ids: heroIds,
            mission_id: missionId
        })
    });

    const result = await response.json();

    if (result.success) {
        alert(`Party mission started! ${result.message}`);
        location.reload();
    } else {
        alert(`Error: ${result.message}`);
    }
}
```

---

## 🧪 TESTING CHECKLIST

### Events System
- [ ] `/api/events` returns only active events
- [ ] Events show correct time_remaining_hours
- [ ] Events appear in EVENTS section (not MISSIONS)
- [ ] Can start event mission like normal mission
- [ ] Event rewards are higher than normal missions

### Party System
- [ ] Missions 003, 006, 009 show [PARTY MISSION]
- [ ] Party selector appears when clicking party mission
- [ ] Can select exactly 5 heroes (not more, not less)
- [ ] Validates all 5 heroes are READY
- [ ] Validates all 5 heroes have enough energy
- [ ] All 5 heroes marked as ON_MISSION
- [ ] Party completion processes each hero individually
- [ ] Each hero can succeed, fail, or die independently
- [ ] Party bonus (+20%) applied to successful heroes
- [ ] All 5 heroes return to READY (or FALLEN) after mission

### Cooldown Messages
- [ ] Clear message when hero already completed mission
- [ ] Shows hours/minutes remaining
- [ ] Suggests trying different mission

---

## 📝 NOTES

### Party Mechanics Summary
- Exactly 5 heroes required
- Each hero pays own energy cost
- Each hero rolls independently for success/failure/death
- Successful heroes get +20% bonus XP and Aura
- Failed/dead heroes get normal penalties
- All 5 heroes have 72h cooldown after completion

### Events Mechanics Summary
- Appear in separate EVENTS section
- Time-limited availability
- Easy difficulty, high rewards (~2.5x normal)
- Can be solo or party (configure party_size in events_config.json)
- 72h cooldown like normal missions

---

## 🚀 DEPLOYMENT STEPS

1. ✅ Update missions_config.json (DONE)
2. ✅ Create events_config.json (DONE)
3. ✅ Add events loading to app.py (DONE)
4. ✅ Add `/api/events` endpoint (DONE)
5. ⏳ Add `handle_party_mission_start()` function
6. ⏳ Modify `/api/mission/start` to support party
7. ⏳ Add `handle_party_mission_complete()` function
8. ⏳ Modify `/api/mission/complete` to support party
9. ⏳ Update cooldown error messages
10. ⏳ Add EVENTS section to frontend
11. ⏳ Add party selector UI to frontend
12. ⏳ Test all functionality
13. ⏳ Deploy to production

---

## 📋 CURRENT STATUS

**Phase 1 (COMPLETED):**
- ✅ Configuration files updated
- ✅ Events system backend (API endpoint)

**Phase 2 (IN PROGRESS):**
- ⏳ Party system backend
  - Need to add `handle_party_mission_start()`
  - Need to add `handle_party_mission_complete()`
  - Need to modify existing endpoints to detect party missions

**Phase 3 (PENDING):**
- ⏳ Frontend for events section
- ⏳ Frontend for party selector

**Estimated completion time:** 2-3 hours of development + 1 hour testing
