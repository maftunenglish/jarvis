# memory/long_term.py
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import os
import shutil
from pathlib import Path

class LongTermMemory:
    def __init__(self, db_path: str = 'memory/jarvis_memory.db'):
        # Ensure the memory directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.backup_path = f"{db_path}.backup"
        self._init_database()
    
    def _is_database_corrupted(self) -> bool:
        """Check if the database is corrupted."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA integrity_check;")
            conn.close()
            return False
        except sqlite3.DatabaseError:
            return True
    
    def _backup_corrupted_database(self):
        """Backup the corrupted database before recreating it."""
        if os.path.exists(self.db_path):
            try:
                if os.path.exists(self.backup_path):
                    os.remove(self.backup_path)
                shutil.copy2(self.db_path, self.backup_path)
                print(f"⚠️ Backed up corrupted database to {self.backup_path}")
            except Exception as e:
                print(f"❌ Failed to backup corrupted database: {e}")
    
    def _recreate_database(self):
        """Recreate the database from scratch."""
        self._backup_corrupted_database()
        
        # Remove the corrupted database
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
                print(f"🗑️ Removed corrupted database: {self.db_path}")
            except Exception as e:
                print(f"❌ Failed to remove corrupted database: {e}")
                # Try to continue with a different path
                self.db_path = f"memory/jarvis_memory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                print(f"📁 Using alternative database path: {self.db_path}")
        
        # Reinitialize the database
        self._init_tables()
    
    def _init_tables(self):
        """Initialize database tables without error handling."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Table for storing facts with version history
        c.execute('''
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY,
                subject TEXT NOT NULL,
                attribute TEXT NOT NULL,
                value TEXT NOT NULL,
                valid_from DATETIME NOT NULL,
                valid_until DATETIME,
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT 'user_input',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add indexes for better performance
        c.execute('CREATE INDEX IF NOT EXISTS idx_facts_subject_attr ON facts(subject, attribute)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_facts_valid_from ON facts(valid_from)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_facts_valid_until ON facts(valid_until)')
        
        conn.commit()
        conn.close()
    
    def _init_database(self):
        """Initialize the database with corruption recovery."""
        try:
            # Check if database exists and is not corrupted
            if os.path.exists(self.db_path):
                if self._is_database_corrupted():
                    print("❌ Database is corrupted, recreating...")
                    self._recreate_database()
                else:
                    # Database exists and is healthy, just ensure tables exist
                    self._init_tables()
            else:
                # Database doesn't exist, create fresh
                self._init_tables()
                print(f"✅ Created new database: {self.db_path}")
                
        except Exception as e:
            print(f"❌ Critical error initializing database: {e}")
            self._recreate_database()
    
    def _execute_safe(self, query: str, params: tuple = None):
        """Execute SQL query with error handling and automatic recovery."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            if params:
                c.execute(query, params)
            else:
                c.execute(query)
                
            conn.commit()
            conn.close()
            return True
            
        except sqlite3.DatabaseError as e:
            print(f"❌ Database error: {e}. Attempting recovery...")
            self._recreate_database()
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def add_fact(self, subject: str, attribute: str, value: str, valid_from: datetime = None):
        """
        Add a new fact or update an existing one with versioning.
        """
        valid_from = valid_from or datetime.now()
        
        # First, invalidate any current fact for this subject+attribute
        self._execute_safe('''
            UPDATE facts SET valid_until = ?
            WHERE subject = ? AND attribute = ? AND valid_until IS NULL
        ''', (valid_from, subject, attribute))
        
        # Insert the new fact as current
        success = self._execute_safe('''
            INSERT INTO facts (subject, attribute, value, valid_from, valid_until)
            VALUES (?, ?, ?, ?, NULL)
        ''', (subject, attribute, value, valid_from))
        
        return success
    
    def get_current_fact(self, subject: str, attribute: str) -> Optional[Dict]:
        """Get the current value of a fact."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''
                SELECT value, valid_from 
                FROM facts 
                WHERE subject = ? AND attribute = ? AND valid_until IS NULL
                ORDER BY valid_from DESC LIMIT 1
            ''', (subject, attribute))
            
            result = c.fetchone()
            conn.close()
            
            if result:
                return {'value': result[0], 'valid_from': result[1]}
            return None
            
        except sqlite3.DatabaseError:
            print("❌ Database error in get_current_fact, recreating database...")
            self._recreate_database()
            return None
    
    def get_fact_history(self, subject: str, attribute: str) -> List[Dict]:
        """Get complete history of a fact with timestamps."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''
                SELECT value, valid_from, valid_until 
                FROM facts 
                WHERE subject = ? AND attribute = ?
                ORDER BY valid_from DESC
            ''', (subject, attribute))
            
            history = []
            for row in c.fetchall():
                history.append({
                    'value': row[0],
                    'valid_from': row[1],
                    'valid_until': row[2]
                })
            
            conn.close()
            return history
            
        except sqlite3.DatabaseError:
            print("❌ Database error in get_fact_history, recreating database...")
            self._recreate_database()
            return []
    
    def get_fact_at_time(self, subject: str, attribute: str, target_time: datetime) -> Optional[Dict]:
        """Get what a fact was at a specific point in time."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            c.execute('''
                SELECT value, valid_from, valid_until 
                FROM facts 
                WHERE subject = ? AND attribute = ? 
                AND valid_from <= ? AND (valid_until >= ? OR valid_until IS NULL)
                ORDER BY valid_from DESC LIMIT 1
            ''', (subject, attribute, target_time, target_time))
            
            result = c.fetchone()
            conn.close()
            
            if result:
                return {
                    'value': result[0],
                    'valid_from': result[1],
                    'valid_until': result[2]
                }
            return None
            
        except sqlite3.DatabaseError:
            print("❌ Database error in get_fact_at_time, recreating database...")
            self._recreate_database()
            return None

    def get_database_info(self) -> Dict:
        """Get information about the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Get number of facts
            c.execute('SELECT COUNT(*) FROM facts')
            total_facts = c.fetchone()[0]
            
            # Get number of current facts
            c.execute('SELECT COUNT(*) FROM facts WHERE valid_until IS NULL')
            current_facts = c.fetchone()[0]
            
            conn.close()
            
            return {
                'database_path': self.db_path,
                'total_facts': total_facts,
                'current_facts': current_facts,
                'database_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            }
            
        except Exception as e:
            return {
                'database_path': self.db_path,
                'error': str(e),
                'status': 'corrupted'
            }

# Global memory instance with error handling
try:
    long_term_memory = LongTermMemory()
    print("✅ Long-term memory initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize long-term memory: {e}")
    # Create a fallback instance with alternative path
    long_term_memory = LongTermMemory('memory/jarvis_memory_fallback.db')