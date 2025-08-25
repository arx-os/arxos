"""Mobile Integration Module (Future)

Will handle mobile app integration features:
- Real-time AR session management
- Mobile device communication
- Push notifications
- Offline sync
"""

from .mobile_session_manager import MobileSessionManager, ARSession

__all__ = [
    'MobileSessionManager',
    'ARSession'
]
