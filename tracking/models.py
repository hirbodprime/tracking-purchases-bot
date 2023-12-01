from django.db import models

class UserModel(models.Model):
    user_id = models.CharField(max_length=100, unique=True)  # Telegram user ID
    username = models.CharField(max_length=100, unique=True,null=True, blank=True)
    email = models.EmailField(unique=True,null=True, blank=True)
    country = models.CharField(max_length=100,null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)  # New field for state
    # is_verified = models.BooleanField(default=False,null=True, blank=True)

class Purchase(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE,null=True,blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=255)
    item = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item} - {self.amount}"
        
class Wallet(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE,null=True,blank=True)
    paycheck_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paycheck_date = models.DateTimeField()

    def __str__(self):
        return f"Paycheck of {self.paycheck_amount} on {self.paycheck_date.strftime('%Y-%m-%d')}"