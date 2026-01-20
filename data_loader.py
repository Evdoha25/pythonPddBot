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
        
        Supports two formats:
        1. Grouped format: [{"ticketNumber": 1, "questions": [...]}]
        2. Flat format: [{"ticketNumber": 1, "questionNumber": 1, "text": "...", "options": [...]}]
        
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
            
            # Show first 300 chars for debugging
            preview = raw_content[:300].replace('\n', '\\n')
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
            
            # Handle dict wrapper
            if isinstance(data, dict):
                if 'tickets' in data:
                    data = data['tickets']
                elif 'questions' in data:
                    data = data['questions']
                else:
                    print(f"[DataLoader] ERROR: Unknown dict structure. Keys: {list(data.keys())}")
                    return False
            
            if not isinstance(data, list) or len(data) == 0:
                print(f"[DataLoader] ERROR: Expected non-empty list, got: {type(data)}")
                return False
            
            # Detect format by checking the first item
            first_item = data[0]
            if not isinstance(first_item, dict):
                print(f"[DataLoader] ERROR: First item is not a dict: {type(first_item)}")
                return False
            
            print(f"[DataLoader] First item keys: {list(first_item.keys())}")
            
            # Check if it's FLAT format (each item is a question with ticketNumber)
            # or GROUPED format (each item is a ticket with questions array)
            is_flat_format = 'questions' not in first_item and 'ticketNumber' in first_item
            
            if is_flat_format:
                print("[DataLoader] Detected FLAT format (questions with ticketNumber field)")
                self._tickets = self._load_flat_format(data)
            else:
                print("[DataLoader] Detected GROUPED format (tickets with questions array)")
                self._tickets = self._load_grouped_format(data)
            
            self._loaded = True
            print(f"\n[DataLoader] === RESULT: Loaded {len(self._tickets)} tickets ===")
            
            if len(self._tickets) == 0:
                print("[DataLoader] WARNING: No tickets were loaded!")
            else:
                print(f"[DataLoader] Available ticket numbers: {sorted(self._tickets.keys())}")
                # Show question counts
                for t_num in sorted(self._tickets.keys())[:5]:
                    print(f"[DataLoader]   Ticket {t_num}: {len(self._tickets[t_num])} questions")
                if len(self._tickets) > 5:
                    print(f"[DataLoader]   ... and {len(self._tickets) - 5} more tickets")
            
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
    
    def _normalize_question(self, q: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize question to standard format.
        
        Handles different field names:
        - text/questionText -> questionText
        - options/answers -> answers
        """
        return {
            'questionId': q.get('questionId') or q.get('questionNumber') or q.get('id'),
            'questionText': q.get('text') or q.get('questionText') or q.get('question', ''),
            'answers': q.get('options') or q.get('answers') or [],
            'correctAnswerIndex': q.get('correctAnswerIndex', 0),
            'imageUrl': q.get('imageUrl') or q.get('image') or q.get('img', ''),
        }
    
    def _load_flat_format(self, data: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
        """
        Load flat format where each item is a question with ticketNumber field.
        
        Format: [{"ticketNumber": 1, "text": "...", "options": [...]}]
        """
        tickets: Dict[int, List[Dict[str, Any]]] = {}
        
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                print(f"[DataLoader] WARNING: Item {idx} is not a dict, skipping")
                continue
            
            # Get ticket number
            ticket_number = item.get('ticketNumber') or item.get('ticket_number') or item.get('ticket')
            
            if ticket_number is None:
                print(f"[DataLoader] WARNING: Item {idx} has no ticketNumber, skipping")
                continue
            
            ticket_number = int(ticket_number)
            
            # Normalize the question
            normalized = self._normalize_question(item)
            
            # Add to tickets dict
            if ticket_number not in tickets:
                tickets[ticket_number] = []
            
            tickets[ticket_number].append(normalized)
        
        # Sort questions within each ticket by questionNumber if available
        for ticket_num in tickets:
            tickets[ticket_num].sort(key=lambda q: q.get('questionId', 0) if isinstance(q.get('questionId'), int) else 0)
        
        print(f"[DataLoader] Grouped {len(data)} questions into {len(tickets)} tickets")
        return tickets
    
    def _load_grouped_format(self, data: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
        """
        Load grouped format where each item is a ticket with questions array.
        
        Format: [{"ticketNumber": 1, "questions": [...]}]
        """
        tickets: Dict[int, List[Dict[str, Any]]] = {}
        
        for idx, ticket in enumerate(data):
            if not isinstance(ticket, dict):
                print(f"[DataLoader] WARNING: Item {idx} is not a dict, skipping")
                continue
            
            # Get ticket number
            ticket_number = ticket.get('ticketNumber') or ticket.get('ticket_number') or ticket.get('id')
            questions = ticket.get('questions', [])
            
            if ticket_number is None:
                print(f"[DataLoader] WARNING: Ticket {idx} has no ticketNumber, skipping")
                continue
            
            if not questions:
                print(f"[DataLoader] WARNING: Ticket {ticket_number} has no questions, skipping")
                continue
            
            ticket_number = int(ticket_number)
            
            # Normalize all questions
            normalized_questions = [self._normalize_question(q) for q in questions]
            
            tickets[ticket_number] = normalized_questions
            print(f"[DataLoader] ✓ Loaded ticket {ticket_number} with {len(normalized_questions)} questions")
        
        return tickets
    
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
