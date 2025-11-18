# core/filters.py
import django_filters as df
from .models import Transaction

class TransactionFilter(df.FilterSet):
    from_date = df.DateFilter(field_name="date", lookup_expr="gte")
    to_date   = df.DateFilter(field_name="date", lookup_expr="lte")
    min_amount = df.NumberFilter(field_name="amount", lookup_expr="gte")
    max_amount = df.NumberFilter(field_name="amount", lookup_expr="lte")
    type     = df.CharFilter(field_name="type", lookup_expr="iexact")
    remark   = df.CharFilter(field_name="remark", lookup_expr="icontains")
    category = df.NumberFilter(field_name="category_id", lookup_expr="exact")

    class Meta:
        model = Transaction
        fields = ["type", "from_date", "to_date", "remark", "min_amount", "max_amount", "category"]
