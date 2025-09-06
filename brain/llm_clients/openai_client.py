# brain/llm_clients/openai_client.py
"""
Robust OpenAI client with API-key rotation, retry on rate-limits/errors, and token usage tracking.
Now with J.A.R.V.I.S. personality integration.
"""

import os
import time
import math
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Import utility classes
from brain.llm_utils.token_tracker import TokenTracker
from brain.llm_utils.key_manager import KeyManager

# Import personality config
from brain.utils.config_loader import config_loader

try:
    from openai import (
        APIError, APIConnectionError, RateLimitError, APITimeoutError, 
        AuthenticationError, BadRequestError, OpenAI
    )
except Exception as e:
    raise RuntimeError("Please install/upgrade the 'openai' package.") from e

class OpenAIClient:
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        default_cooldown: int = 60,
        max_retries_per_key: int = 1,
        min_request_interval: float = 3.0,
        daily_token_limit: int = 100000,
        max_tokens_per_request: int = 2000,
    ):
        load_dotenv()
        self.model = model
        self.max_retries_per_key = max_retries_per_key
        self.min_request_interval = min_request_interval
        self.max_tokens_per_request = max_tokens_per_request
        self.last_request_time = 0

        # Initialize managers
        self.key_manager = KeyManager(default_cooldown)
        self.token_tracker = TokenTracker(daily_token_limit)
        
        # Initialize personality configuration
        self.personality = config_loader
        self.user_address = self.personality.get_user_address()

        # Load keys
        raw_keys = self.key_manager.load_keys_from_env()
        if not raw_keys:
            raise RuntimeError("No OpenAI API keys found in environment.")

        self.key_manager.keys_state = [
            {"key": k.strip(), "cooldown_until": 0.0, "bad": False} for k in raw_keys
        ]

        print(f"[openai_client] Token usage: {self.token_tracker.data['tokens_used_today']}/{daily_token_limit} today")
        print(f"[openai_client] Personality: {self.personality.get_personality_traits()['name']}")
        print(f"[openai_client] Addressing user as: {self.user_address}")

    def _apply_personality_system_prompt(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply J.A.R.V.I.S. personality system prompt to messages if not already present."""
        # Check if system prompt already exists
        has_system_prompt = any(msg.get('role') == 'system' for msg in messages)
        
        if not has_system_prompt:
            # Insert J.A.R.V.I.S. system prompt at the beginning
            system_message = {"role": "system", "content": self.personality.get_system_prompt()}
            return [system_message] + messages
        
        return messages

    def _apply_personality_post_processing(self, response: str) -> str:
        """Apply J.A.R.V.I.S. personality post-processing to responses."""
        # Remove emojis if disabled in personality
        if not self.personality.should_use_emojis():
            response = self._remove_emojis(response)
        
        # Ensure professional tone
        response = self._ensure_professional_tone(response)
        
        return response

    def _remove_emojis(self, text: str) -> str:
        """Remove emojis from text (J.A.R.V.I.S. doesn't use emojis)."""
        import re
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "]+", flags=re.UNICODE
        )
        return emoji_pattern.sub(r'', text)

    def _ensure_professional_tone(self, text: str) -> str:
        """Ensure response maintains J.A.R.V.I.S. professional tone."""
        import re
        # Remove excessive informality
        informal_patterns = [
            r'\b(lol|rofl|lmao|haha|hehe)\b',
            r'\b(omg|wtf|smh)\b',
            r'!!!+',
            r'\?\!+',
            r'\.\.\.+'
        ]
        
        for pattern in informal_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text

    def _truncate_messages_if_needed(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Truncate messages if they exceed the maximum tokens per request."""
        estimated_tokens = self.token_tracker.estimate_tokens(messages)

        if estimated_tokens <= self.max_tokens_per_request:
            return messages

        print(f"[openai_client] Warning: Message too long ({estimated_tokens} tokens), truncating...")

        # Keep system messages intact, truncate user messages
        truncated_messages = []
        remaining_tokens = self.max_tokens_per_request

        for message in messages:
            if message["role"] == "system":
                truncated_messages.append(message)
                sys_tokens = self.token_tracker.estimate_tokens([message])
                remaining_tokens -= sys_tokens
            else:
                content = message["content"]
                max_chars = remaining_tokens * 4

                if len(content) > max_chars:
                    truncated_content = content[:max_chars - 100] + "... [truncated]"
                    truncated_message = message.copy()
                    truncated_message["content"] = truncated_content
                    truncated_messages.append(truncated_message)
                    break
                else:
                    truncated_messages.append(message)
                    remaining_tokens -= self.token_tracker.estimate_tokens([message])

        return truncated_messages

    def _select_and_apply_key(self) -> tuple:
        """Select and apply the next available API key."""
        idx = self.key_manager.get_available_key_index()
        if idx is None:
            raise RuntimeError("All API keys are either on cooldown or invalid/blocked.")
        
        self.key_manager.current_index = idx
        key = self.key_manager.keys_state[idx]["key"]
        print(f"[openai_client] Using key index {idx}.")
        return idx, OpenAI(api_key=key)

    def get_token_usage_stats(self) -> Dict:
        """Get current token usage statistics."""
        return self.token_tracker.get_stats()

    def chat_completion(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Send chat completion request with automatic key failover, throttling, and token tracking."""
        # Check token limits
        can_proceed, reason = self.token_tracker.check_limits()
        if not can_proceed:
            raise RuntimeError(f"Token limit exceeded: {reason}")

        # Apply J.A.R.V.I.S. personality system prompt
        messages = self._apply_personality_system_prompt(messages)

        # Truncate messages if needed
        messages = self._truncate_messages_if_needed(messages)

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

                    # Track token usage
                    if hasattr(resp, "usage") and resp.usage:
                        tokens_used = resp.usage.total_tokens
                        self.token_tracker.update_usage(tokens_used)

                        print(f"[openai_client] Used {tokens_used} tokens (Total today: {self.token_tracker.data['tokens_used_today']})")

                        # Warn if approaching limit
                        if self.token_tracker.data["tokens_used_today"] > self.token_tracker.daily_limit * 0.8:
                            remaining = self.token_tracker.daily_limit - self.token_tracker.data["tokens_used_today"]
                            print(f"⚠️ [openai_client] Warning: {remaining} tokens remaining today")

                    return resp

                except RateLimitError as e:
                    print(f"[openai_client] RateLimitError on key idx={idx}: attempt {attempt}: {e}")
                    self.key_manager.mark_rate_limited(idx)
                    last_exc = e
                    break
                except (APIError, APIConnectionError, APITimeoutError) as e:
                    print(f"[openai_client] Service/API/Timeout error on key idx={idx}: {e}")
                    self.key_manager.mark_rate_limited(idx, cooldown=10)
                    last_exc = e
                    break
                except AuthenticationError as e:
                    print(f"[openai_client] AuthenticationError (invalid key) idx={idx}: {e}")
                    self.key_manager.mark_bad(idx)
                    last_exc = e
                    break
                except BadRequestError as e:
                    print(f"[openai_client] BadRequestError: {e}")
                    raise
                except Exception as e:
                    print(f"[openai_client] Unexpected error on key idx={idx}: {type(e).__name__}: {e}")
                    self.key_manager.mark_rate_limited(idx, cooldown=5)
                    last_exc = e
                    break

            rotated = self.key_manager.rotate_next()
            if not rotated:
                soonest = min(
                    (st["cooldown_until"] for st in self.key_manager.keys_state if not st["bad"]),
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
        """Convenience method for single messages with personality processing."""
        messages = [{"role": "user", "content": text}]
        resp = self.chat_completion(messages=messages, **kwargs)
        try:
            response_text = resp.choices[0].message.content
            # Apply J.A.R.V.I.S. personality post-processing
            return self._apply_personality_post_processing(response_text)
        except Exception:
            # Use personality-specific error response
            return self.personality.get_error_response()

def get_llm_response(user_input: str, context: list = None) -> str:
    """Compatibility function for existing code with personality integration."""
    client = OpenAIClient()

    messages = []
    if context:
        for exchange in context[-3:]:
            messages.append({"role": "user", "content": exchange.get("user", "")})
            messages.append({"role": "assistant", "content": exchange.get("ai", "")})

    messages.append({"role": "user", "content": user_input})

    try:
        response = client.chat_completion(messages=messages)
        response_text = response.choices[0].message.content
        # Apply personality post-processing
        return client._apply_personality_post_processing(response_text)
    except Exception as e:
        # Use personality-specific error response
        return client.personality.get_error_response() + f" Technical details: {str(e)}"