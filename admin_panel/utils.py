from .models import AdminLog


def log_admin_action(user, action, description, request=None):
    if not user or not user.is_authenticated:
        return
    ip_address = None
    if request is not None:
        ip_address = request.META.get('REMOTE_ADDR')
    AdminLog.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=ip_address,
    )