"""
Enhanced BIM Builder Service for SVGX Engine

Builds hierarchical BIM structures from extracted SVGX elements with spatial organization 
and system classification, optimized for SVGX-specific operations and metadata.
"""

import structlog
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

from structlog import get_logger

from ..models.svgx import SVGXDocument, SVGXElement, ArxObject, ArxBehavior, ArxPhysics
try:
    from ..utils.errors import BIMError, ValidationError
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.errors import BIMError, ValidationError 