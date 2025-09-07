# memory/chat_logger.py
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import threading
import time

class ChatLogger:
    def __init__(self, logs_dir: str = "memory/chat_sessions"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.current_session: List[Dict] = []
        self.session_start_time = None
        self.auto_save_interval = 300  # seconds between auto-saves
        self._stop_auto_save = False
        self._auto_save_thread = None
        
    def start_new_session(self):
        """Start a new chat session with auto-saving"""
        self.current_session = []
        self.session_start_time = datetime.now()
        self._start_auto_save()
        print("💬 New chat session started")
    
    def log_message(self, user: str, message: str, response: str = ""):
        """Log a message exchange with additional metadata"""
        timestamp = datetime.now()
        entry = {
            "timestamp": timestamp.isoformat(),
            "user": user,
            "message": message,
            "response": response,
            "message_length": len(message),
            "response_length": len(response) if response else 0,
            "message_words": len(message.split()),
            "response_words": len(response.split()) if response else 0
        }
        self.current_session.append(entry)
        
        # Auto-save if session is getting large
        if len(self.current_session) % 20 == 0:  # Every 5 messages
            self.save_session(autosave=True)
    
    def _start_auto_save(self):
        """Start background thread for automatic session saving"""
        if self._auto_save_thread and self._auto_save_thread.is_alive():
            self._stop_auto_save = True
            self._auto_save_thread.join(timeout=1.0)
        
        self._stop_auto_save = False
        self._auto_save_thread = threading.Thread(target=self._auto_save_worker, daemon=True)
        self._auto_save_thread.start()
    
    def _auto_save_worker(self):
        """Background worker for automatic saving"""
        while not self._stop_auto_save:
            time.sleep(self.auto_save_interval)
            if self.current_session:
                self.save_session(autosave=True)
    
    def save_session(self, autosave: bool = False):
        """Save current session to file with enhanced metadata"""
        if not self.current_session:
            return None
        
        try:
            timestamp = datetime.now()
            filename = f"session_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.logs_dir / filename
            
            # Calculate statistics
            user_messages = [m for m in self.current_session if m['user'] == 'user']
            ai_messages = [m for m in self.current_session if m['user'] == 'ai']
            
            session_data = {
                "metadata": {
                    "session_id": filename.replace('.json', ''),
                    "session_start": self.current_session[0]['timestamp'],
                    "session_end": timestamp.isoformat(),
                    "total_messages": len(self.current_session),
                    "user_messages": len(user_messages),
                    "ai_messages": len(ai_messages),
                    "total_user_chars": sum(m['message_length'] for m in user_messages),
                    "total_ai_chars": sum(m['response_length'] for m in ai_messages),
                    "total_user_words": sum(m['message_words'] for m in user_messages),
                    "total_ai_words": sum(m['response_words'] for m in ai_messages),
                    "autosave": autosave,
                    "session_duration_seconds": (
                        datetime.fromisoformat(self.current_session[-1]['timestamp']) - 
                        datetime.fromisoformat(self.current_session[0]['timestamp'])
                    ).total_seconds() if len(self.current_session) > 1 else 0
                },
                "messages": self.current_session
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            if not autosave:
                print(f"💾 Chat session saved: {filename}")
            else:
                print(f"💾 Autosaved session: {filename}")
            
            return filepath
            
        except Exception as e:
            print(f"❌ Error saving chat session: {e}")
            return None
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about current session"""
        if not self.current_session:
            return {}
        
        user_messages = [m for m in self.current_session if m['user'] == 'user']
        ai_messages = [m for m in self.current_session if m['user'] == 'ai']
        
        return {
            "total_messages": len(self.current_session),
            "user_messages": len(user_messages),
            "ai_messages": len(ai_messages),
            "total_user_chars": sum(m['message_length'] for m in user_messages),
            "total_ai_chars": sum(m['response_length'] for m in ai_messages),
            "session_duration": self._get_session_duration()
        }
    
    def _get_session_duration(self) -> str:
        """Calculate session duration"""
        if not self.current_session:
            return "0 seconds"
        
        try:
            start = datetime.fromisoformat(self.current_session[0]['timestamp'])
            end = datetime.fromisoformat(self.current_session[-1]['timestamp'])
            duration = end - start
            return str(duration)
        except:
            return "Unknown"
    
    def load_session(self, session_id: str) -> List[Dict]:
        """Load a specific session from file"""
        filepath = self.logs_dir / f"{session_id}.json"
        
        if not filepath.exists():
            print(f"❌ Session file not found: {session_id}")
            return []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            return session_data.get('messages', [])
        except Exception as e:
            print(f"❌ Error loading session {session_id}: {e}")
            return []
    
    def list_sessions(self, days: int = 30) -> List[Dict]:
        """List all available sessions from last X days"""
        sessions = []
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for session_file in self.logs_dir.glob("session_*.json"):
            if session_file.stat().st_mtime >= cutoff_time:
                sessions.append({
                    "filename": session_file.name,
                    "size_kb": round(session_file.stat().st_size / 1024, 2),
                    "modified": datetime.fromtimestamp(session_file.stat().st_mtime),
                    "path": str(session_file)
                })
        
        return sorted(sessions, key=lambda x: x['modified'], reverse=True)
    
    def cleanup_old_sessions(self, days_to_keep: int = 90):
        """Clean up sessions older than X days"""
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        deleted_count = 0
        
        for session_file in self.logs_dir.glob("session_*.json"):
            if session_file.stat().st_mtime < cutoff_time:
                try:
                    session_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ Error deleting {session_file.name}: {e}")
        
        print(f"🗑️ Cleaned up {deleted_count} old session files")
    
    def stop(self):
        """Stop the logger and save current session"""
        self._stop_auto_save = True
        if self._auto_save_thread and self._auto_save_thread.is_alive():
            self._auto_save_thread.join(timeout=2.0)
        
        if self.current_session:
            self.save_session()
            print("✅ Chat logger stopped and session saved")
    
    def export_session(self, session_id: str, format: str = "json") -> bool:
        """Export session to different formats"""
        messages = self.load_session(session_id)
        if not messages:
            return False
        
        if format == "txt":
            filename = f"{session_id}.txt"
            with open(self.logs_dir / filename, 'w', encoding='utf-8') as f:
                for msg in messages:
                    f.write(f"[{msg['timestamp']}] {msg['user']}: {msg['message']}\n")
                    if msg['response']:
                        f.write(f"[{msg['timestamp']}] AI: {msg['response']}\n")
                    f.write("\n")
            return True
        
        return False

# Simple usage example
if __name__ == "__main__":
    logger = ChatLogger()
    logger.start_new_session()
    
    # Example usage
    logger.log_message("user", "Hello Jarvis!")
    logger.log_message("ai", "Hello Sir! How may I assist you?")
    
    print("Session stats:", logger.get_session_stats())
    logger.save_session()