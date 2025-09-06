# brain/llm_clients/openai_client.py
"""
Robust OpenAI client with API-key rotation and retry on rate-limits/errors.
"""

import os
import time
import math
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

try:
    from openai import (
        APIError,
        APIConnectionError,
        RateLimitError,
        APITimeoutError,
        AuthenticationError,
        BadRequestError,
    )
    from openai import OpenAI
except Exception as e:
    raise RuntimeError(
        "Please install/upgrade the 'openai' package (pip install --upgrade openai)."
    ) from e


class OpenAIClient:
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        default_cooldown: int = 60,
        max_retries_per_key: int = 1,
        min_request_interval: float = 3.0,
    ):
        load_dotenv()
        self.model = model
        self.default_cooldown = default_cooldown
        self.max_retries_per_key = max_retries_per_key
        self.min_request_interval = min_request_interval
        self.last_request_time = 0
        
        self._raw_keys = self._load_keys_from_env()
        if not self._raw_keys:
            raise RuntimeError("No OpenAI API keys found in environment.")

        self.keys_state = [
            {"key": k.strip(), "cooldown_until": 0.0, "bad": False}
            for k in self._raw_keys
        ]
        self.current_index = 0

    def _load_keys_from_env(self) -> List[str]:
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

    def _get_available_key_index(self) -> Optional[int]:
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

    def _mark_rate_limited(self, idx: int, cooldown: Optional[int] = None):
        self.keys_state[idx]["cooldown_until"] = time.time() + (
            cooldown or self.default_cooldown
        )
        print(
            f"[openai_client] Key at index {idx} put on cooldown until {self.keys_state[idx]['cooldown_until']}"
        )

    def _mark_bad(self, idx: int):
        self.keys_state[idx]["bad"] = True
        print(f"[openai_client] Key at index {idx} marked BAD (removed from rotation).")

    def _rotate_to_index(self, idx: int):
        self.current_index = idx

    def _rotate_next(self):
        """Advance current_index to next available key."""
        n = len(self.keys_state)
        for i in range(1, n + 1):
            cand = (self.current_index + i) % n
            if (
                not self.keys_state[cand]["bad"]
                and time.time() >= self.keys_state[cand]["cooldown_until"]
            ):
                self.current_index = cand
                return True
        return False

    def _select_and_apply_key(self) -> (int, OpenAI):
        idx = self._get_available_key_index()
        if idx is None:
            raise RuntimeError("All API keys are either on cooldown or invalid/blocked.")
        self._rotate_to_index(idx)
        key = self.keys_state[idx]["key"]
        print(f"[openai_client] Using key index {idx}.")
        return idx, OpenAI(api_key=key)

    def chat_completion(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Send chat completion request with automatic key failover and throttling."""
        # Request throttling
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            print(f"[openai_client] Throttling: waiting {sleep_time:.1f}s between requests")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

        last_exc = None

        while True:
            try:
                idx, client = self._select_and_apply_key()
            except RuntimeError as e:
                raise RuntimeError("No valid OpenAI API keys available: " + str(e))

            for attempt in range(1, self.max_retries_per_key + 1):
                try:
                    resp = client.chat.completions.create(
                        model=self.model, messages=messages, timeout=30.0, **kwargs
                    )
                    return resp
                except RateLimitError as e:
                    print(f"[openai_client] RateLimitError on key idx={idx}: attempt {attempt}: {e}")
                    self._mark_rate_limited(idx)
                    last_exc = e
                    break
                except (APIError, APIConnectionError, APITimeoutError) as e:
                    print(f"[openai_client] Service/API/Timeout error on key idx={idx}: {e}")
                    self._mark_rate_limited(idx, cooldown=10)
                    last_exc = e
                    break
                except AuthenticationError as e:
                    print(f"[openai_client] AuthenticationError (invalid key) idx={idx}: {e}")
                    self._mark_bad(idx)
                    last_exc = e
                    break
                except BadRequestError as e:
                    print(f"[openai_client] BadRequestError: {e}")
                    raise
                except Exception as e:
                    print(f"[openai_client] Unexpected error on key idx={idx}: {type(e).__name__}: {e}")
                    self._mark_rate_limited(idx, cooldown=5)
                    last_exc = e
                    break

            rotated = self._rotate_next()
            if not rotated:
                soonest = min(
                    (st["cooldown_until"] for st in self.keys_state if not st["bad"]),
                    default=None,
                )
                if soonest and soonest > time.time():
                    wait = max(1.0, soonest - time.time())
                    print(f"[openai_client] All keys on cooldown, waiting {math.ceil(wait)}s for earliest cooldown...")
                    time.sleep(wait + 0.5)
                    continue
                raise RuntimeError("Exhausted all API keys; last error: {}".format(last_exc))

            time.sleep(0.5)

    def say(self, text: str, **kwargs) -> str:
        messages = [{"role": "user", "content": text}]
        resp = self.chat_completion(messages=messages, **kwargs)
        try:
            return resp.choices[0].message.content
        except Exception:
            return str(resp)


def get_llm_response(user_input: str, context: list = None) -> str:
    """Compatibility function for existing code."""
    client = OpenAIClient()
    
    messages = []
    if context:
        for exchange in context[-3:]:
            messages.append({"role": "user", "content": exchange.get("user", "")})
            messages.append({"role": "assistant", "content": exchange.get("ai", "")})
    
    messages.append({"role": "user", "content": user_input})
    
    try:
        response = client.chat_completion(messages=messages)
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"