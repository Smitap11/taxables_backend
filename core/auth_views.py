# core/auth_views.py
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """
    Body: { name, email, password }
    Returns: { access, refresh, user: {id, name, email} }
    """
    name = (request.data.get("name") or "").strip()
    email = (request.data.get("email") or "").strip().lower()
    password = request.data.get("password") or ""

    if not email or not password:
        return Response({"detail": "Email and password are required."}, status=400)
    if User.objects.filter(email=email).exists():
        return Response({"detail": "Email already registered."}, status=400)

    with transaction.atomic():
        # Use email as username for simplicity
        user = User(username=email, email=email, first_name=name[:150])
        user.set_password(password)
        user.save()

    # issue tokens (SimpleJWT)
    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)

    return Response({
        "access": access,
        "refresh": str(refresh),
        "user": {"id": user.id, "name": user.first_name or user.username, "email": user.email},
    }, status=status.HTTP_201_CREATED)


# Login: you can use SimpleJWT's built-in TokenObtainPairView at /api/auth/login/
class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def me(request):
    u = request.user
    return Response({
        "id": u.id,
        "name": u.first_name or u.username,
        "email": u.email,
    })
