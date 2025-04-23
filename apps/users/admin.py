# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Profile, OTP, OrganizationRole

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'email', 'username', 'organization', 'role',
        'is_staff', 'is_active',
    )
    list_filter = (
        'organization', 'role',
        'is_staff', 'is_active',
    )
    fieldsets = (
        (None,               {'fields': ('email', 'password')}),
        ('Personal info',    {'fields': ('username','first_name','last_name')}),
        ('Permissions',      {'fields': (
            'is_active','is_staff','is_superuser',
            'groups','user_permissions'
        )}),
        ('Organization',     {'fields': ('organization','role')}),
        ('Important dates',  {'fields': ('last_login','date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email','username','password1','password2',
                'organization','role'
            )
        }),
    )
    ordering = ('email',)

admin.site.register(Profile)           # Profile one‑to‑one
admin.site.register(OTP)               # OTP model
admin.site.register(OrganizationRole)  # Org‑role junction model
