"""
Rate Limiting Middleware
Prevents abuse by limiting requests per IP/user
"""
from fastapi import Request, HTTPException, status
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple
import time

# In-memory rate limit storage (use Redis in production)
rate_limit_storage: Dict[str, list] = defaultdict(list)


class RateLimiter:
    """Rate limiting middleware for FastAPI."""
    
    def __init__(
        self,
        requests_per_minute: int = 100,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
    
    def _get_client_key(self, request: Request) -> str:
        """Get unique client identifier."""
        # Try to get user from token first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return f"user:{auth_header.split(' ')[1][:20]}"  # Use token prefix
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
    
    def _cleanup_old_requests(self, request_times: list, window_seconds: int):
        """Remove requests older than window."""
        cutoff = time.time() - window_seconds
        return [t for t in request_times if t > cutoff]
    
    async def __call__(self, request: Request):
        """Check rate limits for the request."""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return
        
        client_key = self._get_client_key(request)
        current_time = time.time()
        
        # Get request history
        request_times = rate_limit_storage[client_key]
        
        # Cleanup old requests
        request_times = self._cleanup_old_requests(request_times, 86400)  # 24 hours
        
        # Check limits
        recent_minute = [t for t in request_times if t > current_time - 60]
        recent_hour = [t for t in request_times if t > current_time - 3600]
        recent_day = request_times
        
        if len(recent_minute) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
            )
        
        if len(recent_hour) >= self.requests_per_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.requests_per_hour} requests per hour"
            )
        
        if len(recent_day) >= self.requests_per_day:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.requests_per_day} requests per day"
            )
        
        # Add current request
        request_times.append(current_time)
        rate_limit_storage[client_key] = request_times


# Specific rate limiters for different endpoints
login_rate_limiter = RateLimiter(
    requests_per_minute=5,    # 5 login attempts per minute
    requests_per_hour=20,     # 20 per hour
    requests_per_day=100      # 100 per day
)

password_reset_limiter = RateLimiter(
    requests_per_minute=1,    # 1 per minute
    requests_per_hour=3,      # 3 per hour
    requests_per_day=10       # 10 per day
)

otp_rate_limiter = RateLimiter(
    requests_per_minute=1,    # 1 OTP per minute
    requests_per_hour=3,      # 3 per hour
    requests_per_day=10       # 10 per day
)

email_rate_limiter = RateLimiter(
    requests_per_minute=2,    # 2 emails per minute
    requests_per_hour=10,     # 10 per hour
    requests_per_day=50       # 50 per day
)

api_rate_limiter = RateLimiter(
    requests_per_minute=100,  # 100 API calls per minute
    requests_per_hour=1000,   # 1000 per hour
    requests_per_day=10000    # 10000 per day
)
