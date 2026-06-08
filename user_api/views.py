# user_api/views.py
# SHTUAR: moderator_login endpoint, profile endpoint, me_endpoint

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    RegistrationSerializer, LoginSerializer,
    ChangePasswordSerializer, ModeratorLoginSerializer,
    UserProfileSerializer
)
from .permissions import IsModeratorOrAdmin


@api_view(["POST"])
def registration_view(request):
    serializer = RegistrationSerializer(data=request.data)
    if serializer.is_valid():
        account = serializer.save()
        token = Token.objects.get(user=account)
        return Response({
            "response": "Regjistrimi u krye me sukses.",
            "name": account.name,
            "email": account.email,
            "token": token.key
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data
        token, _ = Token.objects.get_or_create(user=user)
        # Përditëso last_login
        user.last_login_at = timezone.now()
        user.save(update_fields=['last_login_at'])
        return Response({
            "token": token.key,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def moderator_login_view(request):
    """
    Login i posaçëm për moderatoren — kërkon role=moderator ose admin.
    POST /api/users/moderator-login/
    Body: { "email": "...", "password": "..." }
    Response: { "token": "...", "name": "...", "email": "...", "role": "..." }
    """
    serializer = ModeratorLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data
        token, _ = Token.objects.get_or_create(user=user)
        user.last_login_at = timezone.now()
        user.save(update_fields=['last_login_at'])
        return Response({
            "token": token.key,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    """
    Kthen profilin e moderatores me statistika.
    GET /api/users/me/
    """
    user = request.user
    if not user.is_moderator:
        return Response(
            {"error": "Nuk keni leje aksesi."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Merr statistikat
    from books_api.models import Book
    from quizes_api.models import Quiz

    stats = {
        "total_books": Book.objects.filter(is_active=True).count(),
        "total_quizzes": Quiz.objects.count(),
        "books_with_notifications": Book.objects.filter(
            notification_sent=True
        ).count(),
    }

    serializer = UserProfileSerializer(user)
    return Response({
        **serializer.data,
        "stats": stats,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    request.user.auth_token.delete()
    return Response({"detail": "Dolet me sukses."}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    serializer = ChangePasswordSerializer(
        data=request.data, context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(
            {'detail': 'Fjalëkalimi u ndryshua me sukses.'},
            status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
