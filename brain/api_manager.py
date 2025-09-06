# brain/api_manager.py
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

class APIManager:
    def __init__(self, db_path: str = "memory/api_keys.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_database()
        # Do NOT import keys here automatically if you want control from main.
        # But keep backward-compatible call:
        try:
            self.import_keys_from_env()
        except Exception:
            # If config/settings import fails, avoid crashing; main() can call import later.
            pass

    def _init_database(self):
        """Initialize the API keys database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY,
                service TEXT NOT NULL,
                api_key TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                rate_limit_reset DATETIME,
                usage_count INTEGER DEFAULT 0,
                last_used DATETIME,
                priority INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    # ---------- new helper ----------
    def _refresh_rate_limited_keys(self, service: str):
        """
        Reactivate keys whose rate_limit_reset timestamp is in the past.
        Runs before selecting keys.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "SELECT id, rate_limit_reset FROM api_keys WHERE service = ? AND status = 'rate_limited'",
            (service,),
        )
        rows = c.fetchall()
        now = datetime.now()
        updated = False
        for r in rows:
            key_id, reset_val = r
            if not reset_val:
                continue
            # stored string might be 'YYYY-MM-DD HH:MM:SS' or ISO; try parsing flexibly
            parsed = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
                try:
                    parsed = datetime.strptime(reset_val, fmt)
                    break
                except Exception:
                    continue
            if parsed is None:
                try:
                    # last attempt: fromisoformat (may raise)
                    parsed = datetime.fromisoformat(reset_val)
                except Exception:
                    parsed = None
            if parsed and parsed <= now:
                c.execute(
                    "UPDATE api_keys SET status = 'active', rate_limit_reset = NULL WHERE id = ?",
                    (key_id,),
                )
                updated = True
        if updated:
            conn.commit()
        conn.close()

    def add_api_key(self, service: str, api_key: str, priority: int = 1):
        """Add a new API key to the database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Check if key already exists
        c.execute("SELECT id FROM api_keys WHERE api_key = ?", (api_key,))
        if c.fetchone():
            conn.close()
            return False  # Key already exists

        c.execute(
            """
            INSERT INTO api_keys (service, api_key, priority)
            VALUES (?, ?, ?)
        """,
            (service, api_key, priority),
        )

        conn.commit()
        conn.close()
        return True

    def get_next_available_key(self, service: str) -> Optional[str]:
        """Get the next available API key, skipping rate-limited ones."""
        # First refresh rate-limited keys whose reset has passed
        self._refresh_rate_limited_keys(service)

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get active keys, ordered by priority (lowest first) then usage count (lowest first)
        c.execute(
            """
            SELECT id, api_key FROM api_keys 
            WHERE service = ? AND status = 'active'
            ORDER BY priority ASC, usage_count ASC
            LIMIT 1
        """,
            (service,),
        )

        result = c.fetchone()

        if result:
            key_id, api_key = result
            # Update usage statistics
            c.execute(
                """
                UPDATE api_keys 
                SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (key_id,),
            )
            conn.commit()
            conn.close()
            return api_key

        conn.close()
        return None

    def mark_key_rate_limited(self, api_key: str, reset_time: datetime = None):
        """Mark a key as rate-limited. reset_time is a datetime or None (defaults to now+1h)."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        reset_time = reset_time or (datetime.now() + timedelta(hours=1))
        # Store as ISO-like string
        reset_str = reset_time.strftime("%Y-%m-%d %H:%M:%S")

        c.execute(
            """
            UPDATE api_keys 
            SET status = 'rate_limited', rate_limit_reset = ?
            WHERE api_key = ?
        """,
            (reset_str, api_key),
        )

        conn.commit()
        conn.close()

    def get_key_status(self, service: str) -> List[Dict]:
        """Get status of all keys for a service (masked for display)."""
        # Refresh rate-limited keys first
        self._refresh_rate_limited_keys(service)

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(
            """
            SELECT api_key, status, rate_limit_reset, usage_count, priority
            FROM api_keys WHERE service = ?
            ORDER BY priority ASC, usage_count ASC
        """,
            (service,),
        )

        keys = []
        for row in c.fetchall():
            api_key_full = row[0]
            keys.append(
                {
                    "api_key": api_key_full[:8] + "..." + api_key_full[-4:],  # Mask key for security
                    "status": row[1],
                    "rate_limit_reset": row[2],
                    "usage_count": row[3],
                    "priority": row[4],
                }
            )

        conn.close()
        return keys

    # ---------- new method ----------
    def get_unmasked_keys(self, service: str) -> List[str]:
        """
        Return full (unmasked) keys for programmatic use, ordered by priority/usage.
        WARNING: only call this internally; do NOT print these.
        """
        # Refresh rate-limited keys first
        self._refresh_rate_limited_keys(service)

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(
            """
            SELECT api_key FROM api_keys 
            WHERE service = ? AND status = 'active'
            ORDER BY priority ASC, usage_count ASC
        """,
            (service,),
        )
        rows = c.fetchall()
        conn.close()
        return [r[0] for r in rows]

    def import_keys_from_env(self):
        """
        Import API keys from environment variables for initial setup.
        Returns number of keys imported.
        """
        # Lazy import of settings so this module can be imported without config present.
        try:
            from config import settings
        except Exception:
            # if config package not available, skip import
            return 0

        imported_count = 0

        # Check if key already exists in database to avoid duplicates
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Import from multiple keys (OPENAI_API_KEY_1 to _5)
        for i in range(1, 6):
            env_var_name = f"OPENAI_API_KEY_{i}"
            if hasattr(settings, env_var_name):
                api_key = getattr(settings, env_var_name)
                if api_key:
                    # Check if key already exists
                    c.execute("SELECT id FROM api_keys WHERE api_key = ?", (api_key,))
                    if not c.fetchone():  # Only add if not exists
                        if self.add_api_key("openai", api_key, priority=i):
                            imported_count += 1
                            print(f"✅ Imported {env_var_name} (priority {i})")

        conn.close()

        if imported_count == 0:
            print("No API keys found in environment. Use 'add api key' command.")

        return imported_count

    def remove_api_key(self, priority: int) -> bool:
        """Remove an API key by priority."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("DELETE FROM api_keys WHERE priority = ?", (priority,))
        changes = conn.total_changes

        conn.commit()
        conn.close()

        return changes > 0


# Global API manager instance
api_manager = APIManager()
