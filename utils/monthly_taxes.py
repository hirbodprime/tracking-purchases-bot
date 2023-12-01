from django.db.models.functions import TruncMonth
from collections import defaultdict
import calendar
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'track_purchases.settings')
django.setup()

from tracking.models import Purchase

def calculate_monthly_taxes(user):
    purchases = Purchase.objects.filter(user=user)
    monthly_totals = defaultdict(float)

    for purchase in purchases:
        month = purchase.date.strftime("%Y-%m")
        monthly_totals[month] += purchase.amount

    tax_rate = TAX_RATES.get(user.country, 0)
    monthly_taxes = {month: total * tax_rate for month, total in monthly_totals.items()}

    return monthly_taxes
