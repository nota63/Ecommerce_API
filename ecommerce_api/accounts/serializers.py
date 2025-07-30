from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from .models import Profile

# Register Serializer - Allowes users to create their accounts
class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

# User Basic Serializer
class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['username', 'date_joined']

        
# 2) Allowes users to manage their profiles 
class ProfileSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    age = serializers.ReadOnlyField()
    full_address = serializers.ReadOnlyField()
    is_profile_complete = serializers.ReadOnlyField()
    
    # Display choices as readable text
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    marital_status_display = serializers.CharField(source='get_marital_status_display', read_only=True)
    employment_status_display = serializers.CharField(source='get_employment_status_display', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'full_name', 'bio', 'date_of_birth', 'age',
            'gender', 'gender_display', 'phone', 'alternate_phone', 'email_secondary',
            'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country',
            'full_address', 'occupation', 'company', 'employment_status', 'employment_status_display',
            'industry', 'experience_years', 'marital_status', 'marital_status_display',
            'website', 'linkedin_profile', 'twitter_handle', 'profile_image',
            'newsletter_subscription', 'email_notifications', 'sms_notifications',
            'profile_visibility', 'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relation', 'created_at', 'updated_at', 'is_verified',
            'verification_date', 'is_profile_complete'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_verified', 'verification_date']

    def validate_phone(self, value):
        if value and not value.startswith('+'):
            raise serializers.ValidationError("Phone number should start with country code (+)")
        return value

    def validate_date_of_birth(self, value):
        if value:
            from datetime import date
            if value > date.today():
                raise serializers.ValidationError("Date of birth cannot be in the future")
            if (date.today() - value).days < 18 * 365:  # Rough age validation
                raise serializers.ValidationError("User must be at least 18 years old")
        return value

class ProfileSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for profile summaries"""
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = Profile
        fields = ['id', 'full_name', 'bio', 'profile_image', 'city', 'country', 'age', 'occupation']

