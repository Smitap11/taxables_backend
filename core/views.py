# core/views.py
from datetime import date, datetime
from typing import Optional, Tuple, List

from django.db.models import Sum, Q
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Income, Expense, Budget
from .serializers import IncomeSerializer, ExpenseSerializer, BudgetSerializer


# -------------------
# Helpers
# -------------------
def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        # Accept YYYY-MM-DD (trim anything extra like time)
        s = s[:10]
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _parse_pagination(request) -> Tuple[int, int]:
    """
    limit / offset pagination (optional). Defaults: limit=50, offset=0.
    """
    try:
        limit = int(request.GET.get("limit", "50"))
    except Exception:
        limit = 50
    try:
        offset = int(request.GET.get("offset", "0"))
    except Exception:
        offset = 0
    limit = max(1, min(limit, 200))  # clamp 1..200
    offset = max(0, offset)
    return limit, offset


# -------------------
# Type slugs <-> DB labels
# -------------------
# Frontend slugs we use everywhere:
#   all | income | expense | savings | emis | loans&advance | other
SLUG_TO_TYPES = {
    "expense": ["Expense", "Expenses", ""],  # include legacy empty as Expense
    "savings": ["Savings", "Saving"],
    "emis": ["EMIs", "EMI"],
    "loans&advance": ["Loans&Advance", "Loans & Advance", "Loan", "Loans"],
    "other": ["Other"],
}
ALL_SLUGS = ["income", "expense", "savings", "emis", "loans&advance", "other"]


def _labels_for_slug(slug: str) -> List[str]:
    """Expense.type values that correspond to a given slug."""
    return SLUG_TO_TYPES.get(slug, [])


def _present_type_slugs(user) -> List[str]:
    """
    Build a dynamic list of slugs present in DB (plus 'all' at the start),
    SCOPED TO USER. Falls back to all known slugs if DB is empty/new.
    """
    slugs: List[str] = []

    if Income.objects.filter(user=user).exists():
        slugs.append("income")

    existing_types = set(
        (t or "").strip()
        for t in Expense.objects.filter(user=user).values_list("type", flat=True).distinct()
    )
    for slug in ["expense", "savings", "emis", "loans&advance", "other"]:
        labels = set(_labels_for_slug(slug))
        if existing_types & labels:
            slugs.append(slug)

    if not slugs:
        slugs = ALL_SLUGS.copy()

    return ["all"] + slugs


# -------------------
# Income
# -------------------
@api_view(["GET", "POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def income_list(request):
    if request.method == "GET":
        # Optional filters: from, to, min_amount, max_amount, remark/source
        from_d = _parse_date(request.GET.get("from"))
        to_d = _parse_date(request.GET.get("to"))
        min_amt = request.GET.get("min_amount")
        max_amt = request.GET.get("max_amount")
        remark = (request.GET.get("remark") or "").strip()

        qs = Income.objects.filter(user=request.user)
        if from_d:
            qs = qs.filter(date__gte=from_d)
        if to_d:
            qs = qs.filter(date__lte=to_d)
        if min_amt:
            qs = qs.filter(amount__gte=min_amt)
        if max_amt:
            qs = qs.filter(amount__lte=max_amt)
        if remark:
            qs = qs.filter(Q(remark__icontains=remark) | Q(source__icontains=remark))

        qs = qs.order_by("-date", "-id")
        limit, offset = _parse_pagination(request)
        page = qs[offset : offset + limit]
        data = IncomeSerializer(page, many=True).data
        return Response({"count": qs.count(), "results": data})

    # POST
    body = request.data
    payload = {
        "amount": body.get("amount"),
        "date": (body.get("date") or "")[:10],
        "source": (body.get("source") or "").strip(),
        "remark": body.get("remark", ""),
    }
    ser = IncomeSerializer(data=payload)
    if ser.is_valid():
        obj = ser.save(user=request.user)
        return Response(IncomeSerializer(obj).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------
# Expense (and subtypes via `type`)
# -------------------
@api_view(["GET", "POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def expense_list(request):
    if request.method == "GET":
        # Optional filters
        from_d = _parse_date(request.GET.get("from"))
        to_d = _parse_date(request.GET.get("to"))
        min_amt = request.GET.get("min_amount")
        max_amt = request.GET.get("max_amount")
        remark = (request.GET.get("remark") or "").strip()
        category_q = (request.GET.get("category") or "").strip()
        t_slug = (request.GET.get("type") or "").strip().lower()

        qs = Expense.objects.filter(user=request.user)
        if from_d:
            qs = qs.filter(date__gte=from_d)
        if to_d:
            qs = qs.filter(date__lte=to_d)
        if min_amt:
            qs = qs.filter(amount__gte=min_amt)
        if max_amt:
            qs = qs.filter(amount__lte=max_amt)
        if remark:
            qs = qs.filter(remark__icontains=remark)
        if category_q:
            qs = qs.filter(category__icontains=category_q)

        # Restrict by slug if provided
        if t_slug in SLUG_TO_TYPES:
            labels = _labels_for_slug(t_slug)
            qs = qs.filter(type__in=labels)

        qs = qs.order_by("-date", "-id")
        limit, offset = _parse_pagination(request)
        page = qs[offset : offset + limit]
        data = ExpenseSerializer(page, many=True).data
        return Response({"count": qs.count(), "results": data})

    # POST
    body = request.data
    payload = {
        "date": (body.get("date") or "")[:10],
        "amount": body.get("amount"),
        "remark": body.get("remark", ""),
        "type": (body.get("type") or "Expense").strip(),
        "category": (body.get("category") or "").strip(),
    }
    ser = ExpenseSerializer(data=payload)
    if ser.is_valid():
        obj = ser.save(user=request.user)
        return Response(ExpenseSerializer(obj).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------
# Budget
# -------------------
@api_view(["GET", "POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def budget_list(request):
    if request.method == "GET":
        # Optional: filter by month range
        from_d = _parse_date(request.GET.get("from"))
        to_d = _parse_date(request.GET.get("to"))

        qs = Budget.objects.filter(user=request.user)
        if from_d:
            qs = qs.filter(date__gte=from_d)
        if to_d:
            qs = qs.filter(date__lte=to_d)

        qs = qs.order_by("-date", "-id")
        limit, offset = _parse_pagination(request)
        page = qs[offset : offset + limit]
        data = BudgetSerializer(page, many=True).data
        return Response({"count": qs.count(), "results": data})

    ser = BudgetSerializer(data=request.data)
    if ser.is_valid():
        obj = ser.save(user=request.user)
        return Response(BudgetSerializer(obj).data, status=status.HTTP_201_CREATED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------
# Dashboard (sample)
# -------------------
@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    try:
        data = {
            "quickLinks": [
                {"label": "Transactions", "route": "/transactions", "icon": "list-alt", "data": "-"},
                {"label": "Wealth", "route": "/wealth", "icon": "account-balance", "data": "-"},
                {"label": "Insights", "route": "/insights", "icon": "insights", "data": "-"},
            ],
            "summary": {
                "income": "₹85K",
                "expenses": "₹40K",
                "savings": "₹10K",
                "insights": "Spending 20% higher than last month",
                "reminders": "💳 EMI due on 25th | 💡 Electricity bill on 28th",
                "goals": "🎯 Save ₹10,000 this month - 60% done",
                "tips": "💡 Automate your savings to build wealth consistently.",
            },
        }
        return Response(data)
    except Exception as e:
        print("Error in dashboard:", e)
        return Response({"error": "Internal Server Error"}, status=500)


# -------------------
# Filters (types + categories)
# -------------------
@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def filter_types(request):
    """
    Returns slugs the FE understands, scoped to current user.
    Example: ["all","income","expense","savings","emis","loans&advance","other"]
    """
    return Response(_present_type_slugs(request.user))


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def filter_categories(request):
    """
    GET /filters/categories/?type=<slug>
      - income            -> distinct Income.source (non-empty)
      - expense/savings/emis/loans&advance/other -> distinct Expense.category filtered by Expense.type
    """
    kind = (request.GET.get("type") or "").strip().lower()
    if not kind:
        return Response([])

    cats: List[str] = []

    if kind == "income":
        cats = list(
            Income.objects.filter(user=request.user)
            .exclude(source="")
            .values_list("source", flat=True)
            .distinct()
        )
    else:
        labels = _labels_for_slug(kind)
        qs = Expense.objects.filter(user=request.user)
        if labels:
            qs = qs.filter(type__in=labels)
        cats = list(qs.exclude(category="").values_list("category", flat=True).distinct())

    cats = sorted([c for c in cats if c])
    return Response(cats)


# -------------------
# Transactions (combined list, FE field names)
# -------------------
@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def transaction_history(request):
    """
    Unified feed for FE with filters compatible with your app:
      type: income | expense | savings | emis | loans&advance | other | all
      from, to: YYYY-MM-DD
      min_amount, max_amount
      remark, category
      limit, offset
    Defaults to current month if from/to are not provided.
    """
    t_type    = (request.GET.get("type") or "all").lower()
    from_date_q = _parse_date(request.GET.get("from"))
    to_date_q   = _parse_date(request.GET.get("to"))
    min_amt   = request.GET.get("min_amount")
    max_amt   = request.GET.get("max_amount")
    remark    = (request.GET.get("remark") or "").strip()
    category_q = (request.GET.get("category") or "").strip()
    limit, offset = _parse_pagination(request)

    # default to current month if not provided
    today = date.today()
    from_d = from_date_q or date(today.year, today.month, 1)
    to_d   = to_date_q or today

    rows = []

    # ---------- Income ----------
    if t_type in ("income", "all"):
        qs_inc = Income.objects.filter(user=request.user, date__gte=from_d, date__lte=to_d)
        if min_amt: qs_inc = qs_inc.filter(amount__gte=min_amt)
        if max_amt: qs_inc = qs_inc.filter(amount__lte=max_amt)
        if remark:  qs_inc = qs_inc.filter(Q(remark__icontains=remark) | Q(source__icontains=remark))
        if category_q: qs_inc = qs_inc.filter(Q(source__icontains=category_q) | Q(remark__icontains=category_q))

        for it in IncomeSerializer(qs_inc, many=True).data:
            rows.append({
                "id": it["id"],
                "type": "Income",
                "remark": it.get("remark") or it.get("source", ""),
                "date": it["date"],
                "amount": it["amount"],
                "category": it.get("source", ""),
            })

    # ---------- Expense + subtypes ----------
    exp_base = Expense.objects.filter(user=request.user, date__gte=from_d, date__lte=to_d)
    if min_amt:    exp_base = exp_base.filter(amount__gte=min_amt)
    if max_amt:    exp_base = exp_base.filter(amount__lte=max_amt)
    if remark:     exp_base = exp_base.filter(remark__icontains=remark)
    if category_q: exp_base = exp_base.filter(category__icontains=category_q)

    if t_type == "expense":
        qs_exp = exp_base.filter(Q(type__iexact="Expense") | Q(type__isnull=True) | Q(type__exact=""))
    elif t_type == "savings":
        qs_exp = exp_base.filter(type__iexact="Savings")
    elif t_type == "emis":
        qs_exp = exp_base.filter(type__iexact="EMIs")
    elif t_type == "loans&advance":
        qs_exp = exp_base.filter(type__iexact="Loans&Advance")
    elif t_type == "other":
        qs_exp = exp_base.filter(type__iexact="Other")
    elif t_type == "all":
        qs_exp = exp_base
    else:
        qs_exp = Expense.objects.none()

    for it in ExpenseSerializer(qs_exp, many=True).data:
        rows.append({
            "id": it["id"],
            "type": it.get("type") or "Expense",
            "date": it["date"],
            "amount": it["amount"],
            "remark": it.get("remark", ""),
            "category": it.get("category", ""),
        })

    # newest first
    rows.sort(key=lambda x: (x.get("date", ""), str(x.get("id", ""))), reverse=True)

    # pagination after merge
    total = len(rows)
    page = rows[offset : offset + limit]
    return Response({"count": total, "results": page})


# -------------------
# Insights (uses FE names)
# -------------------
@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def insights_summary(request):
    scope = request.GET.get("scope", "month")  # 'month' | 'all'
    today = date.today()

    exp_qs = Expense.objects.filter(user=request.user)
    inc_qs = Income.objects.filter(user=request.user)

    if scope == "month":
        exp_qs = exp_qs.filter(date__year=today.year, date__month=today.month)
        inc_qs = inc_qs.filter(date__year=today.year, date__month=today.month)

    rows = []
    for b in Budget.objects.filter(user=request.user):
        cat = (b.category or "").strip().lower()
        sub = (b.subcategory or "").strip()

        actual = 0.0
        if cat == "expense":
            actual = exp_qs.filter(category__iexact=sub).aggregate(s=Sum("amount"))["s"] or 0
        elif cat in ("saving", "savings"):
            # Treat "savings" as income tagged/remarked accordingly
            actual = inc_qs.filter(Q(remark__icontains=sub) | Q(source__icontains=sub)).aggregate(s=Sum("amount"))["s"] or 0

        planned = float(b.amount)
        rows.append({
            "category": b.category,
            "subcategory": b.subcategory,
            "planned": planned,
            "actual": float(actual),
            "difference": float(actual) - planned,
        })

    return Response(rows)


# -------------------
# Detail endpoints (GET, PUT, PATCH, DELETE)
# -------------------
@api_view(["GET", "PUT", "PATCH", "DELETE"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def income_detail(request, pk: int):
    try:
        obj = Income.objects.filter(user=request.user).get(pk=pk)
    except Income.DoesNotExist:
        return Response({"detail": "Not found."}, status=404)

    if request.method == "GET":
        return Response(IncomeSerializer(obj).data)

    partial = (request.method == "PATCH")
    data = request.data.copy()
    if isinstance(data.get("date"), str):
        data["date"] = data["date"][:10]
    ser = IncomeSerializer(obj, data=data, partial=partial)
    if ser.is_valid():
        ser.save()  # user unchanged
        return Response(ser.data)
    return Response(ser.errors, status=400)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def expense_detail(request, pk: int):
    try:
        obj = Expense.objects.filter(user=request.user).get(pk=pk)
    except Expense.DoesNotExist:
        return Response({"detail": "Not found."}, status=404)

    if request.method == "GET":
        return Response(ExpenseSerializer(obj).data)

    partial = (request.method == "PATCH")
    data = request.data.copy()
    if isinstance(data.get("date"), str):
        data["date"] = data["date"][:10]
    ser = ExpenseSerializer(obj, data=data, partial=partial)
    if ser.is_valid():
        ser.save()  # user unchanged
        return Response(ser.data)
    return Response(ser.errors, status=400)
