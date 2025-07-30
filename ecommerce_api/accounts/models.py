from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from PIL import Image
import os
# Create your models here.



class Profile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('S', 'Single'),
        ('M', 'Married'),
        ('D', 'Divorced'),
        ('W', 'Widowed'),
        ('O', 'Other'),
    ]
    
    EMPLOYMENT_STATUS_CHOICES = [
        ('E', 'Employed'),
        ('U', 'Unemployed'),
        ('S', 'Self-employed'),
        ('R', 'Retired'),
        ('ST', 'Student'),
        ('O', 'Other'),
    ]

    # Basic Information
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=100,null=True, blank=True)
    bio = models.TextField(max_length=500, null=True ,blank=True, help_text="Tell us about yourself")
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES,null=True, blank=True)
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(validators=[phone_regex], max_length=17, null=True, blank=True)
    alternate_phone = models.CharField(validators=[phone_regex], max_length=17, null=True, blank=True)
    email_secondary = models.EmailField(null=True, blank=True, help_text="Alternative email address")
    
    # Address Information
    address_line_1 = models.CharField(max_length=255, null=True, blank=True)
    address_line_2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100,null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True, default='India')
    
    # Professional Information
    occupation = models.CharField(max_length=100, null=True, blank=True)
    company = models.CharField(max_length=100, null=True, blank=True)
    employment_status = models.CharField(max_length=2, choices=EMPLOYMENT_STATUS_CHOICES, null=True, blank=True)
    industry = models.CharField(max_length=100,null=True, blank=True)
    experience_years = models.PositiveIntegerField(null=True, blank=True, help_text="Years of experience")
    
    # Personal Information
    marital_status = models.CharField(max_length=1, choices=MARITAL_STATUS_CHOICES, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    linkedin_profile = models.URLField(null=True, blank=True)
    twitter_handle = models.CharField(max_length=50, null=True, blank=True)
    
    # Profile Image
    profile_image = models.ImageField(
        upload_to='profile_images/',
        null=True,
        blank=True,
        help_text="Profile picture"
    )
    
    # Preferences
    newsletter_subscription = models.BooleanField(default=True,null=True, blank=True)
    email_notifications = models.BooleanField(default=True,null=True, blank=True)
    sms_notifications = models.BooleanField(default=False,null=True, blank=True)
    profile_visibility = models.BooleanField(default=True, help_text="Make profile visible to others",null=True, blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100,null=True, blank=True)
    emergency_contact_phone = models.CharField(validators=[phone_regex], max_length=17, null=True, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True, blank=True)
    is_verified = models.BooleanField(default=False,null=True, blank=True)
    verification_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return self.full_name or self.user.username if self.user else 'No User'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Resize profile image if it exists
        if self.profile_image:
            img = Image.open(self.profile_image.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.profile_image.path)
    
    @property
    def age(self):
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    @property
    def full_address(self):
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join([part for part in address_parts if part])
    
    @property
    def is_profile_complete(self):
        required_fields = [
            self.full_name, self.phone, self.address_line_1, 
            self.city, self.state, self.country
        ]
        return all(field for field in required_fields)

