# PDD Trainer Bot

A Telegram bot for practicing Russian traffic rules exam tickets (ПДД).

## Features

- **Ticket Selection**: Choose from available exam tickets via reply keyboard
- **Interactive Questions**: Each question displays an image (if available), question text, and answer options as inline buttons
- **Instant Feedback**: Get immediate feedback (correct/incorrect) via pop-up alerts
- **Progress Tracking**: See your progress (e.g., "Question 1 of 20") with each question
- **Final Statistics**: View your results at the end of each ticket, including:
  - Total correct/incorrect answers
  - Success percentage
  - Pass/fail status (80% threshold)
- **Easy Navigation**: Restart with another ticket anytime

## Requirements

- Python 3.8+
- python-telegram-bot 20.x

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd pythonPddBot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the bot token:

Option A: Set environment variable:
```bash
export BOT_TOKEN="your_telegram_bot_token"
```

Option B: Edit `config.py` and replace `YOUR_BOT_TOKEN_HERE` with your token.

4. Add your question data:
   - Place your `pdd_questions.json` file in the root directory
   - Place question images in the `images/` folder

## Running the Bot

```bash
python bot.py
```

## Project Structure

```
pythonPddBot/
├── bot.py              # Main bot entry point with handlers
├── config.py           # Configuration settings
├── data_loader.py      # JSON data loading module
├── state_manager.py    # In-memory session management
├── pdd_questions.json  # Questions data file
├── images/             # Question images folder
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Data Format

The `pdd_questions.json` file should follow this structure:

```json
[
  {
    "ticketNumber": 1,
    "questions": [
      {
        "questionId": 1,
        "imageUrl": "images/ticket1_q1.jpg",
        "questionText": "Your question text here",
        "answers": [
          "Answer option 1",
          "Answer option 2",
          "Answer option 3"
        ],
        "correctAnswerIndex": 0
      }
    ]
  }
]
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `ticketNumber` | integer | Ticket identifier (1-40) |
| `questions` | array | Array of question objects |
| `questionId` | integer | Question number within ticket |
| `imageUrl` | string | Relative path to question image |
| `questionText` | string | The question text |
| `answers` | array | Array of answer strings |
| `correctAnswerIndex` | integer | Zero-based index of correct answer |

## User Flow

1. User starts bot with `/start`
2. Bot displays ticket selection keyboard
3. User selects a ticket (e.g., "Билет 1")
4. For each question:
   - Bot sends image + question text + answer buttons
   - User taps an answer
   - Bot shows "Correct ✅" or "Incorrect ❌" alert
   - Bot automatically shows next question
5. After last question, bot displays final statistics
6. User can choose another ticket to continue practicing

## Configuration

Edit `config.py` to customize:

- `BOT_TOKEN` - Your Telegram bot token
- `QUESTIONS_FILE` - Path to questions JSON file
- `IMAGES_DIR` - Path to images directory
- `PASS_THRESHOLD` - Passing score percentage (default: 80%)
- `MESSAGES` - All bot messages (for localization)

## Limitations (MVP)

- **No Persistence**: Progress is lost on bot restart
- **Linear Flow**: Cannot skip or revisit questions
- **Single Session**: One ticket at a time per user
- **No Explanations**: Only correct/incorrect feedback
- **No Analytics**: Statistics shown only at ticket end

## Creating a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the API token provided
5. Set the token as `BOT_TOKEN`

## License

This project is provided for educational purposes.

## Support

For issues or questions, please open an issue in the repository.
