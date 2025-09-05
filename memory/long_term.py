# memory/long_term.py
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import os
from enum import Enum

class MemoryCategory(Enum):
    PERSONAL = "personal"
    WORK = "work"
    PREFERENCE = "preference"
    MEDICAL = "medical"
    CONTACT = "contact"
    FINANCIAL = "financial"
    OTHER = "other"

class LongTermMemory:
    def __init__(self, db_path: str = 'memory/jarvis_memory.db'):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with enhanced tables."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Enhanced facts table with categories and confidence
        c.execute('''
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY,
                subject TEXT NOT NULL,
                attribute TEXT NOT NULL,
                value TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'personal',
                confidence REAL DEFAULT 0.8,
                source TEXT DEFAULT 'user_input',
                valid_from DATETIME NOT NULL,
                valid_until DATETIME,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Memory access statistics
        c.execute('''
            CREATE TABLE IF NOT EXISTS memory_access (
                id INTEGER PRIMARY KEY,
                fact_id INTEGER,
                access_type TEXT,
                accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fact_id) REFERENCES facts (id)
            )
        ''')
        
        # Create indexes
        c.execute('CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_facts_confidence ON facts(confidence)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_facts_subject_attr ON facts(subject, attribute)')
        
        conn.commit()
        conn.close()
    
    def add_fact(self, subject: str, attribute: str, value: Any, 
                 category: str = "personal", confidence: float = 0.9, 
                 source: str = "user_input", metadata: dict = None):
        """
        Enhanced fact storage with categories and confidence scoring.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        valid_from = datetime.now()
        metadata_str = json.dumps(metadata) if metadata else None
        
        # Invalidate previous fact if it exists
        c.execute('''
            UPDATE facts SET valid_until = ?, updated_at = CURRENT_TIMESTAMP
            WHERE subject = ? AND attribute = ? AND valid_until IS NULL
        ''', (valid_from, subject, attribute))
        
        # Insert new fact
        c.execute('''
            INSERT INTO facts (subject, attribute, value, category, 
                             confidence, source, valid_from, valid_until, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?)
        ''', (subject, attribute, str(value), category, confidence, 
              source, valid_from, metadata_str))
        
        conn.commit()
        conn.close()
        return True
    
    def get_memory_summary(self, subject: str = "user") -> Dict:
        """Get summary of what we know about a subject."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT category, COUNT(*) as count, 
                   AVG(confidence) as avg_confidence
            FROM facts 
            WHERE subject = ? AND valid_until IS NULL
            GROUP BY category
        ''', (subject,))
        
        summary = {}
        for row in c.fetchall():
            summary[row[0]] = {
                'count': row[1],
                'avg_confidence': round(row[2], 2)
            }
        
        conn.close()
        return summary
    
    def get_related_facts(self, subject: str, attribute: str) -> List[Dict]:
        """Get facts related to a specific attribute."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            SELECT attribute, value, confidence, category
            FROM facts 
            WHERE subject = ? AND valid_until IS NULL
            ORDER BY confidence DESC, updated_at DESC
        ''', (subject,))
        
        related = []
        for row in c.fetchall():
            related.append({
                'attribute': row[0],
                'value': row[1],
                'confidence': row[2],
                'category': row[3]
            })
        
        conn.close()
        return related

# Global memory instance
long_term_memory = LongTermMemory()