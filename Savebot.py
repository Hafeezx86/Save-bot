import os
import telebot
import sqlite3

API_KEY = '8740278653:AAHDTBKggYUTjE9rwTZS6ppLG99v4nbqZQk'
bot = telebot.TeleBot(API_KEY)

#--Database Setup--
DB_PATH = 'savebot.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS savings (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            total_saved REAL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

#--Handlers--

@bot.message_handler(commands=['register'])
def handle_register(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM savings WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()

    if row is not None:
        bot.reply_to(message, "You already have an account! Use /save <amount> to keep saving.")
        conn.close()
        return

    cursor.execute(
        'INSERT INTO savings (user_id, username, total_saved) VALUES (?, ?, 0)',
        (user_id, username)
    )
    conn.commit()
    conn.close()

    bot.reply_to(message, f"✅ Account created, {username}! Use /save <amount> to log your first deposit.")

@bot.message_handler(commands=['start'])
def handle_start(message):
    welcome_text = (
        "👋 Welcome to *SaveBot*!\n\n"
        "I help you track your personal savings. Here's what I can do:\n\n"
        "🆕 /register — create your savings account\n"
        "💰 /save <amount> — log a deposit (e.g. `/save 50`)\n"
        "📊 /balance — check your total savings\n"
        "👋 /greet — say hi to me\n\n"
        "🗑️ /delete_account - delete your savings account\n"
        "Let's get started — try /register to set up your account!"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['greet'])
def handle_greet(message):
    bot.reply_to(message, "Hey! It's SaveBot.")

@bot.message_handler(commands=['hello'])
def handle_hello(message):
    bot.send_message(message.chat.id, "Hello")

@bot.message_handler(commands=['save'])
def handle_save(message):
    user_id = message.from_user.id

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT total_saved FROM savings WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()

    if row is None:
        bot.reply_to(message, "You don't have an account yet. Use /register to create one first.")
        conn.close()
        return

    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "Usage: /save <amount>\nExample: /save 50")
        conn.close()
        return

    try:
        amount = float(parts[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        bot.reply_to(message, "Please enter a valid positive number. Example: /save 50")
        conn.close()
        return

    new_total = row[0] + amount
    cursor.execute('UPDATE savings SET total_saved = ? WHERE user_id = ?', (new_total, user_id))
    conn.commit()
    conn.close()

    bot.reply_to(message, f"Saved GHS {amount:.2f}. Your total savings: GHS {new_total:.2f}")

@bot.message_handler(commands=['balance'])
def handle_balance(message):
    user_id = message.from_user.id

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT total_saved FROM savings WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        bot.reply_to(message, "You don't have an account yet. Use /register to create one first.")
        return

    bot.reply_to(message, f"Your total savings: GHS {row[0]:.2f}")

@bot.message_handler(commands=['delete_account'])
def handle_delete_account(message):
    user_id = message.from_user.id

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT total_saved FROM savings WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()

    if row is None:
        bot.reply_to(message, "You don't have an account to delete.")
        conn.close()
        return

    parts = message.text.split()

    # Require explicit confirmation: /delete_account confirm
    if len(parts) != 2 or parts[1].lower() != 'confirm':
        bot.reply_to(
            message,
            f"⚠️ This will permanently delete your account and erase your savings record "
            f"(current balance: GHS {row[0]:.2f}).\n\n"
            f"This cannot be undone. To confirm, send:\n`/delete_account confirm`",
            parse_mode="Markdown"
        )
        conn.close()
        return

    cursor.execute('DELETE FROM savings WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

    bot.reply_to(message, "🗑️ Your account has been deleted. Send /register anytime to start fresh.")

bot.polling()
