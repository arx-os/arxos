import re
from typing import Optional, Tuple

class ObjectIDService:
    """
    Unified Object ID service for generation and validation of both system-specific and legacy object IDs.
    """
    # System-specific regex patterns
    SYSTEM_PATTERNS = {
        "electrical":  r"^(epnl\d+)\.(spnl\d+)\.(jb\d+)\.(lf\d+)$",
        "hvac":        r"^(ahu\d+)\.(zc\d+)\.(tu\d+)\.(dv\d+)$",
        "plumbing":    r"^(ms\d+)\.(fr\d+)\.(bl\d+)\.(fx\d+)$",
        "fire_alarm":  r"^(fac\d+)\.(nac\d+)\.(jb\d+)\.(fa\d+)$",
        "telecom":     r"^(idf\d+)\.(fdc\d+)\.(dp\d+)\.(po\d+)$",
        "network":     r"^(mcr\d+)\.(idc\d+)\.(dp\d+)\.(eo\d+)$",
        "av":          r"^(avc\d+)\.(amp\d+)\.(cb\d+)\.(av\d+)$",
        "security":    r"^(sec\d+)\.(cc\d+)\.(cb\d+)\.(sc\d+)$",
        "bas":         r"^(bcu\d+)\.(fc\d+)\.(lo\d+)\.(bs\d+)$",
        "lighting":    r"^(lcp\d+)\.(lcg\d+)\.(lcj\d+)\.(ld\d+)$",
        "life_safety": r"^(elp\d+)\.(els\d+)\.(jb\d+)\.(em\d+)$",
    }

    # System-specific ID generators
    SYSTEM_GENERATORS = {
        "electrical":  lambda l1, l2, l3, l4: f"epnl{l1}.spnl{l2}.jb{l3:02d}.lf{l4:02d}",
        "hvac":        lambda l1, l2, l3, l4: f"ahu{l1}.zc{l2}.tu{l3:02d}.dv{l4:02d}",
        "plumbing":    lambda l1, l2, l3, l4: f"ms{l1}.fr{l2}.bl{l3:02d}.fx{l4:02d}",
        "fire_alarm":  lambda l1, l2, l3, l4: f"fac{l1}.nac{l2}.jb{l3:02d}.fa{l4:02d}",
        "telecom":     lambda l1, l2, l3, l4: f"idf{l1}.fdc{l2}.dp{l3:02d}.po{l4:02d}",
        "network":     lambda l1, l2, l3, l4: f"mcr{l1}.idc{l2}.dp{l3:02d}.eo{l4:02d}",
        "av":          lambda l1, l2, l3, l4: f"avc{l1}.amp{l2}.cb{l3:02d}.av{l4:02d}",
        "security":    lambda l1, l2, l3, l4: f"sec{l1}.cc{l2}.cb{l3:02d}.sc{l4:02d}",
        "bas":         lambda l1, l2, l3, l4: f"bcu{l1}.fc{l2}.lo{l3:02d}.bs{l4:02d}",
        "lighting":    lambda l1, l2, l3, l4: f"lcp{l1}.lcg{l2}.lcj{l3:02d}.ld{l4:02d}",
        "life_safety": lambda l1, l2, l3, l4: f"elp{l1}.els{l2}.jb{l3:02d}.em{l4:02d}",
    }

    # Legacy pattern
    LEGACY_PATTERN = re.compile(r"^[A-Z0-9]{3,10}_L[0-9]{1,2}_(E|LV|FA|N|M|P)_[A-Z][a-zA-Z]+_[0-9]{3}$")

    @classmethod
    def generate_system_object_id(cls, system: str, l1: int, l2: int, l3: int, l4: int) -> str:
        if system in cls.SYSTEM_GENERATORS:
            return cls.SYSTEM_GENERATORS[system](l1, l2, l3, l4)
        return f"lvl1{l1}.lvl2{l2}.lvl3{l3:02d}.lvl4{l4:02d}"

    @classmethod
    def is_valid_system_object_id(cls, object_id: str, system: str) -> bool:
        pattern = cls.SYSTEM_PATTERNS.get(system)
        if pattern:
            return re.match(pattern, object_id.lower()) is not None
        return False

    @classmethod
    def is_valid_any_object_id(cls, object_id: str) -> bool:
        if cls.LEGACY_PATTERN.match(object_id):
            return True
        for pattern in cls.SYSTEM_PATTERNS.values():
            if re.match(pattern, object_id.lower()):
                return True
        return False

    @classmethod
    def detect_system_from_id(cls, object_id: str) -> Optional[str]:
        object_id = object_id.lower()
        for system, pattern in cls.SYSTEM_PATTERNS.items():
            if re.match(pattern, object_id):
                return system
        return None

    @classmethod
    def parse_system_object_id(cls, object_id: str) -> Optional[Tuple[str, int, int, int, int]]:
        system = cls.detect_system_from_id(object_id)
        if not system:
            return None
        parts = object_id.split('.')
        if len(parts) != 4:
            return None
        try:
            l1 = cls._extract_number(parts[0])
            l2 = cls._extract_number(parts[1])
            l3 = cls._extract_number(parts[2])
            l4 = cls._extract_number(parts[3])
            return (system, l1, l2, l3, l4)
        except Exception:
            return None

    @staticmethod
    def _extract_number(s: str) -> int:
        match = re.search(r"(\d+)", s)
        return int(match.group(1)) if match else 0 