from fastapi import Request
from fastapi.responses import JSONResponse
import logging
import time

logger = logging.getLogger("middleware.audit")

async def audit_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Very simple mock audit log
    logger.info(
        f"AuditLog - Method: {request.method} Path: {request.url.path} "
        f"Status: {response.status_code} Time: {process_time:.3f}s"
    )
    
    return response

# Note: In main.py we simply use standard logging for now, but a true audit middleware
# would write to the `audit_logs` database table.
