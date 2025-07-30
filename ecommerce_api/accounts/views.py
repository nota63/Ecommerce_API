from django.shortcuts import render
from rest_framework import generics
from .serializers import (RegisterSerializer, ProfileSerializer,ProfileSummarySerializer)
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Profile


# 1) Register 
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


# 2) Manage Profiles 
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        """Get user's profile"""
        try:
            profile = request.user.profile
            serializer = ProfileSerializer(profile)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': 'Profile retrieved successfully'
            })
        except Profile.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Profile not found'
            }, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        """Complete profile update"""
        try:
            profile = request.user.profile
            serializer = ProfileSerializer(profile, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'data': serializer.data,
                    'message': 'Profile updated successfully'
                })
            return Response({
                'success': False,
                'errors': serializer.errors,
                'message': 'Validation failed'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Profile.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Profile not found'
            }, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request):
        """Partial profile update"""
        try:
            profile = request.user.profile
            serializer = ProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'data': serializer.data,
                    'message': 'Profile updated successfully'
                })
            return Response({
                'success': False,
                'errors': serializer.errors,
                'message': 'Validation failed'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Profile.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Profile not found'
            }, status=status.HTTP_404_NOT_FOUND)

class ProfileImageUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        """Upload or update profile image"""
        try:
            profile = request.user.profile
            if 'profile_image' not in request.FILES:
                return Response({
                    'success': False,
                    'message': 'No image file provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            profile.profile_image = request.FILES['profile_image']
            profile.save()
            
            return Response({
                'success': True,
                'data': {'profile_image': profile.profile_image.url if profile.profile_image else None},
                'message': 'Profile image uploaded successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error uploading image: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProfileSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Search profiles by name, city, occupation, etc."""
        query = request.query_params.get('q', '')
        city = request.query_params.get('city', '')
        occupation = request.query_params.get('occupation', '')
        
        profiles = Profile.objects.filter(profile_visibility=True).exclude(user=request.user)
        
        if query:
            profiles = profiles.filter(
                Q(full_name__icontains=query) |
                Q(bio__icontains=query) |
                Q(occupation__icontains=query) |
                Q(company__icontains=query)
            )
        
        if city:
            profiles = profiles.filter(city__icontains=city)
            
        if occupation:
            profiles = profiles.filter(occupation__icontains=occupation)
        
        profiles = profiles[:50]  # Limit results
        serializer = ProfileSummarySerializer(profiles, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'count': len(serializer.data),
            'message': 'Profiles retrieved successfully'
        })

class ProfileStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get profile completion stats and suggestions"""
        try:
            profile = request.user.profile
            
            # Calculate completion percentage
            total_fields = 20  # Adjust based on important fields
            completed_fields = 0
            
            important_fields = [
                profile.full_name, profile.phone, profile.address_line_1,
                profile.city, profile.state, profile.country, profile.occupation,
                profile.bio, profile.date_of_birth, profile.gender
            ]
            
            completed_fields = sum(1 for field in important_fields if field)
            completion_percentage = (completed_fields / len(important_fields)) * 100
            
            # Suggestions for improvement
            suggestions = []
            if not profile.profile_image:
                suggestions.append("Add a profile picture")
            if not profile.bio:
                suggestions.append("Write a bio about yourself")
            if not profile.date_of_birth:
                suggestions.append("Add your date of birth")
            if not profile.occupation:
                suggestions.append("Add your occupation")
            if not profile.linkedin_profile:
                suggestions.append("Add your LinkedIn profile")
            
            return Response({
                'success': True,
                'data': {
                    'completion_percentage': round(completion_percentage, 2),
                    'completed_fields': completed_fields,
                    'total_fields': len(important_fields),
                    'suggestions': suggestions,
                    'is_complete': profile.is_profile_complete
                },
                'message': 'Profile stats retrieved successfully'
            })
        except Profile.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Profile not found'
            }, status=status.HTTP_404_NOT_FOUND)

