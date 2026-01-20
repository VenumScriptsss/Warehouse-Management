from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from users.models import *
from inventory.models import *
from users.activity_logger import log_login, log_logout
from django.contrib.auth.decorators import login_required
from users.decorators import role_required
from django.db.models import Count
from collections import defaultdict
from datetime import datetime, timedelta
from django.utils import timezone

def landing_page(request):
    """Landing page for the warehouse management system"""
    return render(request, 'index.html')

def signin_view(request):
    context = {}
    context["warehouses"] = WarehouseModel.objects.all()
    if request.method == 'POST':
        # Handle form submission
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        role = request.POST.get('role')
        warehouse_id = request.POST.get('warehouse')

        # Basic validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, 'SignIn.html')

        # Create the user with is_active=False (pending admin approval)
        user = UserModel.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            warehouse_id=warehouse_id if warehouse_id else None,
            is_active=False  # Set to False for admin approval
        )

        # Log the user creation activity
        from users.activity_logger import log_create
        log_create(
            user=user,
            request=request,
            model_name='User',
            object_id=user.id,
            username=username,
            email=email,
            role=role,
            status='pending_approval'
        )

        messages.success(request, "Account created successfully! Your account is pending admin approval. You will be able to log in once approved.")
        return redirect('login')

    return render(request, 'SignIn.html', context)

def login_view(request):
    if request.method == 'POST':
        # Handle form submission
        username = request.POST.get('username')
        password = request.POST.get('password')

        # First, try to get the user regardless of active status
        try:
            user = UserModel.objects.get(username=username)

            # Check if password is correct
            if user.check_password(password):
                # Check if user account is active
                if user.is_active:
                    login(request, user)

                    # Log the login activity
                    log_login(user, request)

                    return redirect('home')
                else:
                    messages.error(request, "Your account is pending admin approval. Please contact an administrator.")
            else:
                messages.error(request, "Invalid username or password")
        except UserModel.DoesNotExist:
            messages.error(request, "Invalid username or password")

    return render(request, 'LogIn.html')

@login_required
def logout_view(request):
    """Logout the user and redirect to landing page"""
    if request.user.is_authenticated:
        # Log the logout activity
        log_logout(request.user, request)
        logout(request)
        # messages.info(request, "You have been logged out successfully.")
    return redirect('index')

@login_required
@role_required(['admin', 'manager'])
def activity_reports(request):
    """Show activity reports for admins and managers"""
    # Get all activity reports
    reports = ReportModel.objects.all().order_by('-performed_at')

    # Filter by user if provided
    user_filter = request.GET.get('user')
    if user_filter:
        reports = reports.filter(user_id=user_filter)

    # Filter by activity type if provided
    activity_filter = request.GET.get('activity')
    if activity_filter:
        reports = reports.filter(activity=activity_filter)

    # Filter by date range if provided
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        reports = reports.filter(performed_at__range=[start_date, end_date])

    context = {
        'reports': reports,
        'users': UserModel.objects.all(),
        'activity_types': ReportModel.ACTIVITY_CHOICES,
        'start_date': start_date,
        'end_date': end_date,
        'user_filter': user_filter,
        'activity_filter': activity_filter
    }

    return render(request, 'activity_reports.html', context)

@login_required
@role_required(['admin', 'manager'])
def audit_dashboard(request):
    """
    Audit Dashboard showing visual user activity analysis
    - Visual log of user activity
    - Track most edited items
    - Track frequent stock adjustments
    """
    # Get date range for analysis (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    # 1. User Activity Timeline (last 30 days)
    activity_timeline = ReportModel.objects.filter(
        performed_at__range=[start_date, end_date]
    ).order_by('-performed_at')[:50]  # Last 50 activities

    # Format timeline data
    formatted_timeline = []
    for activity in activity_timeline:
        formatted_timeline.append({
            'timestamp': activity.performed_at,
            'user': activity.user.username if activity.user else 'System',
            'role': activity.user.role if activity.user else 'System',
            'activity': activity.get_activity_display(),
            'object': f"{activity.object_model} #{activity.object_id}" if activity.object_model and activity.object_id else activity.object_model,
            'status': activity.status,
            'ip_address': activity.ip_address
        })

    # 2. Most Edited Items Analysis
    most_edited_items = ReportModel.objects.filter(
        activity='EDIT',
        object_model__in=['Product', 'Inbound', 'Outbound']
    ).values('object_model', 'object_id').annotate(
        edit_count=Count('id')
    ).order_by('-edit_count')[:10]  # Top 10 most edited items

    # Get details for most edited items
    edited_items_details = []
    for item in most_edited_items:
        try:
            if item['object_model'] == 'Product':
                product = productsModel.objects.get(id=item['object_id'])
                edited_items_details.append({
                    'model': 'Product',
                    'name': product.name,
                    'sku': product.sku,
                    'edit_count': item['edit_count'],
                    'object_id': item['object_id']
                })
            elif item['object_model'] == 'Inbound':
                inbound = Inbound.objects.get(id=item['object_id'])
                edited_items_details.append({
                    'model': 'Inbound',
                    'name': f"Inbound {inbound.reference_number}",
                    'supplier': inbound.supplier,
                    'edit_count': item['edit_count'],
                    'object_id': item['object_id']
                })
            elif item['object_model'] == 'Outbound':
                outbound = Outbound.objects.get(id=item['object_id'])
                edited_items_details.append({
                    'model': 'Outbound',
                    'name': f"Outbound {outbound.reference_number}",
                    'client': outbound.client,
                    'edit_count': item['edit_count'],
                    'object_id': item['object_id']
                })
        except:
            # Handle case where object no longer exists
            edited_items_details.append({
                'model': item['object_model'],
                'name': f"Deleted {item['object_model']} #{item['object_id']}",
                'edit_count': item['edit_count'],
                'object_id': item['object_id']
            })

    # 3. Frequent Stock Adjustments Analysis
    # Look for patterns in inventory adjustments
    stock_adjustments = ReportModel.objects.filter(
        activity__in=['CREATE', 'EDIT'],
        object_model='inventoryModel'
    ).order_by('-performed_at')[:20]

    adjustment_patterns = []
    adjustment_by_user = defaultdict(int)
    adjustment_by_product = defaultdict(int)

    for adjustment in stock_adjustments:
        # Count adjustments by user
        user_key = adjustment.user.username if adjustment.user else 'System'
        adjustment_by_user[user_key] += 1

        # Count adjustments by product (if available in details)
        if adjustment.details and 'product_id' in adjustment.details:
            product_id = adjustment.details['product_id']
            adjustment_by_product[product_id] += 1

    # Convert to lists for template
    user_adjustment_counts = [{'user': user, 'count': count} for user, count in adjustment_by_user.items()]
    product_adjustment_counts = []

    # Get product details for frequently adjusted products
    for product_id, count in adjustment_by_product.items():
        try:
            product = productsModel.objects.get(id=product_id)
            product_adjustment_counts.append({
                'product': product.name,
                'sku': product.sku,
                'count': count,
                'product_id': product_id,
                'count_10':count*10
            })
        except:
            product_adjustment_counts.append({
                'product': f"Deleted Product #{product_id}",
                'count': count,
                'product_id': product_id
            })

    # 4. User Activity Summary
    user_activity_summary = ReportModel.objects.filter(
        performed_at__range=[start_date, end_date]
    ).values('user__username', 'user__role').annotate(
        total_activities=Count('id')
    ).order_by('-total_activities')[:5]

    # 5. Activity Type Distribution
    activity_type_distribution = ReportModel.objects.filter(
        performed_at__range=[start_date, end_date]
    ).values('activity').annotate(
        count=Count('id')
    ).order_by('-count')

    context = {
        'user': request.user,
        'activity_timeline': formatted_timeline,
        'most_edited_items': edited_items_details,
        'user_adjustment_counts': user_adjustment_counts,
        'product_adjustment_counts': product_adjustment_counts,
        'user_activity_summary': user_activity_summary,
        'activity_type_distribution': activity_type_distribution,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d')
    }

    return render(request, 'audit_dashboard.html', context)

@login_required
@role_required(['admin', 'manager'])
def admin_control_panel(request):
    """
    Admin Control Panel for managing user accounts
    - View all users with their status
    - Filter by active/inactive status
    - Activate/deactivate users
    """
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')

    # Base queryset
    users = UserModel.objects.all().order_by('-date_joined')

    # Apply filters
    if status_filter != 'all':
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)

    if search_query:
        users = users.filter(
            models.Q(username__icontains=search_query) |
            models.Q(email__icontains=search_query)
        )

    # Handle activation/deactivation actions
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')

        if action and user_id:
            try:
                user = UserModel.objects.get(id=user_id)

                if action == 'activate':
                    user.is_active = True
                    user.save()

                    # Log activation
                    from users.activity_logger import log_create
                    log_create(
                        user=request.user,
                        request=request,
                        model_name='User',
                        object_id=user.id,
                        username=user.username,
                        action='activate',
                        status='activated'
                    )

                    messages.success(request, f"User {user.username} has been activated successfully.")

                elif action == 'deactivate':
                    user.is_active = False
                    user.save()

                    # Log deactivation
                    from users.activity_logger import log_create
                    log_create(
                        user=request.user,
                        request=request,
                        model_name='User',
                        object_id=user.id,
                        username=user.username,
                        action='deactivate',
                        status='deactivated'
                    )

                    messages.success(request, f"User {user.username} has been deactivated successfully.")

            except UserModel.DoesNotExist:
                messages.error(request, "User not found.")

        return redirect('admin-control-panel')

    context = {
        'users': users,
        'status_filter': status_filter,
        'search_query': search_query,
        'active_users_count':users.filter(is_active=True).count(),
        'none_active_users_count':users.filter(is_active=False).count(),
        'user': request.user
    }

    return render(request, 'admin_control_panel.html', context)
