"""
Health Check Service

This module provides health check functionality for the infrastructure layer.
"""

import logging
from typing import Any, Dict, List, Callable, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Health check service for monitoring system components."""

    def __init__(self):
        """Initialize health check service."""
        self.checks: Dict[str, Callable] = {}
        self.last_check_time: Optional[datetime] = None
        self.check_results: Dict[str, Dict[str, Any]] = {}

    def register_check(
        self, name: str, check_function: Callable[[], Dict[str, Any]]
    ) -> None:
        """Register a health check function."""
        self.checks[name] = check_function
        logger.info(f"Registered health check: {name}")

    def unregister_check(self, name: str) -> bool:
        """Unregister a health check function."""
        if name in self.checks:
            del self.checks[name]
            logger.info(f"Unregistered health check: {name}")
            return True
        return False

    def run_check(self, name: str) -> Dict[str, Any]:
        """Run a specific health check."""
        if name not in self.checks:
            return {"status": "error", "message": f"Health check '{name}' not found"}

        try:
            result = self.checks[name]()
            self.check_results[name] = result
            return result
        except Exception as e:
            logger.error(f"Error running health check '{name}': {e}")
            result = {"status": "error", "message": str(e)}
            self.check_results[name] = result
            return result

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks."""
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "checks": {},
        }

        for name in self.checks:
            check_result = self.run_check(name)
            results["checks"][name] = check_result

            if check_result.get("status") != "healthy":
                results["overall_status"] = "unhealthy"

        self.last_check_time = datetime.utcnow()
        return results

    def get_last_results(self) -> Dict[str, Any]:
        """Get the last health check results."""
        if not self.last_check_time:
            return {
                "status": "no_checks_run",
                "message": "No health checks have been run yet",
            }

        return {
            "last_check_time": self.last_check_time.isoformat(),
            "results": self.check_results,
        }

    def get_check_status(self, name: str) -> Dict[str, Any]:
        """Get the status of a specific health check."""
        if name not in self.check_results:
            return {
                "status": "unknown",
                "message": f"Health check '{name}' has not been run",
            }

        return self.check_results[name]

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the health check service itself."""
        return {
            "status": "healthy",
            "registered_checks": len(self.checks),
            "last_check_time": (
                self.last_check_time.isoformat() if self.last_check_time else None
            ),
        }
