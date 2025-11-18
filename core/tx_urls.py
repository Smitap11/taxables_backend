from django.urls import path
from . import views

urlpatterns = [
  path("", views.TransactionListCreate.as_view(), name="tx-list-create"),
  path("<int:pk>/", views.TransactionDetail.as_view(), name="tx-detail"),
  path("kpis/month/", views.month_kpis, name="tx-month-kpis"),
  path("categories/", views.CategoryListCreate.as_view(), name="cat-list-create"),
  path("categories/<int:pk>/", views.CategoryDetail.as_view(), name="cat-detail"),
]
