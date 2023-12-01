import os
import django
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from django.db.models import Sum
from datetime import datetime
from dotenv import load_dotenv
from telegram import ParseMode
import random
from decorators.complete_profile import requires_profile_completion
from decorators.check_membership import requires_channel_membership
# Load environment variables from .env file
load_dotenv()
bot_token = os.getenv("BOT_TOKEN")

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'track_purchases.settings')
django.setup()
from django.db.utils import IntegrityError

from tracking.models import Purchase, Wallet, UserModel
EMAIL, USERNAME, COUNTRY, STATE = range(4)

COUNTRY_MAPPING = {
    "1": "USA",
    "2": "Canada",
    "3": "UK",
    "4": "Germany",
    "5": "France",
    "6": "Australia",
    "7": "Japan",
    "8": "South Korea",
    "9": "Brazil",
    "10": "India",
    "11": "Iran",
    # Add more countries as needed
}

def convert_number_to_country_name(number):
    return COUNTRY_MAPPING.get(number, "Unknown Country")
US_TAX_RATES = {
    "Alabama": 0.04, "Alaska": 0.0, "Arizona": 0.056,
    "Arkansas": 0.065, "California": 0.0725, "Colorado": 0.029,
    "Connecticut": 0.0635, "Delaware": 0.0, "Florida": 0.06,
    "Georgia": 0.04, "Hawaii": 0.04, "Idaho": 0.06,
    "Illinois": 0.0625, "Indiana": 0.07, "Iowa": 0.06,
    "Kansas": 0.065, "Kentucky": 0.06, "Louisiana": 0.0445,
    "Maine": 0.055, "Maryland": 0.06, "Massachusetts": 0.0625,
    "Michigan": 0.06, "Minnesota": 0.06875, "Mississippi": 0.07,
    "Missouri": 0.04225, "Montana": 0.0, "Nebraska": 0.055,
    "Nevada": 0.0685, "New Hampshire": 0.0, "New Jersey": 0.06625,
    "New Mexico": 0.05125, "New York": 0.04, "North Carolina": 0.0475,
    "North Dakota": 0.05, "Ohio": 0.0575, "Oklahoma": 0.045,
    "Oregon": 0.0, "Pennsylvania": 0.06, "Rhode Island": 0.07,
    "South Carolina": 0.06, "South Dakota": 0.045, "Tennessee": 0.07,
    "Texas": 0.0625, "Utah": 0.0595, "Vermont": 0.06,
    "Virginia": 0.053, "Washington": 0.065, "West Virginia": 0.06,
    "Wisconsin": 0.05, "Wyoming": 0.04
}

TAX_RATES = {
    "USA": 0.20,  # 20%
    "Canada": 0.15,  # 15%
    "UK": 0.25,  # 25%
    "Germany": 0.19,  # 19%
    "France": 0.20,  # 20%
    "Australia": 0.18,  # 18%
    "Japan": 0.10,  # 10%
    "South Korea": 0.15,  # 15%
    "Brazil": 0.17,  # 17%
    "India": 0.18,  # 18%
    "Iran": 0.9,  # 25%
}

def calculate_tax(country, state, amount):
    if country == "USA":
        tax_rate = US_TAX_RATES.get(state, 0)
    else:
        tax_rate = GLOBAL_TAX_RATES.get(country, 0)
    
    # Distribute amount to 100 and then multiply by tax rate
    return (amount / 100) * tax_rate

def start(update, context):
    user_id = update.message.from_user.id
    user, created = UserModel.objects.get_or_create(user_id=str(user_id))

    if not user.email or not user.username or not user.country:
        update.message.reply_text('Welcome! Let\'s complete your profile. What is your email address?')
        return EMAIL
    else:
        update.message.reply_text('Welcome back to the Purchase Tracker Bot! Type /help to see how to use.')
        return ConversationHandler.END

@requires_profile_completion
@requires_channel_membership    
def help_command(update, context):
    help_text = (
        "*Welcome to the Purchase Tracker Bot!*\n"
        "Below are the commands you can use:\n\n"
        "/start - Begin your interaction with the bot.\n"
        "/help - Show this help message.\n"
        "/record <amount> <location> <item> - Record a new purchase. Example: '/record 100 supermarket apples'.\n"
        "/purchases - List all your recorded purchases.\n"
        "/calculate <YYYY-MM-DD> - Calculate total spent since a given date.\n"
        "/paycheck <amount> <YYYY-MM-DD> - Record your paycheck. Example: '/paycheck 2000 2023-01-01'.\n"
        "/listpaychecks - List all your recorded paychecks.\n"
        "/sincepaycheck [ID] - Calculate your total purchases since the last paycheck or a specified ID.\n"
        "/tax <amount> [tax rate] - Calculate tax based on your location, or an optional manual tax rate.\n"
        "/updatestate <state> - Update your state information. Applicable for users in the USA.\n"
        "/monthlytax - Show a breakdown of taxes based on monthly purchases."
    )
    update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


def email(update, context):
    user_id = update.message.from_user.id
    user = UserModel.objects.get(user_id=str(user_id))
    new_email = update.message.text

    try:
        user.email = new_email
        user.save()
        update.message.reply_text('What should we call you? (Please enter your username)')
        return USERNAME
    except IntegrityError:
        update.message.reply_text('This email is already in use. Please enter another email address.')
        return EMAIL
def username(update, context):
    user_id = update.message.from_user.id
    user = UserModel.objects.get(user_id=str(user_id))
    new_username = update.message.text

    try:
        user.username = new_username
        user.save()

        countries = (
            "1. USA\n2. Canada\n3. UK\n4. Germany\n5. France\n"
            "6. Australia\n7. Japan\n8. South Korea\n9. Brazil\n"
            "10. India\n11. Iran\n"
        )
        update.message.reply_text(f'Where are you from?\n{countries}')
        return COUNTRY
    except IntegrityError:
        update.message.reply_text('This username is already taken. Please enter another username.')
        return USERNAME

def country(update, context):
    country_number = update.message.text
    country_name = convert_number_to_country_name(country_number)

    user_id = update.message.from_user.id
    user = UserModel.objects.get(user_id=str(user_id))
    user.country = country_name
    user.save()

    if country_name == "USA":
        update.message.reply_text('Which state are you from? Please enter the state name.')
        return STATE  # New state in the conversation handler
    elif country_name == "Unknown Country":
        update.message.reply_text('Unknown country number. Please try again or type /cancel to exit.')
        return COUNTRY
    else:
        update.message.reply_text('Thank you for completing your profile!')
        return ConversationHandler.END

def state(update, context):
    state_name = update.message.text.title()  # Capitalize the state name

    # Check if the entered state is in the US_TAX_RATES dictionary
    if state_name not in US_TAX_RATES:
        valid_states = "\n, ".join(US_TAX_RATES.keys())
        update.message.reply_text(f"Invalid state name. Please choose from the following: {valid_states}\n")
        # Return a state identifier that keeps the user in the current step
        return STATE  # Replace CURRENT_STATE with the appropriate state or step identifier

    # Existing logic for valid state names
    user_id = update.message.from_user.id
    user = UserModel.objects.get(user_id=str(user_id))
    user.state = state_name
    user.save()

    update.message.reply_text('Thank you for completing your profile!')
    return ConversationHandler.END



def cancel(update, context):
    update.message.reply_text('Profile update cancelled.')
    return ConversationHandler.END


@requires_profile_completion
def update_state(update, context):
    user_id = update.message.from_user.id
    user = UserModel.objects.get(user_id=str(user_id))

    try:
        new_state = context.args[0].title()
        user.state = new_state
        user.save()
        update.message.reply_text(f"Your state has been updated to {new_state}.")
    except IndexError:
        update.message.reply_text("Please provide your state. Usage: /updatestate <state>")



@requires_profile_completion
@requires_channel_membership
def add_paycheck(update, context):
    user_id = update.message.from_user.id
    user, created = UserModel.objects.get_or_create(user_id=str(user_id))

    try:
        amount, date_str = context.args[0], context.args[1]
        paycheck_date = datetime.strptime(date_str, '%Y-%m-%d')
        Wallet.objects.create(user=user, paycheck_amount=amount, paycheck_date=paycheck_date)
        update.message.reply_text(f"Paycheck of {amount} recorded on {paycheck_date.strftime('%Y-%m-%d')}.")
    except (IndexError, ValueError):
        update.message.reply_text("Please provide the paycheck amount and date in the format: '/paycheck amount YYYY-MM-DD'.")
@requires_profile_completion
@requires_channel_membership
def list_paychecks(update, context):
    user_id = update.message.from_user.id
    user, created = UserModel.objects.get_or_create(user_id=str(user_id))
    paychecks = Wallet.objects.filter(user=user).order_by('-paycheck_date')

    if paychecks.exists():
        response = "\n".join([f"*ID:* `{paycheck.id}` - *Amount:* `{paycheck.paycheck_amount}` - *Date:* `{paycheck.paycheck_date.strftime('%Y-%m-%d')}`" for paycheck in paychecks])
    else:
        response = "No paycheck records found."

    update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

@requires_profile_completion
@requires_channel_membership
def record_purchase(update, context):
    user_id = update.message.from_user.id
    user, created = UserModel.objects.get_or_create(user_id=str(user_id))

    if context.args:
        try:
            amount, location, item = ' '.join(context.args).split(' ', 2)
            Purchase.objects.create(user=user, amount=amount, location=location, item=item)
            update.message.reply_text('Purchase recorded!')
        except ValueError:
            update.message.reply_text("To record a purchase, send a message in the format '/record amount location item'.")
    else:
        update.message.reply_text("Please provide purchase details in the format '/record amount location item'.")

@requires_profile_completion
@requires_channel_membership
def list_purchases(update, context):
    user_id = update.message.from_user.id
    user, created = UserModel.objects.get_or_create(user_id=str(user_id))
    purchases = Purchase.objects.filter(user=user)

    if purchases.exists():
        response = "\n".join([f"{purchase.date.strftime('%Y-%m-%d %H:%M')} - {purchase.location} - {purchase.item} - {purchase.amount}" for purchase in purchases])
    else:
        response = "No purchases recorded."
    update.message.reply_text(response)

@requires_profile_completion
@requires_channel_membership
def calculate_since_paycheck(update, context):
    user_id = update.message.from_user.id
    user, created = UserModel.objects.get_or_create(user_id=str(user_id))
    paycheck_id = context.args[0] if context.args else None

    if paycheck_id:
        try:
            last_paycheck = Wallet.objects.get(user=user, id=paycheck_id)
        except Wallet.DoesNotExist:
            update.message.reply_text("Paycheck with provided ID not found.")
            return
    else:
        last_paycheck = Wallet.objects.filter(user=user).order_by('-paycheck_date').first()

    if last_paycheck:
        total_spent = Purchase.objects.filter(user=user, date__gte=last_paycheck.paycheck_date).aggregate(Sum('amount'))['amount__sum'] or 0
        remaining_balance = last_paycheck.paycheck_amount - total_spent
        response = (
            f"Total amount spent since paycheck on {last_paycheck.paycheck_date.strftime('%Y-%m-%d')}: {total_spent}\n"
            f"Remaining balance: {remaining_balance}"
        )
    else:
        response = "No paycheck record found."
    update.message.reply_text(response)

@requires_profile_completion
@requires_channel_membership
def calculate_tax_command(update, context):
    user_id = update.message.from_user.id
    user = UserModel.objects.get(user_id=str(user_id))

    # Check if state is set for USA users
    if user.country == "USA" and not user.state:
        update.message.reply_text("Please enter your state to calculate tax.")
        return

    try:
        amount = float(context.args[0])
        manual_tax_rate = float(context.args[1]) if len(context.args) > 1 else None
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /tax <amount> [optional manual tax rate]")
        return

    if manual_tax_rate is not None:
        tax = amount * manual_tax_rate
    else:
        tax = calculate_tax(user.country, user.state, amount)
    
    update.message.reply_text(f"Calculated tax: {tax}")


@requires_profile_completion
@requires_channel_membership
def calculate_total(update, context):
    user_id = update.message.from_user.id
    user, created = UserModel.objects.get_or_create(user_id=str(user_id))
    try:
        start_date = datetime.strptime(context.args[0], '%Y-%m-%d')
        total = Purchase.objects.filter(user=user, date__gte=start_date).aggregate(Sum('amount'))['amount__sum'] or 0
        response = f"Total amount spent since {start_date.strftime('%Y-%m-%d')}: {total}"
    except (IndexError, ValueError):
        response = "Please provide a valid date in the format YYYY-MM-DD."
    update.message.reply_text(response)


@requires_profile_completion
@requires_channel_membership
def monthly_tax_command(update, context):
    user_id = update.message.from_user.id
    user = UserModel.objects.get(user_id=str(user_id))

    if not user.country:
        update.message.reply_text("Your country is not set. Please update your profile.")
        return

    monthly_taxes = calculate_monthly_taxes(user)
    if not monthly_taxes:
        update.message.reply_text("No purchase records found.")
        return

    response = "Monthly Tax Breakdown:\n"
    for month, tax in monthly_taxes.items():
        year, month_num = month.split('-')
        month_name = calendar.month_name[int(month_num)]
        response += f"{month_name} {year}: {tax:.2f}\n"

    update.message.reply_text(response)



USERNAME, EMAIL, CAPTCHA = range(3)

def main():
    updater = Updater(token=bot_token, use_context=True)
    dp = updater.dispatcher
    # Add handlers to dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            EMAIL: [MessageHandler(Filters.text & ~Filters.command, email)],
            USERNAME: [MessageHandler(Filters.text & ~Filters.command, username)],
            COUNTRY: [MessageHandler(Filters.text & ~Filters.command, country)],
            STATE: [MessageHandler(Filters.text & ~Filters.command, state)],  # New state handler
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )


    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("tax", calculate_tax_command))
    dp.add_handler(CommandHandler("updatestate", update_state))
    dp.add_handler(CommandHandler("monthlytax", monthly_tax_command))
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("record", record_purchase))
    dp.add_handler(CommandHandler("purchases", list_purchases))
    dp.add_handler(CommandHandler("calculate", calculate_total))
    dp.add_handler(CommandHandler("sincepaycheck", calculate_since_paycheck))
    dp.add_handler(CommandHandler("paycheck", add_paycheck))
    dp.add_handler(CommandHandler("listpaychecks", list_paychecks))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
