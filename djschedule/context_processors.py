from django.conf import settings


def google_login(request):
    """Expose whether Google OAuth credentials are configured, so templates can hide the button."""
    return {'google_login_enabled': settings.GOOGLE_LOGIN_ENABLED}
