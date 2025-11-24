# 🔍 SMART CONTRACT AUDIT REPORT
## EmberholmPortal.sol - Complete Analysis

**Contract Version:** 3.0 (Professional - No Treasury)
**Network:** Base Mainnet
**Audit Date:** 2025-11-24
**Status:** ⚠️ REQUIRES MODIFICATIONS

---

## 📋 EXECUTIVE SUMMARY

**Overall Assessment:** The contract is **WELL DESIGNED** but has **CRITICAL INCOMPATIBILITIES** with the current backend/frontend implementation and the metadata structure we just designed.

### Severity Levels:
- 🔴 **CRITICAL** - Must fix before deployment
- 🟡 **IMPORTANT** - Should fix for optimal integration
- 🟢 **OPTIONAL** - Nice to have improvements

---

## 🔴 CRITICAL ISSUES

### 1. **EQUIPMENT SLOTS MISMATCH** 🔴

**Contract Definition:**
```solidity
string[4] public equipmentSlots = ["weapon", "armor", "boots", "accessory"];
```

**Metadata Definition (generator_v2_items_ranks.py):**
```json
"equipped_items": {
  "weapon": null,
  "armor": null,
  "accessory": null,
  "trinket": null
}
```

**Problem:** Contract uses `"boots"` but metadata uses `"trinket"`.

**Impact:** When items are implemented, the contract won't recognize `"trinket"` slot from metadata.

**Fix Required:**
```solidity
// CHANGE THIS:
string[4] public equipmentSlots = ["weapon", "armor", "boots", "accessory"];

// TO THIS:
string[4] public equipmentSlots = ["weapon", "armor", "accessory", "trinket"];
```

**Location:** Line ~52 of contract

---

### 2. **ITEM STATS SYSTEM INCOMPATIBILITY** 🔴

**Contract Item Stats:**
```solidity
struct ItemStats {
    uint16 attackBonus;   // ← Generic RPG stats
    uint16 defenseBonus;
    uint16 speedBonus;
    uint16 auraBonus;
    uint8 rarity;
}
```

**Game System Stats (app.py:1736-1738, missions_config.json):**
- D&D style: `str`, `dex`, `con`, `int`, `wis`, `cha`
- Success rate bonuses (guild, class, race, level, aura)
- Mission difficulty system (EASY/MEDIUM/HARD)

**Metadata Item Bonuses (generator_v2_items_ranks.py):**
```json
"item_bonuses": {
  "str": 0,
  "dex": 0,
  "con": 0,
  "int": 0,
  "wis": 0,
  "cha": 0,
  "power": 0,
  "success_rate": 0
}
```

**Problem:** The contract's item stats (`attackBonus`, `defenseBonus`, `speedBonus`) don't map to the game's D&D stat system.

**Impact:** When calculating mission success rates, the contract's item stats won't integrate with the existing bonus system.

**Solutions:**

#### Option A: Change Contract to Match Game System
```solidity
struct ItemStats {
    uint8 strBonus;
    uint8 dexBonus;
    uint8 conBonus;
    uint8 intBonus;
    uint8 wisBonus;
    uint8 chaBonus;
    uint8 powerBonus;
    uint8 successRateBonus;
    uint8 rarity;
}
```

#### Option B: Create Mapping Layer (Recommended)
Keep contract as-is but map in backend:
```python
# app.py - Mapping layer
def map_contract_stats_to_game_stats(contract_stats):
    """
    Map contract's generic RPG stats to game's D&D stats.
    """
    return {
        "str": contract_stats.attackBonus // 2,      # Attack → STR
        "dex": contract_stats.speedBonus // 2,       # Speed → DEX
        "con": contract_stats.defenseBonus // 2,     # Defense → CON
        "power": contract_stats.attackBonus,         # Attack → Power
        "success_rate": contract_stats.auraBonus // 2 # Aura → Success
    }
```

**Recommendation:** Use **Option B** (mapping layer) to avoid contract redeployment issues, but document this clearly.

---

## 🟡 IMPORTANT ISSUES

### 3. **STAKING NOT INTEGRATED WITH BACKEND** 🟡

**Contract Has:**
```solidity
mapping(uint256 => bool) public stakedTokens;
mapping(uint256 => uint256) public stakeTimestamp;

function stakeToken(uint256 tokenId) external { ... }
function unstakeToken(uint256 tokenId) external { ... }

// Prevents transfer of staked tokens
function _update(...) {
    require(!stakedTokens[tokenId], "Token is staked");
    ...
}
```

**Backend Has (app.py:1748-1768):**
```python
"state": "READY",  # READY / ON_MISSION / FALLEN
"current_mission_id": None,
"mission_start_time": None
```

**Problem:** Backend changes NFT state to `"ON_MISSION"` in its database, but **DOESN'T call contract's `stakeToken()`**.

**Impact:**
- NFTs on missions can still be transferred (defeats the purpose of on-chain staking)
- Contract's staking system is unused

**Current Behavior:**
1. User starts mission → Backend sets `state = "ON_MISSION"` in DB
2. NFT is still **unstaked on-chain**
3. User can transfer NFT to another wallet
4. Mission completes but NFT is in different wallet (bug!)

**Fix Required:**

#### Backend Integration Needed:

**app.py - Mission Start:**
```python
@app.route("/api/mission/start", methods=["POST"])
def start_mission():
    # ... existing validation ...

    # 🔥 STAKE TOKEN ON-CHAIN
    try:
        # Call contract's stakeToken() via Web3
        tx = contract.functions.stakeToken(token_id).transact({
            'from': mission_manager_wallet
        })
        w3.eth.wait_for_transaction_receipt(tx)
        logger.info(f"✅ Token {token_id} staked on-chain")
    except Exception as e:
        logger.error(f"❌ Failed to stake token: {e}")
        return jsonify({"error": "Failed to stake token"}), 500

    # Update backend state
    hero["dynamic_state"]["state"] = "ON_MISSION"
    # ... rest of function
```

**app.py - Mission Complete:**
```python
@app.route("/api/mission/complete", methods=["POST"])
def complete_mission():
    # ... reward calculation ...

    # 🔥 UNSTAKE TOKEN ON-CHAIN
    try:
        tx = contract.functions.unstakeToken(token_id).transact({
            'from': mission_manager_wallet
        })
        w3.eth.wait_for_transaction_receipt(tx)
        logger.info(f"✅ Token {token_id} unstaked on-chain")
    except Exception as e:
        logger.error(f"⚠️ Failed to unstake token: {e}")

    # Update backend state
    hero["dynamic_state"]["state"] = "READY"
    # ... rest of function
```

**Alternative:** If you want to avoid on-chain staking costs, consider removing staking from contract entirely and rely on backend validation only.

---

### 4. **MISSION MANAGER SECURITY RISK** 🟡

**Contract Code:**
```solidity
function unstakeToken(uint256 tokenId) external {
    address owner = ownerOf(tokenId);
    require(
        msg.sender == owner || msg.sender == missionManager, // ← Risk
        "Not authorized"
    );
    require(stakedTokens[tokenId], "Not staked");

    stakedTokens[tokenId] = false;
    emit TokenUnstaked(tokenId, owner, block.timestamp);
}
```

**Problem:** `missionManager` wallet can unstake **ANY** token, even if not the owner.

**Risk:** If `missionManager` wallet is compromised:
- Attacker can unstake all NFTs
- Attacker can transfer staked NFTs after unstaking
- No rate limiting or safeguards

**Impact:** **MEDIUM** - Requires compromising the missionManager wallet

**Recommendations:**

#### Option A: Add Cooldown Period
```solidity
mapping(uint256 => uint256) public lastUnstakeTime;
uint256 public constant UNSTAKE_COOLDOWN = 1 hours;

function unstakeToken(uint256 tokenId) external {
    address owner = ownerOf(tokenId);
    require(
        msg.sender == owner || msg.sender == missionManager,
        "Not authorized"
    );

    // If missionManager unstaking, enforce cooldown
    if (msg.sender == missionManager) {
        require(
            block.timestamp >= lastUnstakeTime[tokenId] + UNSTAKE_COOLDOWN,
            "Cooldown not elapsed"
        );
    }

    require(stakedTokens[tokenId], "Not staked");
    stakedTokens[tokenId] = false;
    lastUnstakeTime[tokenId] = block.timestamp;

    emit TokenUnstaked(tokenId, owner, block.timestamp);
}
```

#### Option B: Remove missionManager from unstake
Only allow **owner** to unstake:
```solidity
function unstakeToken(uint256 tokenId) external {
    require(ownerOf(tokenId) == msg.sender, "Not owner");
    require(stakedTokens[tokenId], "Not staked");

    stakedTokens[tokenId] = false;
    emit TokenUnstaked(tokenId, msg.sender, block.timestamp);
}
```

**Trade-off:** Option B means backend can't auto-unstake when mission completes. Users must manually unstake.

**Recommendation:** Use **Option A** with a short cooldown (1-4 hours) to prevent abuse while allowing legitimate backend operations.

---

### 5. **PRIMARY TOKEN NOT IMPLEMENTED IN FRONTEND** 🟡

**Contract Has:**
```solidity
mapping(address => uint256) public primaryToken;

function setPrimaryToken(uint256 tokenId) external { ... }
function getPrimaryTokenInfo(address owner) external view returns (TokenInfo memory) { ... }
```

**Frontend Has:** Nothing. The concept of "TOP EMISSARY" or primary token doesn't exist in UI.

**Impact:** Users can't select which NFT represents them. First NFT in array is always shown.

**Recommendation:** Either:
1. **Implement in frontend** - Add "Set as Primary" button in profile
2. **Remove from contract** - Reduces complexity if not needed

**If Implementing:**

**static/index.html:**
```javascript
async function setPrimaryEmissary(tokenId) {
    try {
        const tx = await contract.methods.setPrimaryToken(tokenId).send({
            from: currentWallet
        });

        showNotification("✅ Primary Emissary set!", "success");
        await loadProfile(currentWallet);
    } catch (error) {
        showNotification("❌ Failed to set primary emissary", "error");
    }
}

// Add button to profile card
<button onclick="setPrimaryEmissary('${hero.token_id}')">
    Set as Primary Emissary
</button>
```

---

### 6. **CUSTOM METADATA ON-CHAIN NOT USED** 🟡

**Contract Has:**
```solidity
mapping(uint256 => string) public tokenImageOverride;
mapping(uint256 => mapping(string => string)) public tokenAttributes;

function setTokenImage(uint256 tokenId, string calldata imageURI) external { ... }
function setTokenAttribute(uint256 tokenId, string calldata key, string calldata value) external { ... }
```

**Backend Has:** All metadata in `/data/metadata/` and `nfts_database.json`.

**Impact:** Paying gas for on-chain storage that's never read.

**Recommendation:**
- **Keep for future use** - Could allow users to customize avatars/badges on-chain
- **Document clearly** - Currently unused, backend metadata is source of truth

---

## 🟢 OPTIONAL IMPROVEMENTS

### 7. **GAS OPTIMIZATION: tokensOfOwner() IS EXPENSIVE** 🟢

**Current Implementation:**
```solidity
function tokensOfOwner(address owner) public view returns (uint256[] memory) {
    uint256 balance = balanceOf(owner);
    if (balance == 0) {
        return new uint256[](0);
    }

    uint256[] memory tokens = new uint256[](balance);
    uint256 index = 0;
    uint256 supply = totalMinted(); // Could be 35,000!

    // Iterates over ALL tokens ever minted
    for (uint256 tokenId = 1; tokenId <= supply && index < balance; tokenId++) {
        if (_ownerOf(tokenId) == owner) {
            tokens[index] = tokenId;
            index++;
        }
    }

    return tokens;
}
```

**Problem:** With 35,000 NFTs minted, this function iterates up to 35,000 times.

**Gas Cost:** Could exceed block gas limit for users with many NFTs.

**Impact:** LOW - This is a `view` function (no gas cost when called off-chain), but still slow.

**Recommendation:** Consider using an enumerable extension:
```solidity
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";

contract EmberholmPortal is ERC721Enumerable, Ownable, ERC2981 {
    // Automatically tracks tokenOfOwnerByIndex()
    // Small gas cost on mint/transfer, but O(1) lookups
}
```

**Trade-off:** Adds ~5-10% gas cost to mints/transfers, but makes `tokensOfOwner()` instant.

---

### 8. **MISSING EMERGENCY PAUSE MECHANISM** 🟢

**Current State:** No way to pause minting or transfers in emergency.

**Recommendation:** Add OpenZeppelin's Pausable:
```solidity
import "@openzeppelin/contracts/utils/Pausable.sol";

contract EmberholmPortal is ERC721, Ownable, ERC2981, Pausable {

    function mint(uint256 quantity) external payable whenNotPaused {
        // ... existing code ...
    }

    function _update(...) internal override whenNotPaused returns (address) {
        // ... existing code ...
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }
}
```

**Benefit:** Can pause contract if exploit is discovered.

---

## ✅ WHAT'S WORKING WELL

### 1. **SECURITY** ✅
- ✅ Uses OpenZeppelin contracts (industry standard)
- ✅ Proper access control (`onlyOwner`, owner checks)
- ✅ Reentrancy protection (follows CEI pattern)
- ✅ Refunds excess ETH in mint
- ✅ Prevents transfer of staked tokens
- ✅ ERC2981 royalties implemented

### 2. **GAS EFFICIENCY** ✅
- ✅ Uses `calldata` instead of `memory` where possible
- ✅ Batch operations to reduce RPC calls
- ✅ No unnecessary storage writes
- ✅ Efficient refund mechanism

### 3. **FUNCTIONALITY** ✅
- ✅ Mint with quantity (1-10 per tx)
- ✅ Owner mint for airdrops
- ✅ Staking system (needs backend integration)
- ✅ Equipment slots (prepared for items)
- ✅ Batch query functions
- ✅ Wallet profile in one call

### 4. **DESIGN PHILOSOPHY** ✅
- ✅ **Backend-first approach** - Guild, names, achievements off-chain (FREE)
- ✅ **Minimal on-chain state** - Only ownership and critical features
- ✅ **Extensible** - Items contract can be connected later
- ✅ **Standard compliance** - ERC721, ERC2981

---

## 🛠️ REQUIRED CHANGES SUMMARY

### Must Fix Before Deployment:

1. **Change equipment slots:**
   ```solidity
   // Line ~52
   string[4] public equipmentSlots = ["weapon", "armor", "accessory", "trinket"];
   ```

2. **Document stat mapping:**
   Create clear documentation on how contract stats map to game stats, OR change ItemStats struct to match game system.

3. **Integrate staking with backend:**
   Add Web3 calls to `stakeToken()` and `unstakeToken()` in mission start/complete endpoints.

### Should Fix:

4. **Add unstake cooldown for missionManager** (security)

5. **Implement primary token in frontend** OR remove from contract

### Optional:

6. **Add Pausable for emergency stops**

7. **Consider ERC721Enumerable** for gas-efficient token lookups

---

## 📊 COMPATIBILITY MATRIX

| Feature | Contract | Backend | Frontend | Metadata | Status |
|---------|----------|---------|----------|----------|--------|
| **Ownership** | ✅ | ✅ | ✅ | ✅ | ✅ COMPATIBLE |
| **Staking** | ✅ | ❌ | ❌ | N/A | 🔴 NOT INTEGRATED |
| **Equipment Slots** | ⚠️ boots | N/A | N/A | ⚠️ trinket | 🔴 MISMATCH |
| **Item Stats** | ⚠️ attack/defense | ⚠️ str/dex/con | N/A | ⚠️ str/dex/con | 🔴 INCOMPATIBLE |
| **Primary Token** | ✅ | ❌ | ❌ | N/A | 🟡 NOT USED |
| **Custom Metadata** | ✅ | ❌ | ❌ | N/A | 🟡 NOT USED |
| **Guilds** | ❌ (off-chain) | ✅ | ✅ | ✅ | ✅ COMPATIBLE |
| **Achievements** | ❌ (off-chain) | ✅ | ✅ | ✅ | ✅ COMPATIBLE |
| **Ranks** | ❌ (off-chain) | ⚠️ (to implement) | ⚠️ (to implement) | ✅ | ✅ COMPATIBLE |

---

## 🎯 DEPLOYMENT CHECKLIST

Before deploying to Base Mainnet:

- [ ] Fix equipment slots: `boots` → `trinket`
- [ ] Document or fix item stats mapping
- [ ] Integrate staking with backend (or remove from contract)
- [ ] Add missionManager unstake cooldown
- [ ] Set correct `baseTokenURI` (currently points to Render)
- [ ] Set `missionManager` address after deployment
- [ ] Test all functions on Base Sepolia testnet
- [ ] Verify contract on Basescan
- [ ] Transfer ownership to multisig (recommended)

---

## 📝 RECOMMENDED CONTRACT CHANGES

Here's a diff of critical changes needed:

```solidity
// ========== CHANGE 1: Fix Equipment Slots ==========
- string[4] public equipmentSlots = ["weapon", "armor", "boots", "accessory"];
+ string[4] public equipmentSlots = ["weapon", "armor", "accessory", "trinket"];

// ========== CHANGE 2: Add Unstake Cooldown ==========
+ mapping(uint256 => uint256) public lastUnstakeTime;
+ uint256 public constant UNSTAKE_COOLDOWN = 2 hours;

function unstakeToken(uint256 tokenId) external {
    address owner = ownerOf(tokenId);
    require(
        msg.sender == owner || msg.sender == missionManager,
        "Not authorized"
    );
+
+   // Enforce cooldown for missionManager
+   if (msg.sender == missionManager) {
+       require(
+           block.timestamp >= lastUnstakeTime[tokenId] + UNSTAKE_COOLDOWN,
+           "Cooldown not elapsed"
+       );
+   }

    require(stakedTokens[tokenId], "Not staked");
    stakedTokens[tokenId] = false;
+   lastUnstakeTime[tokenId] = block.timestamp;

    emit TokenUnstaked(tokenId, owner, block.timestamp);
}

// ========== CHANGE 3: Option - Match Game Stats ==========
// (Alternative to mapping layer in backend)
struct ItemStats {
-   uint16 attackBonus;
-   uint16 defenseBonus;
-   uint16 speedBonus;
-   uint16 auraBonus;
+   uint8 strBonus;
+   uint8 dexBonus;
+   uint8 conBonus;
+   uint8 intBonus;
+   uint8 wisBonus;
+   uint8 chaBonus;
+   uint8 powerBonus;
+   uint8 successRateBonus;
    uint8 rarity;
}
```

---

## 🎉 FINAL VERDICT

**Contract Quality:** ⭐⭐⭐⭐☆ (4/5)

**Pros:**
- ✅ Clean, professional code
- ✅ Good security practices
- ✅ Backend-first design philosophy
- ✅ Extensible for future features

**Cons:**
- 🔴 Equipment slots mismatch
- 🔴 Item stats incompatibility
- 🟡 Staking not integrated with backend
- 🟡 Some features unused (primary token, custom metadata)

**Recommendation:** **FIX CRITICAL ISSUES** before deployment. The contract is solid overall but needs alignment with the game system.

---

## 📞 NEXT STEPS

1. **Review this audit** with your team
2. **Decide on stat system:** Keep contract stats and map in backend, OR change contract
3. **Fix equipment slots** in contract
4. **Integrate staking** with backend (or remove from contract)
5. **Test on Base Sepolia** testnet
6. **Deploy to Base Mainnet** once verified

Would you like me to create the corrected contract with all fixes applied?
