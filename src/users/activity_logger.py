from .models import ReportModel

def log_activity(
    user,
    activity,
    object_model=None,
    object_id=None,
    ip_address=None,
    details=None,
    changes=None,
    status='SUCCESS'
):
    """
    Simple activity logging function

    Args:
        user: UserModel instance
        activity: Activity type (CREATE, EDIT, DELETE, etc.)
        object_model: Name of the model affected (optional)
        object_id: ID of the object affected (optional)
        ip_address: User's IP address (optional)
        details: Additional details as dict (optional)
        changes: Changes made as dict (optional)
        status: Activity status (optional, default: SUCCESS)
    """
    ReportModel.objects.create(
        user=user,
        activity=activity,
        object_model=object_model,
        object_id=object_id,
        ip_address=ip_address,
        details=details,
        changes=changes,
        status=status
    )

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Simple convenience functions
def log_create(user, request, model_name, object_id, **extra_details):
    """Log object creation"""
    log_activity(
        user=user,
        activity='CREATE',
        object_model=model_name,
        object_id=object_id,
        ip_address=get_client_ip(request),
        details=extra_details
    )

def log_edit(user, request, model_name, object_id, **extra_details):
    """Log object editing"""
    log_activity(
        user=user,
        activity='EDIT',
        object_model=model_name,
        object_id=object_id,
        ip_address=get_client_ip(request),
        details=extra_details
    )

def log_delete(user, request, model_name, object_id, **extra_details):
    """Log object deletion"""
    log_activity(
        user=user,
        activity='DELETE',
        object_model=model_name,
        object_id=object_id,
        ip_address=get_client_ip(request),
        details=extra_details
    )

def log_login(user, request):
    """Log user login"""
    log_activity(
        user=user,
        activity='LOGIN',
        ip_address=get_client_ip(request)
    )

def log_logout(user, request):
    """Log user logout"""
    log_activity(
        user=user,
        activity='LOGOUT',
        ip_address=get_client_ip(request)
    )

# def log_view(user, request, view_name):
#     """Log view access"""
#     log_activity(
#         user=user,
#         activity='VIEW',
#         object_model=view_name,
#         ip_address=get_client_ip(request)
#     )

def log_import(user, request, model_name, record_count):
    """Log bulk import"""
    log_activity(
        user=user,
        activity='IMPORT',
        object_model=model_name,
        ip_address=get_client_ip(request),
        details={'records_imported': record_count}
    )

def log_export(user, request, model_name, record_count):
    """Log bulk export"""
    log_activity(
        user=user,
        activity='EXPORT',
        object_model=model_name,
        ip_address=get_client_ip(request),
        details={'records_exported': record_count}
    )
