# brain/memory_orchestrator.py
from memory.long_term import long_term_memory, MemoryCategory
from openai import OpenAI
from config.settings import settings
import json
import re
from datetime import datetime

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class MemoryOrchestrator:
    def __init__(self):
        self.min_confidence_threshold = 0.7
    
    def analyze_conversation(self, user_input: str, ai_response: str) -> dict:
        """
        Uses LLM to analyze conversation for memory-worthy information.
        """
        try:
            prompt = f"""
            Analyze this conversation and identify information worth storing in long-term memory.
            
            USER: {user_input}
            AI: {ai_response}
            
            Respond with JSON containing:
            - should_remember: boolean
            - facts: array of facts to store [{{"subject", "attribute", "value", "category", "confidence", "metadata"}}]
            - clarification_questions: array of questions if information is unclear
            - summary: brief summary of what to remember
            
            Categories: personal, work, preference, medical, contact, financial, other
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" },
                temperature=0.1
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Memory analysis error: {e}")
            return {"should_remember": False, "facts": []}
    
    def extract_and_store_memory(self, user_input: str, ai_response: str) -> dict:
        """
        Main function to extract and store memories from conversation.
        """
        analysis = self.analyze_conversation(user_input, ai_response)
        
        if not analysis.get('should_remember', False):
            return {"stored_count": 0, "needs_clarification": False}
        
        stored_count = 0
        for fact in analysis.get('facts', []):
            try:
                long_term_memory.add_fact(
                    subject=fact.get('subject', 'user'),
                    attribute=fact.get('attribute', ''),
                    value=fact.get('value', ''),
                    category=fact.get('category', 'personal'),
                    confidence=fact.get('confidence', 0.8),
                    source='auto_detection',
                    metadata=fact.get('metadata', {})
                )
                stored_count += 1
            except Exception as e:
                print(f"Error storing fact: {e}")
        
        return {
            "stored_count": stored_count,
            "needs_clarification": len(analysis.get('clarification_questions', [])) > 0,
            "clarification_questions": analysis.get('clarification_questions', []),
            "summary": analysis.get('summary', '')
        }
    
    def get_memory_context(self, user_input: str) -> str:
        """
        Retrieves relevant memories for context in responses.
        """
        try:
            # Analyze query to understand what memories might be relevant
            prompt = f"""
            Analyze this user query to identify what types of memories might be relevant for responding.
            
            USER QUERY: {user_input}
            
            Return JSON with:
            - relevant_categories: array of relevant categories
            - potential_attributes: array of attribute names that might be relevant
            - query_type: type of query (recall, update, verify, etc.)
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" },
                temperature=0.1
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            # Retrieve relevant facts based on analysis
            relevant_facts = []
            if analysis.get('relevant_categories'):
                for category in analysis['relevant_categories']:
                    facts = long_term_memory.get_related_facts('user', category)
                    relevant_facts.extend(facts)
            
            return json.dumps({
                "relevant_facts": relevant_facts[:5],  # Limit to 5 most relevant
                "query_analysis": analysis
            })
            
        except Exception as e:
            print(f"Memory context error: {e}")
            return "{}"

# Global orchestrator instance
memory_orchestrator = MemoryOrchestrator()