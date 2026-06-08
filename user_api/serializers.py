# user_api/serializers.py

from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser


class RegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(
        style={"input_type": "password"}, write_only=True
    )

    class Meta:
        model = CustomUser
        fields = ["name", "email", "password", "password2"]
        extra_kwargs = {"password": {"write_only": True}}

    def save(self):
        password = self.validated_data["password"]
        password2 = self.validated_data["password2"]
        if password != password2:
            raise serializers.ValidationError(
                {"gabim": "Fjalëkalimet nuk përputhen!"}
            )
        if CustomUser.objects.filter(
            email=self.validated_data["email"]
        ).exists():
            raise serializers.ValidationError(
                {"gabim": "Email i regjistruar më parë!"}
            )
        account = CustomUser(
            email=self.validated_data["email"],
            name=self.validated_data["name"],
        )
        account.set_password(password)
        account.save()
        return account


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data.get('email'), password=data.get('password'))
        if user:
            return user
        raise serializers.ValidationError("Kredencialet nuk janë të sakta.")


class ModeratorLoginSerializer(serializers.Serializer):
    """Login vetëm për moderatore dhe admin."""
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(
            username=data.get('email'), password=data.get('password')
        )
        if not user:
            raise serializers.ValidationError(
                "Kredencialet nuk janë të sakta."
            )
        if not user.is_active:
            raise serializers.ValidationError("Llogaria është çaktivizuar.")
        if not user.is_moderator:
            raise serializers.ValidationError(
                "Nuk keni leje për të hyrë si moderatore."
            )
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                "Fjalëkalimi i vjetër nuk është i saktë."
            )
        return value

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Fjalëkalimi duhet të ketë 8 ose më shumë karaktere."
            )
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'name', 'email', 'role', 'created_at', 'last_login_at']
        read_only_fields = ['id', 'email', 'role', 'created_at', 'last_login_at']
