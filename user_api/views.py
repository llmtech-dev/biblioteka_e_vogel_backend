# user_api/views.py
# ZËVENDËSO PLOTËSISHT — shton moderator_login_view dhe me_view

from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import (
    RegistrationSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    ModeratorLoginSerializer,
)
from .throttling import (
    LoginRateThrottle,
    RegisterRateThrottle,
    ModeratorLoginRateThrottle,
)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
def registration_view(request):
    serializer = RegistrationSerializer(data=request.data)
    if serializer.is_valid():
        account = serializer.save()
        token = Token.objects.get(user=account)
        return Response({
            'response': 'Regjistrimi u krye me sukses.',
            'name': account.name,
            'email': account.email,
            'token': token.key,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'name': user.name,
            'email': user.email,
            'role': user.role,
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ModeratorLoginRateThrottle])
def moderator_login_view(request):
    """
    POST /api/users/moderator-login/
    Body: { "email": "...", "password": "..." }
    Kthon token vetëm nëse user ka role=moderator ose role=admin.
    """
    serializer = ModeratorLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'name': user.name,
            'email': user.email,
            'role': user.role,
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """
    GET /api/users/me/
    Kthon profilin e përdoruesit të kyçur.
    """
    user = request.user
    return Response({
        'id': user.pk,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'is_moderator': user.is_moderator,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        request.user.auth_token.delete()
    except Exception:
        pass
    return Response({'detail': 'Dolet me sukses.'}, status=status.HTTP_200_OK)


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
            status=status.HTTP_200_OK,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)