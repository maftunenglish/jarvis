# body/tools/memory_management.py
from memory.long_term import long_term_memory
from datetime import datetime
import re


def remember_fact(user_input: str) -> str:
    """
    Extracts and stores facts from natural language.
    Example: "My favorite color is blue" -> stores fact
    """
    try:
        # Pattern matching for fact statements
        patterns = [
            r"my (.*?) is (.*)",
            r"i like (.*)",
            r"i love (.*)",
            r"remember that (.*?) is (.*)",
            r"store that (.*?) = (.*)",
        ]

        for pattern in patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                if pattern == r"i like (.*)" or pattern == r"i love (.*)":
                    attribute = "preference"
                    value = match.group(1)
                else:
                    attribute = match.group(1)
                    value = match.group(2)

                # Store in long-term memory
                long_term_memory.add_fact("user", attribute, value)
                return f"I have remembered that your {attribute} is {value}, Sir."

        return "I didn't detect a clear fact to remember. Please try phrasing like 'My favorite color is blue'."

    except Exception as e:
        return (
            f"Apologies, Sir. I encountered an error storing that information: {str(e)}"
        )


def recall_fact(user_input: str) -> str:
    """
    Recalls facts from memory based on queries.
    Example: "What is my favorite color?" -> recalls fact
    """
    try:
        # Pattern matching for recall queries
        if "what is my" in user_input:
            attribute = user_input.split("what is my ")[1].replace("?", "").strip()
            fact = long_term_memory.get_current_fact("user", attribute)
            if fact:
                return f"Your {attribute} is {fact['value']}, Sir."
            else:
                return f"I don't have information about your {attribute} yet, Sir."

        # Historical query: "What was my favorite color before 2025-07-21?"
        elif "before" in user_input and "what was my" in user_input:
            parts = user_input.split("before")
            attribute_part = parts[0].replace("what was my", "").strip()
            date_str = parts[1].strip()

            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d")
                attribute = attribute_part.replace("?", "").strip()

                fact = long_term_memory.get_fact_at_time("user", attribute, target_date)
                if fact:
                    return (
                        f"Before {date_str}, your {attribute} was {fact['value']}, Sir."
                    )
                else:
                    return (
                        f"I have no record of your {attribute} before {date_str}, Sir."
                    )
            except ValueError:
                return (
                    "I couldn't understand the date format. Please use YYYY-MM-DD, Sir."
                )

        return "I didn't understand what you wanted me to recall, Sir."

    except Exception as e:
        return f"Apologies, Sir. I encountered an error retrieving that information: {str(e)}"
