from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser


class RegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={"input_type": "password"}, write_only=True)

    class Meta:
        model = CustomUser
        fields = ["name", "email", "password", "password2"]
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def save(self):
        password = self.validated_data["password"]
        password2 = self.validated_data["password2"]

        if password != password2:
            raise serializers.ValidationError({"gabim": "Fjalekalimet nuk perputhen!"})

        if CustomUser.objects.filter(email=self.validated_data["email"]).exists():
            raise serializers.ValidationError({"gabim": "email i regjistruar me pare ne databaze!"})

        account = CustomUser(email=self.validated_data["email"], name=self.validated_data["name"])

        account.set_password(password)
        account.save()

        return account


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        user = authenticate(username=email, password=password)
        if user:
            return user
        raise serializers.ValidationError("Kredencialet nuk jane te sakta.")


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Fjalekalimi i vjeter nuk eshte i sakte.")
        return value

    def validate_new_password(self, value):
        # Add any password validation here
        if len(value) < 8:
            raise serializers.ValidationError("Fjalekalimi duhet te kete 8 ose me shume karaktere.")
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
