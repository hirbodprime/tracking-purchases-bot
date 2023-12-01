import os
import django
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'track_purchases.settings')
django.setup()

def requires_channel_membership(func):
    def wrapper(update, context):
        user_id = update.message.from_user.id
        channel_username = '@hirbots'  # Replace with your channel's username

        try:
            chat_member = context.bot.get_chat_member(chat_id=channel_username, user_id=user_id)
            if chat_member.status not in ['left', 'kicked']:
                return func(update, context)
            else:
                update.message.reply_text('Please join our channel first to use this bot.\n Channel: @Hirbots')
        except Exception as e:
            print(f"Error: {e}")
            update.message.reply_text(f'An error occurred: {str(e)}')
            # Or log the error for debugging

    return wrapper
