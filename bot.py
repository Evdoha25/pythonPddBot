"""
PDD Trainer Bot - Main Bot Module.

A Telegram bot for practicing Russian traffic rules exam tickets.
"""
import logging
import os
from typing import List

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config import (
    BOT_TOKEN,
    IMAGES_DIR,
    MESSAGES,
    PASS_THRESHOLD,
)
from data_loader import data_loader, initialize_data
from state_manager import state_manager, UserSession

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_ticket_keyboard() -> ReplyKeyboardMarkup:
    """
    Create a reply keyboard with available ticket buttons.
    
    Returns:
        ReplyKeyboardMarkup with ticket selection buttons.
    """
    tickets = data_loader.get_available_tickets()
    
    # Handle case when no tickets are loaded
    if not tickets:
        logger.warning("No tickets available for keyboard")
        return ReplyKeyboardMarkup(
            [["Нет доступных билетов"]],
            resize_keyboard=True,
            one_time_keyboard=False
        )
    
    # Create rows of 5 buttons each
    rows: List[List[str]] = []
    current_row: List[str] = []
    
    for ticket_num in tickets:
        current_row.append(f"Билет {ticket_num}")
        if len(current_row) == 5:
            rows.append(current_row)
            current_row = []
    
    # Add remaining buttons
    if current_row:
        rows.append(current_row)
    
    return ReplyKeyboardMarkup(
        rows,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_answer_keyboard(question: dict, ticket_number: int, question_index: int) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard with answer options.
    
    Args:
        question: The question dictionary.
        ticket_number: Current ticket number.
        question_index: Current question index.
        
    Returns:
        InlineKeyboardMarkup with answer buttons.
    """
    answers = question.get('answers', [])
    buttons = []
    
    for idx, answer in enumerate(answers):
        # Callback data format: answer_{ticket}_{question_idx}_{answer_idx}
        callback_data = f"answer_{ticket_number}_{question_index}_{idx}"
        buttons.append([InlineKeyboardButton(answer, callback_data=callback_data)])
    
    return InlineKeyboardMarkup(buttons)


def get_restart_keyboard() -> InlineKeyboardMarkup:
    """
    Create an inline keyboard with restart button.
    
    Returns:
        InlineKeyboardMarkup with restart button.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(MESSAGES["choose_another"], callback_data="restart")]
    ])


async def send_question(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: UserSession
) -> None:
    """
    Send the current question to the user.
    
    Args:
        update: The Telegram update.
        context: The callback context.
        session: The user's session.
    """
    question = session.current_question
    if question is None:
        logger.error(f"No current question for user {session.user_id}")
        return
    
    # Build the message text
    progress = f"❓ {MESSAGES['question_progress'].format(current=session.current_question_index + 1, total=session.total_questions)}\n\n"
    question_text = question.get('questionText', 'Вопрос недоступен')
    message_text = f"{progress}{question_text}"
    
    # Get the answer keyboard
    keyboard = get_answer_keyboard(question, session.ticket_number, session.current_question_index)
    
    # Try to send with image
    image_path = question.get('imageUrl', '')
    full_image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), image_path)
    
    chat_id = update.effective_chat.id
    
    if image_path and os.path.exists(full_image_path):
        try:
            with open(full_image_path, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=InputFile(photo),
                    caption=message_text,
                    reply_markup=keyboard
                )
            return
        except Exception as e:
            logger.warning(f"Failed to send image {image_path}: {e}")
    
    # Send without image (or if image failed)
    # Include a note about missing image if it was expected
    if image_path:
        message_text = f"{MESSAGES['image_not_found']}\n\n{message_text}"
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=message_text,
        reply_markup=keyboard
    )


async def send_results(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session: UserSession
) -> None:
    """
    Send the final results to the user.
    
    Args:
        update: The Telegram update.
        context: The callback context.
        session: The user's session.
    """
    percentage = round(session.percentage)
    passed = percentage >= PASS_THRESHOLD
    
    # Build results message
    results_header = MESSAGES["results_header"].format(ticket=session.ticket_number)
    results_body = MESSAGES["results_body"].format(
        correct=session.score,
        incorrect=session.incorrect_count,
        percentage=percentage
    )
    
    status = MESSAGES["results_passed"] if passed else MESSAGES["results_failed"]
    
    message = f"{results_header}\n{results_body}{status}"
    
    keyboard = get_restart_keyboard()
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=keyboard
    )
    
    # Clean up the session
    state_manager.delete_session(session.user_id)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /start command.
    
    Args:
        update: The Telegram update.
        context: The callback context.
    """
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot")
    
    # Clear any existing session
    state_manager.delete_session(user.id)
    
    # Send welcome message with ticket keyboard
    keyboard = get_ticket_keyboard()
    await update.message.reply_text(
        MESSAGES["welcome"],
        reply_markup=keyboard
    )


async def ticket_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle ticket selection from reply keyboard.
    
    Args:
        update: The Telegram update.
        context: The callback context.
    """
    user = update.effective_user
    text = update.message.text
    
    # Parse ticket number from message
    if not text.startswith("Билет "):
        # Not a ticket selection, ignore
        return
    
    try:
        ticket_number = int(text.replace("Билет ", "").strip())
    except ValueError:
        await update.message.reply_text(MESSAGES["ticket_not_found"])
        return
    
    # Get questions for the ticket
    questions = data_loader.get_ticket_questions(ticket_number)
    if questions is None:
        await update.message.reply_text(MESSAGES["ticket_not_found"])
        return
    
    logger.info(f"User {user.id} selected ticket {ticket_number}")
    
    # Create a new session
    session = state_manager.create_session(
        user_id=user.id,
        ticket_number=ticket_number,
        questions=questions
    )
    
    # Send the first question
    await send_question(update, context, session)


async def answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle answer selection from inline keyboard.
    
    Args:
        update: The Telegram update.
        context: The callback context.
    """
    query = update.callback_query
    user = query.from_user
    
    # Handle restart button
    if query.data == "restart":
        await query.answer()
        # Clear session and show ticket selection
        state_manager.delete_session(user.id)
        keyboard = get_ticket_keyboard()
        await query.message.reply_text(
            MESSAGES["select_ticket"],
            reply_markup=keyboard
        )
        return
    
    # Parse callback data: answer_{ticket}_{question_idx}_{answer_idx}
    try:
        parts = query.data.split("_")
        if parts[0] != "answer" or len(parts) != 4:
            await query.answer("Ошибка обработки ответа")
            return
        
        ticket_number = int(parts[1])
        question_index = int(parts[2])
        answer_index = int(parts[3])
    except (ValueError, IndexError):
        await query.answer("Ошибка обработки ответа")
        return
    
    # Get user session
    session = state_manager.get_session(user.id)
    if session is None:
        await query.answer("Сессия не найдена. Начните заново с /start")
        return
    
    # Validate that we're on the right question
    if session.ticket_number != ticket_number or session.current_question_index != question_index:
        await query.answer("Этот вопрос уже был отвечен")
        return
    
    # Check if the answer is correct
    is_correct = data_loader.validate_answer(ticket_number, question_index, answer_index)
    if is_correct is None:
        await query.answer("Ошибка проверки ответа")
        return
    
    # Show feedback via popup
    feedback = MESSAGES["correct_answer"] if is_correct else MESSAGES["incorrect_answer"]
    await query.answer(feedback, show_alert=True)
    
    # Get the current question to show selected answer
    question = session.current_question
    selected_answer = question['answers'][answer_index] if question and answer_index < len(question.get('answers', [])) else "?"
    
    # Remove inline keyboard and update message to show the answer result
    result_icon = "✅" if is_correct else "❌"
    
    try:
        # Try to edit the message to remove buttons and show result
        if query.message.caption:
            # Message with photo (has caption)
            new_caption = f"{query.message.caption}\n\n{result_icon} Ваш ответ: {selected_answer}"
            await query.message.edit_caption(
                caption=new_caption,
                reply_markup=None  # Remove inline keyboard
            )
        else:
            # Text-only message
            new_text = f"{query.message.text}\n\n{result_icon} Ваш ответ: {selected_answer}"
            await query.message.edit_text(
                text=new_text,
                reply_markup=None  # Remove inline keyboard
            )
    except Exception as e:
        # If editing fails, just log it and continue
        logger.warning(f"Failed to edit message: {e}")
    
    # Record the answer
    session.record_answer(is_correct)
    
    # Check if ticket is completed
    if session.is_completed:
        await send_results(update, context, session)
    else:
        # Send next question
        await send_question(update, context, session)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle errors in the bot.
    
    Args:
        update: The Telegram update.
        context: The callback context.
    """
    logger.error(f"Update {update} caused error {context.error}")
    
    try:
        if update and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=MESSAGES["error_occurred"]
            )
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")


def main() -> None:
    """Start the bot."""
    import sys
    
    print("=" * 50)
    print("PDD Trainer Bot - Starting...")
    print("=" * 50)
    
    # Validate bot token
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        logger.error("Bot token not configured. Set the BOT_TOKEN environment variable.")
        print("\nError: Bot token not configured.")
        print("Set the BOT_TOKEN environment variable or update config.py")
        print("\nExample:")
        print("  Windows: set BOT_TOKEN=your_token_here")
        print("  Linux/Mac: export BOT_TOKEN=your_token_here")
        return
    
    # Show Python version for debugging
    print(f"\nPython version: {sys.version}")
    
    # Initialize data
    print(f"\nLoading questions from: {data_loader.questions_file}")
    
    if not initialize_data():
        logger.error("Failed to initialize data.")
        print("\nError: Failed to load questions data.")
        print("Make sure pdd_questions.json exists and contains valid data.")
        print("\nExpected JSON format:")
        print('[{"ticketNumber": 1, "questions": [...]}]')
        return
    
    ticket_count = data_loader.get_total_tickets()
    logger.info(f"Loaded {ticket_count} tickets")
    
    if ticket_count == 0:
        print("\nWarning: No tickets were loaded!")
        print("Check that pdd_questions.json has the correct format.")
        print("The bot will start but won't have any questions to display.")
    else:
        print(f"\nSuccessfully loaded {ticket_count} tickets")
        print(f"Available tickets: {data_loader.get_available_tickets()}")
    
    # Create the Application
    print("\nInitializing Telegram bot...")
    try:
        application = Application.builder().token(BOT_TOKEN).build()
    except Exception as e:
        logger.error(f"Failed to create bot application: {e}")
        print(f"\nError creating bot: {e}")
        print("\nIf you're using Python 3.14, try downgrading to Python 3.12 or 3.13")
        print("Or update python-telegram-bot: pip install --upgrade python-telegram-bot")
        return
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        ticket_selection_handler
    ))
    application.add_handler(CallbackQueryHandler(answer_handler))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    print("\n" + "=" * 50)
    print("Bot is running! Press Ctrl+C to stop")
    print("=" * 50)
    logger.info("Starting PDD Trainer Bot polling...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
