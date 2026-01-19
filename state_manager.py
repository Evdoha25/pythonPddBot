"""
State Manager Module for PDD Trainer Bot.

This module handles in-memory session state management for users.
"""
import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class UserSession:
    """Represents a user's current session state."""
    user_id: int
    ticket_number: int
    current_question_index: int = 0
    score: int = 0
    questions: List[Dict[str, Any]] = field(default_factory=list)
    answers_history: List[bool] = field(default_factory=list)
    
    @property
    def total_questions(self) -> int:
        """Get total number of questions in current ticket."""
        return len(self.questions)
    
    @property
    def is_completed(self) -> bool:
        """Check if all questions have been answered."""
        return self.current_question_index >= self.total_questions
    
    @property
    def current_question(self) -> Optional[Dict[str, Any]]:
        """Get the current question."""
        if 0 <= self.current_question_index < self.total_questions:
            return self.questions[self.current_question_index]
        return None
    
    @property
    def progress_text(self) -> str:
        """Get progress indicator text (e.g., '1/20')."""
        return f"{self.current_question_index + 1}/{self.total_questions}"
    
    @property
    def incorrect_count(self) -> int:
        """Get number of incorrect answers."""
        return self.total_questions - self.score if self.is_completed else len(self.answers_history) - self.score
    
    @property
    def percentage(self) -> float:
        """Calculate success percentage."""
        if self.total_questions == 0:
            return 0.0
        answered = len(self.answers_history)
        if answered == 0:
            return 0.0
        return (self.score / answered) * 100
    
    def record_answer(self, is_correct: bool) -> None:
        """
        Record an answer and advance to next question.
        
        Args:
            is_correct: Whether the answer was correct.
        """
        self.answers_history.append(is_correct)
        if is_correct:
            self.score += 1
        self.current_question_index += 1
        logger.debug(
            f"User {self.user_id}: Question {self.current_question_index}/{self.total_questions}, "
            f"Score: {self.score}, Answer: {'Correct' if is_correct else 'Incorrect'}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary format."""
        return {
            'user_id': self.user_id,
            'ticket_number': self.ticket_number,
            'current_question_index': self.current_question_index,
            'score': self.score,
            'total_questions': self.total_questions,
            'is_completed': self.is_completed,
            'percentage': self.percentage,
        }


class StateManager:
    """Manages user sessions in memory."""
    
    def __init__(self):
        """Initialize the state manager."""
        self._sessions: Dict[int, UserSession] = {}
    
    def create_session(
        self,
        user_id: int,
        ticket_number: int,
        questions: List[Dict[str, Any]]
    ) -> UserSession:
        """
        Create a new session for a user.
        
        Args:
            user_id: The Telegram user ID.
            ticket_number: The selected ticket number.
            questions: List of question dictionaries for the ticket.
            
        Returns:
            The created UserSession.
        """
        session = UserSession(
            user_id=user_id,
            ticket_number=ticket_number,
            questions=questions.copy()  # Copy to avoid modification
        )
        self._sessions[user_id] = session
        logger.info(f"Created session for user {user_id}, ticket {ticket_number}")
        return session
    
    def get_session(self, user_id: int) -> Optional[UserSession]:
        """
        Get the current session for a user.
        
        Args:
            user_id: The Telegram user ID.
            
        Returns:
            The UserSession, or None if no session exists.
        """
        return self._sessions.get(user_id)
    
    def has_session(self, user_id: int) -> bool:
        """
        Check if a user has an active session.
        
        Args:
            user_id: The Telegram user ID.
            
        Returns:
            True if session exists, False otherwise.
        """
        return user_id in self._sessions
    
    def delete_session(self, user_id: int) -> bool:
        """
        Delete a user's session.
        
        Args:
            user_id: The Telegram user ID.
            
        Returns:
            True if session was deleted, False if no session existed.
        """
        if user_id in self._sessions:
            del self._sessions[user_id]
            logger.info(f"Deleted session for user {user_id}")
            return True
        return False
    
    def get_active_sessions_count(self) -> int:
        """
        Get the number of active sessions.
        
        Returns:
            Number of active user sessions.
        """
        return len(self._sessions)
    
    def clear_all_sessions(self) -> None:
        """Clear all sessions."""
        self._sessions.clear()
        logger.info("Cleared all user sessions")


# Singleton instance for global access
state_manager = StateManager()
