"""
Token usage tracking with daily limits and persistence.
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Any

class TokenTracker:
    def __init__(self, daily_limit: int = 100000, data_file: str = "openai_token_usage.json"):
        self.daily_limit = daily_limit
        self.data_file = Path(data_file)
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load token usage data from file with daily reset."""
        default_data = {
            "tokens_used_today": 0,
            "tokens_used_total": 0,
            "last_reset_date": time.strftime("%Y-%m-%d"),
            "request_count_today": 0,
            "request_count_total": 0,
        }

        try:
            if self.data_file.exists():
                with open(self.data_file, "r") as f:
                    data = json.load(f)

                # Reset daily counter if new day
                current_date = time.strftime("%Y-%m-%d")
                if data.get("last_reset_date") != current_date:
                    data["tokens_used_today"] = 0
                    data["request_count_today"] = 0
                    data["last_reset_date"] = current_date

                # Ensure all keys exist
                for key in default_data:
                    if key not in data:
                        data[key] = default_data[key]

                return data
        except Exception as e:
            print(f"[token_tracker] Error loading token usage: {e}")

        return default_data

    def _save_data(self):
        """Save token usage data to file."""
        try:
            with open(self.data_file, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"[token_tracker] Error saving token usage: {e}")

    def check_limits(self) -> tuple:
        """Check if token usage is within limits."""
        if self.data["tokens_used_today"] >= self.daily_limit:
            return (
                False,
                f"Daily token limit reached ({self.data['tokens_used_today']}/{self.daily_limit})",
            )
        return True, ""

    def estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """Estimate token count for messages (approx 4 chars per token + overhead)."""
        total_chars = 0
        for message in messages:
            total_chars += len(str(message.get("content", "")))
            total_chars += len(str(message.get("role", "")))
            total_chars += len(str(message.get("name", "")))

        # Approximate token count (4 chars per token + 4 tokens per message overhead)
        estimated_tokens = (total_chars // 4) + (len(messages) * 4)
        return estimated_tokens

    def update_usage(self, tokens_used: int):
        """Update token usage statistics."""
        self.data["tokens_used_today"] += tokens_used
        self.data["tokens_used_total"] += tokens_used
        self.data["request_count_today"] += 1
        self.data["request_count_total"] += 1
        self._save_data()

    def get_stats(self) -> Dict:
        """Get current token usage statistics."""
        return {
            "tokens_used_today": self.data["tokens_used_today"],
            "daily_token_limit": self.daily_limit,
            "tokens_remaining_today": max(0, self.daily_limit - self.data["tokens_used_today"]),
            "tokens_used_total": self.data["tokens_used_total"],
            "request_count_today": self.data["request_count_today"],
            "request_count_total": self.data["request_count_total"],
            "last_reset_date": self.data["last_reset_date"],
        }