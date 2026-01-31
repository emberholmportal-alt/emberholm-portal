-- =========================================================================
-- EMBERHOLM PORTAL - Database Verification Script
-- =========================================================================
-- Ejecuta este script para verificar el estado de tu base de datos
-- =========================================================================
-- Ejecutar: psql $DATABASE_URL -f migrations/verify_database.sql
-- =========================================================================

\echo '=========================================='
\echo 'EMBERHOLM DATABASE VERIFICATION'
\echo '=========================================='

-- =========================================================================
-- 1. VERIFICAR TABLAS EXISTENTES
-- =========================================================================

\echo ''
\echo '1. CHECKING TABLES...'
\echo '----------------------'

SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'nfts') THEN '✅ nfts'
        ELSE '❌ nfts (MISSING)'
    END as table_status
UNION ALL SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'active_missions') THEN '✅ active_missions'
        ELSE '❌ active_missions (MISSING)'
    END
UNION ALL SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'pyre_balances') THEN '✅ pyre_balances'
        ELSE '❌ pyre_balances (MISSING)'
    END
UNION ALL SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'micro_missions') THEN '✅ micro_missions'
        ELSE '❌ micro_missions (MISSING)'
    END
UNION ALL SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'active_micro_missions') THEN '✅ active_micro_missions'
        ELSE '❌ active_micro_missions (MISSING)'
    END
UNION ALL SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_profiles') THEN '✅ user_profiles'
        ELSE '❌ user_profiles (MISSING)'
    END
UNION ALL SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'private_messages') THEN '✅ private_messages'
        ELSE '❌ private_messages (MISSING)'
    END
UNION ALL SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'social_rewards_log') THEN '✅ social_rewards_log'
        ELSE '❌ social_rewards_log (MISSING)'
    END
UNION ALL SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_streaks') THEN '✅ user_streaks'
        ELSE '❌ user_streaks (MISSING)'
    END
UNION ALL SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'items') THEN '✅ items'
        ELSE '❌ items (MISSING)'
    END
UNION ALL SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_balances') THEN '✅ user_balances'
        ELSE '❌ user_balances (MISSING)'
    END
UNION ALL SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'events') THEN '✅ events'
        ELSE '❌ events (MISSING)'
    END;

-- =========================================================================
-- 2. VERIFICAR COLUMNAS EN nfts
-- =========================================================================

\echo ''
\echo '2. CHECKING nfts TABLE COLUMNS...'
\echo '----------------------------------'

SELECT
    column_name,
    data_type,
    CASE
        WHEN column_name IN ('token_id', 'name', 'guild', 'race_class', 'last_known_owner', 'dynamic_state', 'image_url', 'weapon_id', 'armor_id', 'helmet_id', 'accessory_id', 'amulet_id', 'rune_ids', 'land_id')
        THEN '✅'
        ELSE '➕'
    END as required
FROM information_schema.columns
WHERE table_name = 'nfts'
ORDER BY ordinal_position;

-- =========================================================================
-- 3. VERIFICAR DATOS EN MICRO_MISSIONS
-- =========================================================================

\echo ''
\echo '3. CHECKING MICRO_MISSIONS DATA...'
\echo '-----------------------------------'

SELECT
    CASE
        WHEN COUNT(*) > 0 THEN '✅ Found ' || COUNT(*) || ' micro-missions'
        ELSE '❌ No micro-missions found - run 002_seed_micro_missions.sql'
    END as status
FROM micro_missions WHERE is_active = TRUE;

SELECT id, name, difficulty, ember_reward_min || '-' || ember_reward_max as ember_reward
FROM micro_missions
WHERE is_active = TRUE
ORDER BY difficulty, id
LIMIT 10;

-- =========================================================================
-- 4. VERIFICAR user_profiles
-- =========================================================================

\echo ''
\echo '4. CHECKING USER_PROFILES...'
\echo '-----------------------------'

SELECT
    CASE
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_profiles')
        THEN '✅ user_profiles table exists with ' ||
             (SELECT COUNT(*) FROM user_profiles) || ' users'
        ELSE '❌ user_profiles table MISSING'
    END as status;

-- =========================================================================
-- 5. VERIFICAR CONTEOS GENERALES
-- =========================================================================

\echo ''
\echo '5. DATA COUNTS...'
\echo '-----------------'

SELECT 'nfts' as table_name, COUNT(*) as row_count FROM nfts
UNION ALL SELECT 'active_missions', COUNT(*) FROM active_missions
UNION ALL SELECT 'items', COUNT(*) FROM items
UNION ALL SELECT 'user_balances', COUNT(*) FROM user_balances
UNION ALL SELECT 'pyre_balances', COUNT(*) FROM pyre_balances
UNION ALL SELECT 'micro_missions', COUNT(*) FROM micro_missions
UNION ALL SELECT 'user_profiles', COUNT(*) FROM user_profiles
UNION ALL SELECT 'events', COUNT(*) FROM events
ORDER BY table_name;

\echo ''
\echo '=========================================='
\echo 'VERIFICATION COMPLETE'
\echo '=========================================='
\echo ''
\echo 'If you see ❌ for any required tables, run:'
\echo '  psql $DATABASE_URL -f migrations/001_mini_app_tables.sql'
\echo '  psql $DATABASE_URL -f migrations/002_seed_micro_missions.sql'
\echo ''
