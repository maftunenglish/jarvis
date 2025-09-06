"""
API key management with rotation and cooldown.
"""
import os
import time
from typing import List, Dict, Optional

class KeyManager:
    def __init__(self, default_cooldown: int = 60):
        self.default_cooldown = default_cooldown
        self.keys_state = []
        self.current_index = 0
    
    def load_keys_from_env(self) -> List[str]:
        """Load API keys from environment variables."""
        keys = []

        # 1) comma separated list
        multi = os.getenv("OPENAI_API_KEYS")
        if multi:
            for k in multi.split(","):
                ks = k.strip()
                if ks:
                    keys.append(ks)

        # 2) single key var
        single = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
        if single:
            if single not in keys:
                keys.append(single.strip())

        # 3) numbered keys
        i = 1
        while True:
            kname = f"OPENAI_API_KEY_{i}"
            val = os.getenv(kname)
            if not val:
                break
            if val.strip() and val.strip() not in keys:
                keys.append(val.strip())
            i += 1

        return keys

    def get_available_key_index(self) -> Optional[int]:
        """Return index of next available key not on cooldown and not marked bad."""
        n = len(self.keys_state)
        for offset in range(n):
            idx = (self.current_index + offset) % n
            st = self.keys_state[idx]
            if st["bad"]:
                continue
            if time.time() >= st["cooldown_until"]:
                return idx
        return None

    def mark_rate_limited(self, idx: int, cooldown: Optional[int] = None):
        """Mark a key as rate-limited."""
        self.keys_state[idx]["cooldown_until"] = time.time() + (cooldown or self.default_cooldown)
        print(f"[key_manager] Key at index {idx} put on cooldown until {self.keys_state[idx]['cooldown_until']}")

    def mark_bad(self, idx: int):
        """Mark a key as bad (removed from rotation)."""
        self.keys_state[idx]["bad"] = True
        print(f"[key_manager] Key at index {idx} marked BAD (removed from rotation).")

    def rotate_next(self) -> bool:
        """Advance current_index to next available key."""
        n = len(self.keys_state)
        for i in range(1, n + 1):
            cand = (self.current_index + i) % n
            if (not self.keys_state[cand]["bad"] and 
                time.time() >= self.keys_state[cand]["cooldown_until"]):
                self.current_index = cand
                return True
        return False