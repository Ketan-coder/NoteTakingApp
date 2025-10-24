from django.contrib import admin
from .models import Profile, UserPreferences

# Profile Admin
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'firstName', 'lastName', 'email', 'bio')
    
    # Proper search fields with the correct field references using double underscores for related fields
    search_fields = (
        'user__username',   # Searching by username in the related User model
        'firstName',        # Searching by firstName in the Profile model
        'lastName',         # Searching by lastName in the Profile model
        'email',            # Searching by email in the Profile model
        'bio',              # Searching by bio in the Profile model
        'user__email',      # Searching by email in the related User model
        'user__first_name', # Searching by first name in the related User model
        'user__last_name',  # Searching by last name in the related User model
        'user__id',        # Searching by identifier in the related User model
        'id',           # Searching by identifier in the Profile model
    )
    
    list_filter = ('user__is_active',)
    ordering = ('-user__last_login', '-user__date_joined')  # Corrected ordering
    readonly_fields = ('email_confirmation_token',)

admin.site.register(Profile, ProfileAdmin)


# UserPreferences Admin
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ('profile', 'theme', 'text_size', 'biometric_enabled', 'notifications_enabled')
    
    # Search using correct relationships and fields
    search_fields = (
        'profile__user__username',  # Searching by username in related user model
        'profile__firstName',       # Searching by firstName in related profile model
        'profile__lastName',        # Searching by lastName in related profile model
        'profile__email',           # Searching by email in related profile model
    )
    
    list_filter = ('theme', 'text_size', 'biometric_enabled', 'notifications_enabled')
    ordering = ('-profile__user__last_login', '-updated_at')
    readonly_fields = ('updated_at',)

admin.site.register(UserPreferences, UserPreferencesAdmin)
