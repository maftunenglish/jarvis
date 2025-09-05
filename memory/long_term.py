# memory/long_term.py
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import os

class LongTermMemory:
    def __init__(self, db_path: str = 'memory/jarvis_memory.db'):
        # Ensure the memory directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables."""
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
        
        conn.commit()
        conn.close()
    
    def add_fact(self, subject: str, attribute: str, value: str, valid_from: datetime = None):
        """
        Add a new fact or update an existing one with versioning.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        valid_from = valid_from or datetime.now()
        
        # First, invalidate any current fact for this subject+attribute
        c.execute('''
            UPDATE facts SET valid_until = ?
            WHERE subject = ? AND attribute = ? AND valid_until IS NULL
        ''', (valid_from, subject, attribute))
        
        # Insert the new fact as current
        c.execute('''
            INSERT INTO facts (subject, attribute, value, valid_from, valid_until)
            VALUES (?, ?, ?, ?, NULL)
        ''', (subject, attribute, value, valid_from))
        
        conn.commit()
        conn.close()
        return True
    
    def get_current_fact(self, subject: str, attribute: str) -> Optional[Dict]:
        """Get the current value of a fact."""
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
    
    def get_fact_history(self, subject: str, attribute: str) -> List[Dict]:
        """Get complete history of a fact with timestamps."""
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
    
    def get_fact_at_time(self, subject: str, attribute: str, target_time: datetime) -> Optional[Dict]:
        """Get what a fact was at a specific point in time."""
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

# Global memory instance
long_term_memory = LongTermMemory()