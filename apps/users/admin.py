# apps/users/admin.py
from django.contrib import admin
from .models import CustomUser, Profile, OTP, OrganizationRole

admin.site.register(CustomUser)
admin.site.register(Profile)
admin.site.register(OTP)
admin.site.register(OrganizationRole)
