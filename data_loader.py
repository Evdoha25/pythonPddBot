"""
Data Loader Module for PDD Trainer Bot.

This module handles loading and parsing questions from the JSON file.
"""
import json
import logging
from typing import Dict, List, Optional, Any

from config import QUESTIONS_FILE, IMAGES_DIR

logger = logging.getLogger(__name__)


class DataLoader:
    """Handles loading and organizing PDD questions from JSON file."""
    
    def __init__(self, questions_file: str = QUESTIONS_FILE):
        """
        Initialize the DataLoader.
        
        Args:
            questions_file: Path to the JSON file containing questions.
        """
        self.questions_file = questions_file
        self._tickets: Dict[int, List[Dict[str, Any]]] = {}
        self._loaded = False
    
    def load_questions(self) -> bool:
        """
        Load questions from the JSON file.
        
        Returns:
            True if loading was successful, False otherwise.
        """
        try:
            import os
            
            print(f"\n[DataLoader] Loading questions from: {self.questions_file}")
            print(f"[DataLoader] File exists: {os.path.exists(self.questions_file)}")
            
            if not os.path.exists(self.questions_file):
                print(f"[DataLoader] ERROR: File not found!")
                print(f"[DataLoader] Current directory: {os.getcwd()}")
                print(f"[DataLoader] Files in current dir: {os.listdir('.')}")
                return False
            
            # Read file content first to debug
            with open(self.questions_file, 'r', encoding='utf-8-sig') as f:
                raw_content = f.read()
            
            print(f"[DataLoader] File size: {len(raw_content)} bytes")
            
            # Show first 200 chars for debugging
            preview = raw_content[:200].replace('\n', '\\n')
            print(f"[DataLoader] File preview: {preview}...")
            
            if not raw_content.strip():
                print("[DataLoader] ERROR: File is empty!")
                return False
            
            # Parse JSON
            data = json.loads(raw_content)
            
            print(f"[DataLoader] JSON type: {type(data).__name__}")
            if isinstance(data, list):
                print(f"[DataLoader] JSON is a list with {len(data)} items")
            elif isinstance(data, dict):
                print(f"[DataLoader] JSON is a dict with keys: {list(data.keys())}")
            
            # Handle both list format and dict format
            if isinstance(data, dict):
                # If it's a dict, it might have a 'tickets' key or be a single ticket
                if 'tickets' in data:
                    data = data['tickets']
                    print(f"[DataLoader] Extracted 'tickets' key, now have {len(data)} items")
                elif 'ticketNumber' in data:
                    data = [data]
                    print("[DataLoader] Wrapped single ticket in list")
                else:
                    print(f"[DataLoader] ERROR: Unknown JSON structure. Keys: {list(data.keys())}")
                    print("[DataLoader] Expected 'tickets' or 'ticketNumber' key")
                    return False
            
            if not isinstance(data, list):
                print(f"[DataLoader] ERROR: Expected list of tickets, got: {type(data)}")
                return False
            
            self._tickets = {}
            for idx, ticket in enumerate(data):
                if not isinstance(ticket, dict):
                    print(f"[DataLoader] WARNING: Item {idx} is {type(ticket).__name__}, not dict - skipping")
                    continue
                
                # Try different key names for ticket number
                ticket_number = ticket.get('ticketNumber') or ticket.get('ticket_number') or ticket.get('id')
                questions = ticket.get('questions', [])
                
                print(f"[DataLoader] Ticket {idx}: number={ticket_number}, questions={len(questions)}, keys={list(ticket.keys())}")
                
                if ticket_number is not None and questions:
                    self._tickets[int(ticket_number)] = questions
                    print(f"[DataLoader] ✓ Loaded ticket {ticket_number} with {len(questions)} questions")
                else:
                    print(f"[DataLoader] ✗ Skipped ticket {idx}: number={ticket_number}, questions={len(questions)}")
            
            self._loaded = True
            print(f"\n[DataLoader] === RESULT: Loaded {len(self._tickets)} tickets ===")
            
            if len(self._tickets) == 0:
                print("[DataLoader] WARNING: No tickets were loaded!")
                print("[DataLoader] Expected JSON format:")
                print('[{"ticketNumber": 1, "questions": [{"questionText": "...", "answers": [...], "correctAnswerIndex": 0}]}]')
            else:
                print(f"[DataLoader] Available ticket numbers: {sorted(self._tickets.keys())}")
            
            logger.info(f"Successfully loaded {len(self._tickets)} tickets")
            return True
            
        except FileNotFoundError:
            print(f"[DataLoader] ERROR: File not found: {self.questions_file}")
            logger.error(f"Questions file not found: {self.questions_file}")
            return False
        except json.JSONDecodeError as e:
            print(f"[DataLoader] ERROR: Invalid JSON: {e}")
            logger.error(f"Invalid JSON in questions file: {e}")
            return False
        except Exception as e:
            print(f"[DataLoader] ERROR: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Error loading questions: {e}")
            return False
    
    def get_available_tickets(self) -> List[int]:
        """
        Get list of available ticket numbers.
        
        Returns:
            Sorted list of ticket numbers.
        """
        return sorted(self._tickets.keys())
    
    def get_ticket_questions(self, ticket_number: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get questions for a specific ticket.
        
        Args:
            ticket_number: The ticket number to retrieve.
            
        Returns:
            List of question dictionaries, or None if ticket not found.
        """
        return self._tickets.get(ticket_number)
    
    def get_total_tickets(self) -> int:
        """
        Get total number of loaded tickets.
        
        Returns:
            Number of tickets.
        """
        return len(self._tickets)
    
    def is_loaded(self) -> bool:
        """
        Check if data has been loaded.
        
        Returns:
            True if data is loaded, False otherwise.
        """
        return self._loaded
    
    def get_question(self, ticket_number: int, question_index: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific question from a ticket.
        
        Args:
            ticket_number: The ticket number.
            question_index: Zero-based index of the question.
            
        Returns:
            Question dictionary, or None if not found.
        """
        questions = self.get_ticket_questions(ticket_number)
        if questions and 0 <= question_index < len(questions):
            return questions[question_index]
        return None
    
    def validate_answer(self, ticket_number: int, question_index: int, answer_index: int) -> Optional[bool]:
        """
        Validate if the given answer is correct.
        
        Args:
            ticket_number: The ticket number.
            question_index: Zero-based index of the question.
            answer_index: Index of the selected answer.
            
        Returns:
            True if correct, False if incorrect, None if question not found.
        """
        question = self.get_question(ticket_number, question_index)
        if question is None:
            return None
        
        correct_index = question.get('correctAnswerIndex')
        return answer_index == correct_index


# Singleton instance for global access
data_loader = DataLoader()


def initialize_data() -> bool:
    """
    Initialize the data loader. Call this at bot startup.
    
    Returns:
        True if initialization was successful.
    """
    return data_loader.load_questions()
