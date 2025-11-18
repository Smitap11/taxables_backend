from rest_framework import serializers
from .models import Income, Budget, Expense


class IncomeSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Income
        fields = ["id", "user", "amount", "date", "source", "remark", "created_at"]
        read_only_fields = ["user", "created_at"]


class BudgetSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Budget
        fields = ["id", "user", "category", "subcategory", "amount", "date", "created_at"]
        read_only_fields = ["user", "created_at"]


class ExpenseSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Expense
        fields = ["id", "user", "date", "amount", "remark", "type", "category", "created_at"]
        read_only_fields = ["user", "created_at"]

    def validate(self, attrs):
        """
        Keep FE names. Ensure `category` present for expense-like entries,
        but allow `type == "Other"` without a category (default it).
        """
        t = (attrs.get("type") or "").strip() or "Expense"
        c = (attrs.get("category") or "").strip()
        t_l = t.lower()

        # Allow "Other" without category; default to "Other"
        if t_l == "other":
            attrs["type"] = "Other"
            attrs["category"] = c or "Other"
            return attrs

        # For the rest, category is required
        if t_l in ("expense", "saving", "savings", "emis", "emi", "loans&advance", "loan", "loans"):
            if not c:
                raise serializers.ValidationError({"category": ["Category is required."]})

        attrs["type"] = t
        attrs["category"] = c
        return attrs
