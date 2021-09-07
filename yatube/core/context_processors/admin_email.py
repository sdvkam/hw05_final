from django.conf import settings


def admin_email(request):
    return {'admin_email': settings.EMAIL_HOST_USER}
