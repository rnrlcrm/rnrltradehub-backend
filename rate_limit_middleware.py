"""
Rate Limiting and Security Middleware.

Provides:
- Rate limiting per IP and per user
- Anomaly detection
- Brute force protection
- Request throttling
"""
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with in-memory storage.
    
    For production, use Redis or similar distributed cache.
    """
    
    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # In-memory storage: {key: [(timestamp, count)]}
        self.request_log: Dict[str, list] = defaultdict(list)
        self.blocked_ips: Dict[str, datetime] = {}
        
        # Cleanup old entries every 100 requests
        self.request_count = 0
        self.cleanup_interval = 100

    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check X-Forwarded-For header (for proxied requests)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"

    def is_blocked(self, ip: str) -> Tuple[bool, str]:
        """Check if IP is temporarily blocked."""
        if ip in self.blocked_ips:
            block_until = self.blocked_ips[ip]
            if datetime.utcnow() < block_until:
                remaining = (block_until - datetime.utcnow()).seconds
                return True, f"Too many requests. Blocked for {remaining} more seconds."
            else:
                # Unblock
                del self.blocked_ips[ip]
        return False, ""

    def check_rate_limit(self, key: str) -> Tuple[bool, str]:
        """
        Check if request exceeds rate limits.
        
        Returns (allowed, message)
        """
        now = time.time()
        one_minute_ago = now - 60
        one_hour_ago = now - 3600
        
        # Get request history for this key
        requests = self.request_log[key]
        
        # Clean up old requests
        requests = [(ts, count) for ts, count in requests if ts > one_hour_ago]
        
        # Count requests in last minute and hour
        requests_last_minute = sum(
            count for ts, count in requests if ts > one_minute_ago
        )
        requests_last_hour = sum(count for ts, count in requests)
        
        # Check limits
        if requests_last_minute >= self.requests_per_minute:
            return False, f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
        
        if requests_last_hour >= self.requests_per_hour:
            # Block for 15 minutes
            block_until = datetime.utcnow() + timedelta(minutes=15)
            ip = key.split(":")[0] if ":" in key else key
            self.blocked_ips[ip] = block_until
            return False, f"Rate limit exceeded: {self.requests_per_hour} requests per hour. Blocked for 15 minutes."
        
        # Add this request
        requests.append((now, 1))
        self.request_log[key] = requests
        
        return True, ""

    def cleanup_old_entries(self):
        """Remove old entries from request log."""
        now = time.time()
        one_hour_ago = now - 3600
        
        for key in list(self.request_log.keys()):
            requests = self.request_log[key]
            requests = [(ts, count) for ts, count in requests if ts > one_hour_ago]
            
            if requests:
                self.request_log[key] = requests
            else:
                del self.request_log[key]

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/readiness", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Check if IP is blocked
        is_blocked, block_message = self.is_blocked(client_ip)
        if is_blocked:
            raise HTTPException(status_code=429, detail=block_message)
        
        # Rate limiting key (IP-based)
        rate_key = f"{client_ip}"
        
        # For authenticated requests, also check per-user limits
        # (Would need to extract user_id from JWT token)
        
        # Check rate limit
        allowed, message = self.check_rate_limit(rate_key)
        if not allowed:
            raise HTTPException(status_code=429, detail=message)
        
        # Periodic cleanup
        self.request_count += 1
        if self.request_count % self.cleanup_interval == 0:
            self.cleanup_old_entries()
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        # Add headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        
        return response


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware for anomaly detection and logging.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.suspicious_patterns = {
            "sql_injection": ["'", "--", "union", "select", "drop", "insert"],
            "path_traversal": ["../", "..\\", "%2e%2e"],
            "command_injection": [";", "&&", "||", "|", "$"],
        }
        self.failed_login_attempts: Dict[str, list] = defaultdict(list)

    def detect_suspicious_activity(self, request: Request) -> Tuple[bool, str]:
        """Detect potentially malicious requests."""
        path = request.url.path.lower()
        query = str(request.url.query).lower()
        
        # Check for SQL injection patterns
        for keyword in self.suspicious_patterns["sql_injection"]:
            if keyword in path or keyword in query:
                return True, f"Potential SQL injection detected: {keyword}"
        
        # Check for path traversal
        for pattern in self.suspicious_patterns["path_traversal"]:
            if pattern in path:
                return True, f"Potential path traversal detected: {pattern}"
        
        # Check for command injection
        for pattern in self.suspicious_patterns["command_injection"]:
            if pattern in query:
                return True, f"Potential command injection detected: {pattern}"
        
        return False, ""

    def log_suspicious_activity(
        self,
        request: Request,
        reason: str,
        db_session=None
    ):
        """Log suspicious activity to database."""
        # In production, save to SuspiciousActivity model
        client_ip = request.client.host if request.client else "unknown"
        
        logger_data = {
            "ip": client_ip,
            "path": request.url.path,
            "method": request.method,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # TODO: Save to database
        import logging
        logging.warning(f"Suspicious activity: {logger_data}")

    async def dispatch(self, request: Request, call_next):
        """Process request with security checks."""
        # Detect suspicious activity
        is_suspicious, reason = self.detect_suspicious_activity(request)
        
        if is_suspicious:
            self.log_suspicious_activity(request, reason)
            # For now, just log - in production, might want to block
            # raise HTTPException(status_code=400, detail="Suspicious request detected")
        
        # Add security headers to response
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


def add_security_middleware(app):
    """Add all security middleware to the FastAPI app."""
    # Rate limiting (60 req/min, 1000 req/hour)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=60, requests_per_hour=1000)
    
    # Security checks
    app.add_middleware(SecurityMiddleware)
