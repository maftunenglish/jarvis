# brain/chat_learner.py
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
from body.tools.memory_management import JARVISMemoryManager

class ChatHistoryLearner:
    def __init__(self, logs_dir: str = "memory/chat_sessions"):
        self.logs_dir = Path(logs_dir)
        self.memory_manager = JARVISMemoryManager()
        self.learning_patterns = self._initialize_learning_patterns()
    
    def _initialize_learning_patterns(self) -> List[Dict]:
        """Initialize patterns for what to learn from chat history"""
        return [
            # Personal information
            {
                "pattern": r"(?:my|i am|i'm) (\d+) years? old",
                "attribute": "age",
                "confidence": 0.9,
                "description": "Extract age information"
            },
            {
                "pattern": r"my (?:name|full name) is ([a-zA-Z\s]+)",
                "attribute": "full_name",
                "confidence": 0.95,
                "description": "Extract full name"
            },
            {
                "pattern": r"i live in ([a-zA-Z\s\.,]+)",
                "attribute": "city",
                "confidence": 0.8,
                "description": "Extract city of residence"
            },
            {
                "pattern": r"i am from ([a-zA-Z\s\.,]+)",
                "attribute": "hometown",
                "confidence": 0.8,
                "description": "Extract hometown"
            },
            # Family information
            {
                "pattern": r"my (father|mother)'s name is ([a-zA-Z\s]+)",
                "attribute": lambda m: f"{m[1]}_name",
                "value": lambda m: m[2],
                "confidence": 0.85,
                "description": "Extract family member names"
            },
            {
                "pattern": r"i have (a|an) ([a-zA-Z\s]+) (brother|sister)",
                "attribute": lambda m: f"{m[2]}_sibling",
                "value": lambda m: f"{m[1]} {m[2]}",
                "confidence": 0.7,
                "description": "Extract sibling information"
            },
            # Preferences and favorites
            {
                "pattern": r"my favorite (food|color|sport|movie|book) is ([a-zA-Z\s]+)",
                "attribute": lambda m: f"favorite_{m[1]}",
                "value": lambda m: m[2],
                "confidence": 0.75,
                "description": "Extract favorite things"
            },
            {
                "pattern": r"i (really|absolutely) love ([a-zA-Z\s]+)",
                "attribute": "strong_preference",
                "confidence": 0.7,
                "description": "Extract strong preferences"
            },
            # Work and education
            {
                "pattern": r"i work as (a|an) ([a-zA-Z\s]+)",
                "attribute": "occupation",
                "confidence": 0.8,
                "description": "Extract occupation"
            },
            {
                "pattern": r"i work at ([a-zA-Z\s\.]+)",
                "attribute": "company",
                "confidence": 0.7,
                "description": "Extract company"
            },
            {
                "pattern": r"i studied ([a-zA-Z\s]+) at ([a-zA-Z\s]+)",
                "attribute": "education",
                "value": lambda m: f"{m[1]} at {m[2]}",
                "confidence": 0.7,
                "description": "Extract education"
            },
            # Important dates and events
            {
                "pattern": r"my (birthday|anniversary) is on ([a-zA-Z0-9\s]+)",
                "attribute": lambda m: m[1],
                "value": lambda m: m[2],
                "confidence": 0.8,
                "description": "Extract important dates"
            }
        ]
    
    def learn_from_recent_sessions(self, days: int = 7, max_sessions: int = 20) -> Dict[str, Any]:
        """Learn from chat sessions in the past X days with enhanced reporting"""
        results = {
            "sessions_processed": 0,
            "facts_learned": 0,
            "errors": 0,
            "session_details": []
        }
        
        session_files = self._get_recent_session_files(days, max_sessions)
        
        for session_file in session_files:
            try:
                session_facts = self._process_session_file(session_file)
                results["sessions_processed"] += 1
                results["facts_learned"] += len(session_facts)
                results["session_details"].append({
                    "session": session_file.name,
                    "facts_learned": len(session_facts),
                    "facts": session_facts
                })
                
            except Exception as e:
                results["errors"] += 1
                print(f"❌ Error processing {session_file.name}: {e}")
        
        return results
    
    def _get_recent_session_files(self, days: int, max_sessions: int) -> List[Path]:
        """Get list of recent session files, sorted by date (newest first)"""
        session_files = []
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # Get all session files and sort by modification time (newest first)
        all_files = list(self.logs_dir.glob("session_*.json"))
        all_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        for session_file in all_files:
            if datetime.fromtimestamp(session_file.stat().st_mtime) >= cutoff_time:
                session_files.append(session_file)
                if len(session_files) >= max_sessions:
                    break
        
        return session_files
    
    def _process_session_file(self, filepath: Path) -> List[Dict]:
        """Extract learnings from a session file with pattern matching"""
        learned_facts = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            messages = session_data.get('messages', [])
            
            for message in messages:
                if message.get('user') == 'user':  # Only learn from user messages
                    user_message = message.get('message', '')
                    if user_message:
                        # Extract facts using pattern matching
                        facts = self._extract_facts_with_patterns(user_message)
                        learned_facts.extend(facts)
            
            return learned_facts
            
        except Exception as e:
            print(f"Error processing session file {filepath}: {e}")
            return []
    
    def _extract_facts_with_patterns(self, message: str) -> List[Dict]:
        """Extract facts from message using configured patterns"""
        extracted_facts = []
        
        for pattern_config in self.learning_patterns:
            try:
                matches = re.finditer(pattern_config["pattern"], message.lower())
                
                for match in matches:
                    # Handle dynamic attribute extraction
                    if callable(pattern_config.get("attribute")):
                        attribute = pattern_config["attribute"](match)
                    else:
                        attribute = pattern_config["attribute"]
                    
                    # Handle dynamic value extraction
                    if callable(pattern_config.get("value")):
                        value = pattern_config["value"](match)
                    else:
                        # Default: use first capture group
                        value = match.group(1).strip() if match.groups() else match.group(0)
                    
                    # Store the fact using memory manager
                    result = self.memory_manager.remember_fact(
                        f"user {attribute} is {value}"
                    )
                    
                    if "stored" in result.lower() or "remembered" in result.lower():
                        extracted_facts.append({
                            "attribute": attribute,
                            "value": value,
                            "confidence": pattern_config.get("confidence", 0.7),
                            "source_message": message[:100] + "..." if len(message) > 100 else message
                        })
                        
            except Exception as e:
                print(f"Error applying pattern {pattern_config.get('pattern')}: {e}")
                continue
        
        return extracted_facts
    
    def learn_from_specific_session(self, session_id: str) -> List[Dict]:
        """Learn from a specific session file"""
        session_file = self.logs_dir / f"{session_id}.json"
        if session_file.exists():
            return self._process_session_file(session_file)
        return []
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get statistics about available sessions and learning patterns"""
        session_files = list(self.logs_dir.glob("session_*.json"))
        
        return {
            "total_sessions": len(session_files),
            "sessions_last_7_days": len(self._get_recent_session_files(7, 1000)),
            "sessions_last_30_days": len(self._get_recent_session_files(30, 1000)),
            "learning_patterns_count": len(self.learning_patterns),
            "patterns_by_category": self._get_patterns_by_category()
        }
    
    def _get_patterns_by_category(self) -> Dict[str, int]:
        """Categorize learning patterns for statistics"""
        categories = {
            "personal": 0,
            "family": 0,
            "preferences": 0,
            "work_education": 0,
            "dates_events": 0
        }
        
        personal_keywords = ["name", "age", "city", "hometown", "live", "from"]
        family_keywords = ["father", "mother", "brother", "sister", "family"]
        preference_keywords = ["favorite", "love", "like", "prefer"]
        work_keywords = ["work", "job", "occupation", "company", "studied", "education"]
        date_keywords = ["birthday", "anniversary", "date", "schedule"]
        
        for pattern in self.learning_patterns:
            pattern_str = str(pattern.get("pattern", ""))
            
            if any(keyword in pattern_str for keyword in personal_keywords):
                categories["personal"] += 1
            elif any(keyword in pattern_str for keyword in family_keywords):
                categories["family"] += 1
            elif any(keyword in pattern_str for keyword in preference_keywords):
                categories["preferences"] += 1
            elif any(keyword in pattern_str for keyword in work_keywords):
                categories["work_education"] += 1
            elif any(keyword in pattern_str for keyword in date_keywords):
                categories["dates_events"] += 1
        
        return categories
    
    def add_custom_pattern(self, pattern: str, attribute: str, confidence: float = 0.7) -> bool:
        """Add a custom learning pattern dynamically"""
        try:
            new_pattern = {
                "pattern": pattern,
                "attribute": attribute,
                "confidence": confidence,
                "description": f"Custom pattern: {pattern}"
            }
            self.learning_patterns.append(new_pattern)
            return True
        except Exception as e:
            print(f"Error adding custom pattern: {e}")
            return False
    
    def list_learning_patterns(self) -> List[Dict]:
        """List all configured learning patterns"""
        return [
            {
                "pattern": p.get("pattern"),
                "attribute": p.get("attribute"),
                "confidence": p.get("confidence", 0.7),
                "description": p.get("description", "No description")
            }
            for p in self.learning_patterns
        ]
    
    def export_learning_report(self, output_path: str) -> bool:
        """Export a report of learning statistics and patterns"""
        try:
            report = {
                "generated_at": datetime.now().isoformat(),
                "statistics": self.get_learning_statistics(),
                "patterns": self.list_learning_patterns(),
                "recent_learning": self.learn_from_recent_sessions(7, 10)
            }
            
            output_file = Path(output_path) / "learning_report.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"📊 Learning report exported to: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting learning report: {e}")
            return False

# Usage example
if __name__ == "__main__":
    learner = ChatHistoryLearner()
    
    # Learn from recent sessions
    results = learner.learn_from_recent_sessions(days=7)
    print(f"📚 Learned {results['facts_learned']} facts from {results['sessions_processed']} sessions")
    
    # Show statistics
    stats = learner.get_learning_statistics()
    print(f"Total sessions: {stats['total_sessions']}")
    print(f"Learning patterns: {stats['learning_patterns_count']}")