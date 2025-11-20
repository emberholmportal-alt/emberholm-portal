"""
EMBERHOLM PORTAL - MONITORING & ALERTING MODULE
Sistema de monitoreo, métricas y alertas automáticas
"""

import os
import json
import logging
import traceback
from datetime import datetime, timedelta
from functools import wraps
import time

logger = logging.getLogger(__name__)

# =========================================================================
# ERROR LOGGING TO DATABASE
# =========================================================================

def log_error_to_db(error_type, error_message, stack_trace=None, context=None, severity='ERROR'):
    """
    Log error to database for monitoring and alerts.

    Args:
        error_type: Type of error (e.g., 'DatabaseError', 'ValidationError')
        error_message: Error message
        stack_trace: Full stack trace
        context: Additional context (dict)
        severity: 'CRITICAL', 'ERROR', 'WARNING', 'INFO'
    """
    try:
        import database as db
        if not db.is_postgresql_available():
            return

        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO error_log (error_type, error_message, stack_trace, context, severity)
                VALUES (%s, %s, %s, %s, %s)
            """, (error_type, error_message, stack_trace, json.dumps(context or {}), severity))
        conn.commit()
        db.release_connection(conn)

    except Exception as e:
        logger.error(f"Failed to log error to database: {e}")

# =========================================================================
# PERFORMANCE METRICS
# =========================================================================

def log_performance_metric(endpoint, method, response_time_ms, status_code, user_wallet=None):
    """
    Log performance metric to database.

    Args:
        endpoint: API endpoint (e.g., '/api/stats')
        method: HTTP method (GET, POST, etc.)
        response_time_ms: Response time in milliseconds
        status_code: HTTP status code
        user_wallet: Optional wallet address
    """
    try:
        import database as db
        if not db.is_postgresql_available():
            return

        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO performance_metrics (endpoint, method, response_time_ms, status_code, user_wallet)
                VALUES (%s, %s, %s, %s, %s)
            """, (endpoint, method, response_time_ms, status_code, user_wallet))
        conn.commit()
        db.release_connection(conn)

    except Exception as e:
        logger.warning(f"Failed to log performance metric: {e}")

# =========================================================================
# DECORATORS FOR AUTOMATIC MONITORING
# =========================================================================

def monitor_endpoint(func):
    """
    Decorator to automatically monitor endpoint performance and errors.

    Usage:
        @app.route('/api/stats')
        @monitor_endpoint
        def api_stats():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        endpoint = func.__name__
        method = 'GET'  # Default, can be improved with request context

        try:
            # Execute function
            result = func(*args, **kwargs)

            # Log success metric
            response_time_ms = int((time.time() - start_time) * 1000)
            log_performance_metric(endpoint, method, response_time_ms, 200)

            return result

        except Exception as e:
            # Log error
            response_time_ms = int((time.time() - start_time) * 1000)
            log_performance_metric(endpoint, method, response_time_ms, 500)

            log_error_to_db(
                error_type=type(e).__name__,
                error_message=str(e),
                stack_trace=traceback.format_exc(),
                context={'endpoint': endpoint, 'args': str(args)[:200]},
                severity='ERROR'
            )

            # Re-raise exception
            raise

    return wrapper

# =========================================================================
# ALERTING SYSTEM
# =========================================================================

class AlertThresholds:
    """Alert thresholds configuration"""
    ERROR_COUNT_THRESHOLD = 10  # Alert if >10 errors in last hour
    SLOW_RESPONSE_THRESHOLD = 2000  # Alert if response time > 2000ms
    FAILED_MISSIONS_THRESHOLD = 50  # Alert if >50 failed missions in last hour

def check_error_rate_alert():
    """Check if error rate exceeds threshold"""
    try:
        import database as db
        if not db.is_postgresql_available():
            return None

        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as error_count
                FROM error_log
                WHERE created_at > NOW() - INTERVAL '1 hour'
                AND severity IN ('ERROR', 'CRITICAL')
            """)
            row = cur.fetchone()
            error_count = row[0] if row else 0

        db.release_connection(conn)

        if error_count > AlertThresholds.ERROR_COUNT_THRESHOLD:
            return {
                'alert_type': 'HIGH_ERROR_RATE',
                'message': f'{error_count} errors in last hour',
                'severity': 'CRITICAL',
                'threshold': AlertThresholds.ERROR_COUNT_THRESHOLD
            }

        return None

    except Exception as e:
        logger.error(f"Error checking alert: {e}")
        return None

def check_slow_performance_alert():
    """Check for slow endpoints"""
    try:
        import database as db
        if not db.is_postgresql_available():
            return None

        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT endpoint, AVG(response_time_ms) as avg_time
                FROM performance_metrics
                WHERE created_at > NOW() - INTERVAL '5 minutes'
                GROUP BY endpoint
                HAVING AVG(response_time_ms) > %s
            """, (AlertThresholds.SLOW_RESPONSE_THRESHOLD,))
            slow_endpoints = cur.fetchall()

        db.release_connection(conn)

        if slow_endpoints:
            return {
                'alert_type': 'SLOW_PERFORMANCE',
                'message': f'{len(slow_endpoints)} slow endpoints detected',
                'severity': 'WARNING',
                'endpoints': [(row[0], row[1]) for row in slow_endpoints]
            }

        return None

    except Exception as e:
        logger.error(f"Error checking performance alert: {e}")
        return None

def get_active_alerts():
    """Get all active alerts"""
    alerts = []

    # Check error rate
    error_alert = check_error_rate_alert()
    if error_alert:
        alerts.append(error_alert)

    # Check performance
    perf_alert = check_slow_performance_alert()
    if perf_alert:
        alerts.append(perf_alert)

    return alerts

# =========================================================================
# DASHBOARD METRICS
# =========================================================================

def get_dashboard_metrics():
    """
    Get comprehensive metrics for monitoring dashboard.

    Returns:
        dict: Dashboard metrics
    """
    try:
        import database as db
        if not db.is_postgresql_available():
            return {'error': 'Database not available'}

        conn = db.get_connection()
        metrics = {}

        # Error stats
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '1 hour') as last_hour,
                    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') as last_24h,
                    COUNT(*) FILTER (WHERE severity = 'CRITICAL') as critical_count
                FROM error_log
            """)
            row = cur.fetchone()
            metrics['errors'] = {
                'last_hour': row[0] if row else 0,
                'last_24h': row[1] if row else 0,
                'critical': row[2] if row else 0
            }

        # Performance stats
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    AVG(response_time_ms) as avg_response,
                    MAX(response_time_ms) as max_response,
                    MIN(response_time_ms) as min_response,
                    COUNT(*) as total_requests
                FROM performance_metrics
                WHERE created_at > NOW() - INTERVAL '1 hour'
            """)
            row = cur.fetchone()
            metrics['performance'] = {
                'avg_response_ms': round(row[0]) if row and row[0] else 0,
                'max_response_ms': row[1] if row else 0,
                'min_response_ms': row[2] if row else 0,
                'total_requests': row[3] if row else 0
            }

        # Active missions
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM active_missions")
            row = cur.fetchone()
            metrics['active_missions'] = row[0] if row else 0

        # Recent audit logs
        with conn.cursor() as cur:
            cur.execute("""
                SELECT operation_type, COUNT(*) as count
                FROM audit_log
                WHERE created_at > NOW() - INTERVAL '1 hour'
                GROUP BY operation_type
                ORDER BY count DESC
                LIMIT 10
            """)
            metrics['recent_operations'] = dict(cur.fetchall())

        # Alerts
        metrics['alerts'] = get_active_alerts()

        db.release_connection(conn)
        return metrics

    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        return {'error': str(e)}

def get_recent_errors(limit=50):
    """Get recent errors for dashboard"""
    try:
        import database as db
        if not db.is_postgresql_available():
            return []

        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, error_type, error_message, severity, created_at
                FROM error_log
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            errors = []
            for row in cur.fetchall():
                errors.append({
                    'id': row[0],
                    'type': row[1],
                    'message': row[2],
                    'severity': row[3],
                    'timestamp': row[4].isoformat() if row[4] else None
                })

        db.release_connection(conn)
        return errors

    except Exception as e:
        logger.error(f"Error getting recent errors: {e}")
        return []

def get_endpoint_performance(hours=24):
    """Get endpoint performance stats"""
    try:
        import database as db
        if not db.is_postgresql_available():
            return []

        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    endpoint,
                    COUNT(*) as request_count,
                    AVG(response_time_ms) as avg_response,
                    MAX(response_time_ms) as max_response,
                    MIN(response_time_ms) as min_response
                FROM performance_metrics
                WHERE created_at > NOW() - INTERVAL '%s hours'
                GROUP BY endpoint
                ORDER BY request_count DESC
                LIMIT 20
            """ % hours)

            endpoints = []
            for row in cur.fetchall():
                endpoints.append({
                    'endpoint': row[0],
                    'requests': row[1],
                    'avg_ms': round(row[2]) if row[2] else 0,
                    'max_ms': row[3],
                    'min_ms': row[4]
                })

        db.release_connection(conn)
        return endpoints

    except Exception as e:
        logger.error(f"Error getting endpoint performance: {e}")
        return []
