import os
import django
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'track_purchases.settings')
django.setup()

from tracking.models import UserModel

def requires_profile_completion(func):
    def wrapper(update, context):
        user_id = update.message.from_user.id
        user = UserModel.objects.filter(user_id=str(user_id)).first()

        # Check if user exists and has completed the required fields
        if not user or not user.email or not user.username or not user.country:
            update.message.reply_text('Please complete your profile first. Type /start to begin.')
            return ConversationHandler.END
        else:
            return func(update, context)

    return wrapper
