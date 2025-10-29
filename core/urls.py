# core/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views, auth_views  # import the MODULES

urlpatterns = [
    # --- data APIs ---
    path("income/", views.income_list),                 # GET, POST
    path("income/<int:pk>/", views.income_detail),      # GET, PUT, PATCH, DELETE

    # Use plural to match typical FE calls like /api/expenses/
    path("expenses/", views.expense_list),              # GET, POST
    path("expenses/<int:pk>/", views.expense_detail),   # GET, PUT, PATCH, DELETE

    path("budgets/", views.budget_list),                # GET, POST

    path("filters/types/", views.filter_types),         # GET
    path("filters/categories/", views.filter_categories),  # GET

    path("transactions/", views.transaction_history),   # GET
    path("insights/", views.insights_summary),          # GET

    # --- auth APIs ---
    path("auth/register/", auth_views.register),                  # POST
    path("auth/login/", auth_views.LoginView.as_view()),          # POST -> {access, refresh}
    path("auth/refresh/", TokenRefreshView.as_view()),            # POST -> {refresh} -> new {access}
    path("auth/me/", auth_views.me),                              # GET  -> current user
]
