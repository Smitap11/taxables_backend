from django.urls import path
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate

User = get_user_model()

def token_pair_response(user):
  refresh = RefreshToken.for_user(user)
  return {
    "refresh": str(refresh),
    "access": str(refresh.access_token),
    "user": {"id": user.id, "name": user.get_full_name() or user.username, "email": user.email},
  }

@csrf_exempt
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register(request):
  name = request.data.get("name", "").strip()
  email = request.data.get("email", "").lower().strip()
  password = request.data.get("password", "")
  if not email or not password:
    return Response({"detail": "Email and password required."}, status=400)
  if User.objects.filter(email=email).exists():
    return Response({"detail": "Email already exists."}, status=400)
  user = User.objects.create(username=email, email=email, first_name=name, password=make_password(password))
  return Response(token_pair_response(user), status=201)

@csrf_exempt
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login(request):
  email = request.data.get("email", "").lower().strip()
  password = request.data.get("password", "")
  user = authenticate(request, username=email, password=password)
  if not user:
    return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
  return Response(token_pair_response(user))

@api_view(["GET"])
def me(request):
  u = request.user
  return Response({"id": u.id, "name": u.get_full_name() or u.username, "email": u.email})

urlpatterns = [
  path("register/", register),
  path("login/", login),
  path("me/", me),
]
