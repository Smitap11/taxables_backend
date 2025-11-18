# core/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# --- optional profile for extra user info (phone, etc.) ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=20, blank=True, default="")
    # add more fields later as needed (avatar, address, etc.)

    def __str__(self):
        return f"Profile({self.user.username or self.user.email})"


@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class Income(models.Model):
    # NEW: link row to the logged-in user (kept nullable so current data/migrations don't break)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="incomes",
        null=True, blank=True
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()  # (kept as-is)
    source = models.CharField(max_length=80, default="", blank=True)
    remark = models.CharField(max_length=255, default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        label = self.source or "Income"
        return f"{label} {self.amount} on {self.date}"


class Budget(models.Model):
    # NEW: per-user
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="budgets",
        null=True, blank=True
    )

    category = models.CharField(max_length=100)     # e.g. "Expense" or "Saving"
    subcategory = models.CharField(max_length=100)  # e.g. "Groceries", "SIP", etc.
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.date} | {self.category} - {self.subcategory} - ₹{self.amount}"


class Expense(models.Model):
    # NEW: per-user
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="expenses",
        null=True, blank=True
    )

    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    remark = models.CharField(max_length=255, default="", blank=True)

    # UI subtypes: "Expense" | "Saving" | "EMIs" | "Loans&Advance" | "Other"
    type = models.CharField(max_length=100, default="Expense", blank=True)
    category = models.CharField(max_length=100, default="", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"[{self.type}:{self.category}] {self.remark} - ₹{self.amount} on {self.date}"
