"""
Configuration settings for PDD Trainer Bot MVP.
"""
import os

# Bot Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Data paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE_DIR, "pdd_questions.json")
IMAGES_DIR = os.path.join(BASE_DIR, "images")

# Bot settings
TOTAL_TICKETS = 40  # Total number of exam tickets
QUESTIONS_PER_TICKET = 20  # Standard number of questions per ticket

# Messages
MESSAGES = {
    "welcome": (
        "🚗 Добро пожаловать в PDD Trainer Bot!\n\n"
        "Этот бот поможет вам подготовиться к экзамену по ПДД.\n\n"
        "Выберите билет для начала тренировки:"
    ),
    "select_ticket": "Выберите билет:",
    "question_progress": "Вопрос {current} из {total}",
    "correct_answer": "Правильно! ✅",
    "incorrect_answer": "Неправильно! ❌",
    "results_header": "📊 Результаты билета {ticket}",
    "results_body": (
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Правильных ответов: {correct}\n"
        "❌ Неправильных ответов: {incorrect}\n"
        "📈 Результат: {percentage}%\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    ),
    "results_passed": "\n\n🎉 Поздравляем! Билет сдан!",
    "results_failed": "\n\n📚 Попробуйте ещё раз!",
    "choose_another": "📋 Выбрать другой билет",
    "ticket_not_found": "Билет не найден. Пожалуйста, выберите билет из списка.",
    "image_not_found": "🖼️ Изображение недоступно",
    "error_occurred": "Произошла ошибка. Пожалуйста, попробуйте снова или выберите другой билет.",
}

# Pass threshold (percentage)
PASS_THRESHOLD = 80
