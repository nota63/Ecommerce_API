from django.db import models
from django.contrib.auth.models import User
# Create your models here.



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,null=True,blank=True)
    full_name = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.full_name or self.user.email