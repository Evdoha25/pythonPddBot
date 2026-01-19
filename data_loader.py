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
            logger.info(f"Attempting to load questions from: {self.questions_file}")
            
            with open(self.questions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"JSON loaded, type: {type(data)}, length: {len(data) if isinstance(data, list) else 'N/A'}")
            
            # Handle both list format and dict format
            if isinstance(data, dict):
                # If it's a dict, it might have a 'tickets' key or be a single ticket
                if 'tickets' in data:
                    data = data['tickets']
                elif 'ticketNumber' in data:
                    data = [data]
                else:
                    logger.error(f"Unknown JSON structure. Keys: {list(data.keys())}")
                    return False
            
            if not isinstance(data, list):
                logger.error(f"Expected list of tickets, got: {type(data)}")
                return False
            
            self._tickets = {}
            for idx, ticket in enumerate(data):
                logger.debug(f"Processing ticket {idx}: {type(ticket)}")
                
                if not isinstance(ticket, dict):
                    logger.warning(f"Ticket {idx} is not a dict, skipping")
                    continue
                
                ticket_number = ticket.get('ticketNumber')
                questions = ticket.get('questions', [])
                
                logger.debug(f"Ticket {idx}: ticketNumber={ticket_number}, questions count={len(questions)}")
                
                if ticket_number is not None and questions:
                    self._tickets[ticket_number] = questions
                    logger.info(f"Loaded ticket {ticket_number} with {len(questions)} questions")
                else:
                    logger.warning(f"Ticket {idx} skipped: ticketNumber={ticket_number}, questions={len(questions)}")
            
            self._loaded = True
            logger.info(f"Successfully loaded {len(self._tickets)} tickets")
            
            if len(self._tickets) == 0:
                logger.warning("No tickets were loaded! Check your pdd_questions.json file structure.")
                logger.warning("Expected format: [{\"ticketNumber\": 1, \"questions\": [...]}]")
            
            return True
            
        except FileNotFoundError:
            logger.error(f"Questions file not found: {self.questions_file}")
            logger.error("Make sure pdd_questions.json exists in the same directory as bot.py")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in questions file: {e}")
            logger.error("Check that pdd_questions.json contains valid JSON")
            return False
        except Exception as e:
            logger.error(f"Error loading questions: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
