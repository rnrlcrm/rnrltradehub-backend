"""
Audit Logging Middleware
Logs all requests and important actions for security and compliance
"""
from fastapi import Request
from datetime import datetime
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)


class AuditLogger:
    """Audit logging for security and compliance."""
    
    @staticmethod
    async def log_request(
        request: Request,
        user_id: Optional[str] = None,
        action: str = "API_REQUEST",
        resource: Optional[str] = None,
        details: Optional[dict] = None
    ):
        """Log an audit event."""
        # Get client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else "unknown"
        
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": resource or request.url.path,
            "method": request.method,
            "ip_address": ip_address,
            "user_agent": request.headers.get("User-Agent"),
            "details": details or {}
        }
        
        # Log to standard logger (can be configured to send to database/external service)
        logger.info(f"AUDIT: {json.dumps(audit_entry)}")
        
        return audit_entry
    
    @staticmethod
    async def log_authentication(
        request: Request,
        user_id: str,
        email: str,
        success: bool,
        failure_reason: Optional[str] = None
    ):
        """Log authentication attempts."""
        action = "LOGIN_SUCCESS" if success else "LOGIN_FAILED"
        details = {
            "email": email,
            "success": success
        }
        if failure_reason:
            details["failure_reason"] = failure_reason
        
        await AuditLogger.log_request(
            request,
            user_id=user_id if success else None,
            action=action,
            resource="/auth/login",
            details=details
        )
    
    @staticmethod
    async def log_data_access(
        request: Request,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str = "READ"
    ):
        """Log data access for compliance."""
        await AuditLogger.log_request(
            request,
            user_id=user_id,
            action=f"DATA_ACCESS_{action}",
            resource=f"{resource_type}/{resource_id}",
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action
            }
        )
    
    @staticmethod
    async def log_security_event(
        request: Request,
        event_type: str,
        severity: str = "MEDIUM",
        details: Optional[dict] = None
    ):
        """Log security events."""
        await AuditLogger.log_request(
            request,
            action=f"SECURITY_EVENT_{event_type}",
            details={
                "event_type": event_type,
                "severity": severity,
                **(details or {})
            }
        )


# Middleware function to log all requests
async def audit_middleware(request: Request, call_next):
    """Middleware to audit all requests."""
    start_time = datetime.utcnow()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    # Log the request
    logger.info(
        f"Request: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.3f}s"
    )
    
    return response
