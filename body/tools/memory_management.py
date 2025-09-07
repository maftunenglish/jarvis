# body/tools/memory_management.py
from memory.long_term import long_term_memory
from datetime import datetime
import re
import json
from brain.utils.config_loader import config_loader
from pathlib import Path
import sqlite3

class JARVISMemoryManager:
    def __init__(self):
        self.personality = config_loader
        
    def manual_note_command(self, user_input: str) -> str:
        """
        Handle manual "note this" commands - store anything user explicitly asks to save
        Examples: 
        - "Note that my project deadline is Friday"
        - "Remember that I need to buy milk tomorrow"
        - "Store this in database: my license plate is ABC123"
        """
        note_patterns = [
            r"note (?:that|this|down) (.+)",
            r"remember (?:that|this) (.+)", 
            r"store (?:that|this|in database) (.+)",
            r"save (?:that|this|to memory) (.+)",
            r"add to memory (.+)",
            r"put in database (.+)"
        ]
        
        for pattern in note_patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                note_content = match.group(1).strip()
                
                # Extract potential attribute-value pair or store as freeform note
                if " is " in note_content:
                    parts = note_content.split(" is ", 1)
                    attribute = parts[0].strip()
                    value = parts[1].strip()
                else:
                    # Freeform note - use timestamp as attribute
                    attribute = f"manual_note_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    value = note_content
                
                # Store in database
                success = long_term_memory.add_fact("user", attribute, value)
                
                if success:
                    return f"Noted and stored in database, Sir. '{note_content}' has been archived."
                else:
                    return "Apologies, Sir. I encountered an issue storing that information."
        
        return None  # No manual note command detected
    
    def query_database_intelligently(self, user_input: str) -> str:
        """
        Smart database querying - understand what user might be asking from stored data
        """
        # Check if user is asking about stored information
        query_patterns = [
            r"what (?:is|are) my (.+)\??",
            r"do you know my (.+)\??",
            r"what did i tell you about my (.+)\??",
            r"recall my (.+)",
            r"what's my (.+)\??"
        ]
        
        for pattern in query_patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                attribute_query = match.group(1).strip()
                
                # Try exact match first
                fact = long_term_memory.get_current_fact("user", attribute_query)
                if fact:
                    return f"According to my records, Sir, your {attribute_query} is {fact['value']}."
                
                # Try partial matches (fuzzy search)
                all_facts = self._get_all_user_facts()
                relevant_facts = []
                
                for attr, val in all_facts.items():
                    if attribute_query in attr or any(word in attr for word in attribute_query.split()):
                        relevant_facts.append((attr, val))
                
                if relevant_facts:
                    if len(relevant_facts) == 1:
                        attr, val = relevant_facts[0]
                        return f"I have information about your {attr}, Sir: {val}"
                    else:
                        response = "I found several related facts, Sir:\n"
                        for attr, val in relevant_facts[:3]:  # Show top 3
                            response += f"- Your {attr}: {val}\n"
                        return response
                
                return f"I don't have any information about your {attribute_query} yet, Sir."
        
        return None
    
    def _get_all_user_facts(self) -> dict:
        """Get all current facts about user"""
        # This would need additional methods in long_term_memory
        # For now, placeholder implementation that preserves existing functionality
        try:
            # Try to get all facts if the method exists
            if hasattr(long_term_memory, 'get_all_facts'):
                return long_term_memory.get_all_facts("user")
        except:
            pass
        return {}
    
    def remember_fact(self, user_input: str) -> str:
        """
        Enhanced with manual note capability and smart querying
        """
        # First check if it's a manual note command
        note_response = self.manual_note_command(user_input)
        if note_response:
            return note_response
        
        # Then check if it's a database query
        query_response = self.query_database_intelligently(user_input)
        if query_response:
            return query_response
        
        # Then proceed with automatic fact extraction (your existing code)
        # ... [your existing automatic fact extraction code] ...
        
        # Preserve existing functionality - if you had automatic fact extraction here,
        # it should remain unchanged. If not, this returns the original response.
        return "I didn't detect a clear fact to remember, Sir."

# Preserve any existing functions that might have been in this file
# If you had other functions or classes here, they should remain unchanged


# Global instance for the new class-based system
memory_manager = JARVISMemoryManager()

# These functions maintain compatibility with existing code
def remember_fact(user_input: str) -> str:
    """
    Compatibility wrapper for existing code.
    Example: remember_fact("my name is Tony") → delegates to memory_manager
    """
    return memory_manager.remember_fact(user_input)

def recall_fact(user_input: str) -> str:
    """
    Compatibility wrapper for existing code.  
    Example: recall_fact("what is my name") → delegates to memory_manager
    """
    # Delegate to the memory manager's intelligent query system
    return memory_manager.query_database_intelligently(user_input)
# Add this temporary debug function to memory_management.py
# Add this function to your memory_management.py

# Then test with:
# debug_database()
def debug_database() -> str:
    """Debug function to show database contents"""
    try:
        conn = sqlite3.connect('memory/jarvis_memory.db')
        c = conn.cursor()
        
        # Get all current facts
        c.execute("""
            SELECT subject, attribute, value, valid_from 
            FROM facts 
            WHERE valid_until IS NULL
            ORDER BY subject, attribute
        """)
        facts = c.fetchall()
        
        # Get some history
        c.execute("""
            SELECT subject, attribute, value, valid_from, valid_until
            FROM facts 
            WHERE valid_until IS NOT NULL
            ORDER BY valid_from DESC 
            LIMIT 5
        """)
        history = c.fetchall()
        
        conn.close()
        
        response = "📊 Database Debug Information:\n\n"
        response += f"Current Facts: {len(facts)} entries\n"
        
        for subject, attribute, value, valid_from in facts:
            response += f"  {subject}.{attribute} = '{value}' (since {valid_from})\n"
        
        response += f"\nRecent History: {len(history)} entries\n"
        for subject, attribute, value, valid_from, valid_until in history:
            response += f"  {subject}.{attribute} = '{value}' ({valid_from} to {valid_until})\n"
        
        if not facts and not history:
            response += "  Database is empty or not accessible.\n"
            
        return response
        
    except Exception as e:
        return f"❌ Database debug error: {str(e)}"
def recall_fact(user_input: str) -> str:
    """
    Compatibility wrapper for existing code.  
    Example: recall_fact("what is my name") → delegates to memory_manager
    """
    return memory_manager.recall_fact(user_input)

# Optional: Also provide access to the manual note command
def manual_note_command(user_input: str) -> str:
    """Compatibility function for manual note commands"""
    return memory_manager.manual_note_command(user_input)

print("✅ Memory management system initialized with backward compatibility")


# Example of preserving existing functionality:
# If you had a function like this, it stays as-is:
def existing_function():
    """Any existing function should remain unchanged"""
    pass