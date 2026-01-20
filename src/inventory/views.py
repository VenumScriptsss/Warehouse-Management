from django.shortcuts import render,redirect
from inventory.models import *
from inventory.forms import *
from inventory.services.inbound_service import *
from inventory.services.outbound_service import *
from users.activity_logger import *
from users.models import ReportModel
import json,os
from django.http import JsonResponse
from django.urls import reverse
from users.decorators import role_required
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict
from django.db.models import Sum, Avg, Q
from django.core.files.storage import default_storage
from inventory.services.excel_import_service import ExcelImportService
from django.shortcuts import get_object_or_404
from django.contrib import messages

@login_required
def homepage(request):
    return render(request, "homepage.html")

@login_required
def inventory(request):
    context = {}
    inventory = inventoryModel.objects.all()
    products_list = productsModel.objects.all()
    warehouses = WarehouseModel.objects.all()

    # Apply filters if present
    category = request.GET.get('category')
    warehouse_id = request.GET.get('warehouse')
    search_query = request.GET.get('search')

    if category:
        inventory = inventory.filter(product__category=category)
    if warehouse_id:
        inventory = inventory.filter(warehouse_id=warehouse_id)
    if search_query:
        inventory = inventory.filter(
            models.Q(product__name__icontains=search_query) |
            models.Q(product__sku__icontains=search_query)
        )
    context['inventory'] = inventory
    context['products_list'] = products_list
    context['category_list'] = list({p.category for p in products_list})
    context['warehouses'] = warehouses
    context['user'] = request.user

    return render(request, 'inventory.html', context)
@login_required
def products(request):
    context = {}
    products_list = productsModel.objects.all()

    # Apply filters if present
    category = request.GET.get('category')
    search_query = request.GET.get('search')

    if category:
        products_list = products_list.filter(category=category)
    if search_query:
        products_list = products_list.filter(
            models.Q(name__icontains=search_query) |
            models.Q(sku__icontains=search_query)
        )

    # Get unique categories for filter dropdown
    categories = productsModel.objects.values_list('category', flat=True).distinct()

    context['products_list'] = products_list
    context['categories'] = categories
    context['user'] = request.user

    return render(request, 'products.html', context)

@login_required
def insights(request):
    return render(request, "insights.html")

@login_required
@role_required(['admin', 'manager'])
def bulk_upload_results(request):
    """Display results of bulk product upload"""
    # Get results from session
    results = request.session.get('bulk_upload_results', {})

    if not results:
        messages.warning(request, "No bulk upload results found.")
        return redirect('inv_addProd')

    context = {
        'success_count': results.get('success_count', 0),
        'error_count': results.get('error_count', 0),
        'total_processed': results.get('success_count', 0) + results.get('error_count', 0),
        'errors': results.get('errors', []),
        'processed_at': results.get('processed_at', timezone.now().isoformat()),
        'user': request.user
    }

    # Clear the session data after displaying
    if 'bulk_upload_results' in request.session:
        del request.session['bulk_upload_results']

    return render(request, 'bulk_upload_results.html', context)

@login_required
@role_required(['admin', 'manager'])
def inv_addProd(request):
    context = {}
    if request.POST:
        # Check if this is a bulk upload (XLSX file)
        content_type = request.headers.get('Content-Type', '')
        excel_file = request.FILES.get('excel_file')

        if excel_file and 'multipart/form-data' in content_type:
            # Handle XLSX bulk upload
            try:
                # Save file temporarily
                file_path = default_storage.save(f"temp_file_uploads/bulk_prod_creation_{excel_file.name}", excel_file)

                # Process Excel
                service = ExcelImportService()
                result = service.product_excel_file_process(file_path)

                if not result['success']:
                    os.remove(file_path)
                    messages.error(request, f"Failed to process Excel file: {result.get('error', 'Unknown error')}")
                    return render(request, 'add-product.html', context)

                # Create products in bulk
                products_to_create = []
                created_count = 0
                error_messages = []

                # Log errors if any
                for error in result['errors']:
                    error_messages.append(f"Row {error['row']}: {error.get('error', 'Unknown error')}")

                # Prepare products for bulk creation
                for product_data in result['products']:
                    products_to_create.append(productsModel(**product_data))

                # Bulk create products
                if products_to_create:
                    created_products = productsModel.objects.bulk_create(products_to_create)
                    created_count = len(created_products)

                    # Log each created product
                    for product in created_products:
                        log_create(
                            user=request.user,
                            request=request,
                            model_name='Product',
                            object_id=product.id,
                            sku=product.sku,
                            name=product.name,
                            category=product.category,
                            price=str(product.price)
                        )

                # Clean up
                os.remove(file_path)

                # Prepare success message
                success_message = f"Successfully created {created_count} products"
                if result['errors']:
                    success_message += f", {len(result['errors'])} products failed to create"
                    for error_msg in error_messages:
                        messages.warning(request, error_msg)

                messages.success(request, success_message)

                # Store results in session for display on results page
                request.session['bulk_upload_results'] = {
                    'success_count': created_count,
                    'error_count': len(result['errors']),
                    'errors': result['errors'],
                    'processed_at': timezone.now().isoformat()
                }

                return redirect('bulk_upload_results')

            except Exception as e:
                print(f"Excel processing error: {e}")
                messages.error(request, f'Excel processing error: {str(e)}')
                return render(request, 'add-product.html', context)

        else:
            # Handle regular form submission
            form = createProductFrom(request.POST)

            if form.is_valid():
                product = form.save()

                # Log the product creation
                log_create(
                    user=request.user,
                    request=request,
                    model_name='Product',
                    object_id=product.id,
                    sku=product.sku,
                    name=product.name,
                    category=product.category,
                    price=str(product.price)
                )

                messages.success(request, f"Product '{product.name}' created successfully!")
                return redirect('products')
            else:
                print("[ERROR] form is not valid:", form.errors)
                messages.error(request, "Please correct the errors in the form")
    return render(request, 'add-product.html', context)

@login_required
@role_required(['admin', 'manager'])
def edit_product(request, product_id):
    product = productsModel.objects.get(id=product_id)

    if request.method == 'POST':
        form = createProductFrom(request.POST, instance=product)

        if form.is_valid():
            updated_product = form.save()

            # Log the product update
            log_create(
                user=request.user,
                request=request,
                model_name='Product',
                object_id=updated_product.id,
                sku=updated_product.sku,
                name=updated_product.name,
                category=updated_product.category,
                price=str(updated_product.price)
            )

            return redirect('products')
        else:
            print("[ERROR] form is not valid:", form.errors)
    else:
        # For GET request, populate form with existing product data
        form = createProductFrom(instance=product)

    context = {
        'form': form,
        'product': product,
        'user': request.user
    }
    return render(request, 'edit-product.html', context)

@login_required
@role_required(['admin', 'manager'])
def delete_product(request, product_id):
    product = productsModel.objects.get(id=product_id)

    if request.method == 'POST':
        # Log the product deletion
        log_create(
            user=request.user,
            request=request,
            model_name='Product',
            object_id=product.id,
            sku=product.sku,
            name=product.name,
            category=product.category,
            price=str(product.price)
        )

        # Delete the product
        product.delete()

        return redirect('products')

    context = {
        'product': product,
        'user': request.user
    }
    return render(request, 'delete-product.html', context)


@login_required
def inv_inboundProcess(request):
    context = {}
    products_list = productsModel.objects.all()
    warehouses = WarehouseModel.objects.all()
    context['products_list'] = products_list
    context['warehouses'] = warehouses

    if request.method == 'POST':
        # Check if this is a FormData submission (XLSX upload) or JSON submission
        content_type = request.headers.get('Content-Type', '')

        if 'multipart/form-data' in content_type:
            # Handle XLSX upload with FormData
            print("Processing FormData (XLSX upload)")

            # Get form data
            is_excel_upload = request.POST.get('is_excel_upload', 'false')
            excel_file = request.FILES.get('excel_file')

            if is_excel_upload == 'true' and excel_file:
                # Process Excel file
                try:
                    # Save file temporarily
                    file_path = default_storage.save('temp_inbound.xlsx', excel_file)

                    # Process Excel
                    service = ExcelImportService()
                    result = service.inbound_excel_file_process(file_path)

                    if not result['success']:
                        os.remove(file_path)
                        return JsonResponse({
                            'success': False,
                            'error': 'Failed to process Excel file: ' + (result.get('error', 'Unknown error'))
                        }, status=400)

                    # Get other form data
                    data = {
                        'warehouse': request.POST.get('warehouse'),
                        'supplier': request.POST.get('supplier'),
                        'ref_num': request.POST.get('ref_num'),
                        'total_price': request.POST.get('total_price'),
                        'inbound_date': request.POST.get('inbound_date'),
                        'is_excel_upload': 'true',
                        'items': result['data']['items']
                    }

                    # Clean up
                    os.remove(file_path)

                except Exception as e:
                    print(f"Excel processing error: {e}")
                    return JsonResponse({
                        'success': False,
                        'error': f'Excel processing error: {str(e)}'
                    }, status=500)

            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid XLSX upload'
                }, status=400)

        else:
            # Handle JSON submission (regular form)
            print("Processing JSON data")
            try:
                data = json.loads(request.body)
                print("Incoming JSON data:")
                print(data)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid JSON data'
                }, status=400)

        # Create inbound record (common for both JSON and FormData)
        try:
            inbound = Inbound.objects.create(
                warehouse_id=data['warehouse'],
                supplier=data['supplier'],
                reference_number=data['ref_num'],
                total_price=data['total_price'],
                received_date=data['inbound_date'],
                created_by = request.user
            )
            total_price_cpt = 0

            for item in data['items']:
                total_price_cpt += float(item['unit_price'])

                InboundItem.objects.create(
                    inbound=inbound,
                    product_id=item['product'],
                    quantity=item['quantity'],
                    expiry_date=item['expiry_date'],
                    purshased_price=item['unit_price']
                )
            if inbound.total_price == 0:
                inbound.total_price = total_price_cpt
                inbound.save()

            process_inbound(inbound)

            # Log the inbound creation
            log_create(
                user=request.user,
                request=request,
                model_name='Inbound',
                object_id=inbound.id,
                supplier=data['supplier'],
                reference_number=data['ref_num'],
                total_price=str(data['total_price']),
                received_date=str(data['inbound_date']),
                items_count=len(data['items'])
            )

            # Return JSON response with redirect URL
            return JsonResponse({
                'success': True,
                'message': f"Inbound {data['ref_num']} was registered successfully",
            })

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    # For GET requests, render the form
    return render(request, 'register-inbound.html', context)

@login_required
def inv_outboundProcess(request):
    context = {}
    products_list = productsModel.objects.all()
    warehouses = WarehouseModel.objects.all()

    context['products_list'] = products_list
    context['warehouses'] = warehouses
    if request.method == 'POST':
        # Check if this is a FormData submission (XLSX upload) or JSON submission
        content_type = request.headers.get('Content-Type', '')

        if 'multipart/form-data' in content_type:
            # Handle XLSX upload with FormData
            print("Processing FormData (XLSX upload)")

            # Get form data
            is_excel_upload = request.POST.get('is_excel_upload', 'false')
            excel_file = request.FILES.get('excel_file')

            if is_excel_upload == 'true' and excel_file:
                # Process Excel file
                try:
                    # Save file temporarily
                    file_path = default_storage.save('temp_outbound.xlsx', excel_file)

                    # Process Excel
                    service = ExcelImportService()
                    result = service.outbound_excel_file_process(file_path)

                    if not result['success']:
                        os.remove(file_path)
                        return JsonResponse({
                            'success': False,
                            'error': 'Failed to process Excel file: ' + (result.get('error', 'Unknown error'))
                        }, status=400)

                    # Get other form data
                    data = {
                        'warehouse': request.POST.get('warehouse'),
                        'client': request.POST.get('client'),
                        'ref_num': request.POST.get('ref_num'),
                        'outbound_date': request.POST.get('outbound_date'),
                        'is_excel_upload': 'true',
                        'items': result['data']['items']
                    }

                    # Clean up
                    os.remove(file_path)

                except Exception as e:
                    print(f"Excel processing error: {e}")
                    return JsonResponse({
                        'success': False,
                        'error': f'Excel processing error: {str(e)}'
                    }, status=500)

            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid XLSX upload'
                }, status=400)

        else:
            # Handle JSON submission (regular form)
            print("Processing JSON data")
            try:
                data = json.loads(request.body)
                print("Incoming JSON data:")
                print(data)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid JSON data'
                }, status=400)

        # Create outbound record (common for both JSON and FormData)
        try:
            outbound = Outbound.objects.create(
                warehouse_id=data['warehouse'],
                client=data['client'],
                reference_number=data['ref_num'],
                issue_date=data['outbound_date'],
                created_by = request.user
            )

            for item in data['items']:
                OutboundItem.objects.create(
                    outbound=outbound,
                    product_id=item['product'],
                    quantity=item['quantity'],
                )

            process_outbound(outbound)

            # Log the outbound creation
            log_create(
                user=request.user,
                request=request,
                model_name='Outbound',
                object_id=outbound.id,
                client=data['client'],
                reference_number=data['ref_num'],
                issue_date=str(data['outbound_date']),
                items_count=len(data['items'])
            )

            # Return JSON response with redirect URL
            return JsonResponse({
                'success': True,
                'message': f"Outbound {data['ref_num']} was registered successfully",
            })

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    # For GET requests, render the form
    return render(request, 'register-outbound.html', context)

@login_required
def main_dashboard_view(request):
    """
    Dashboard view showing inventory stats, recent activity, and transaction charts
    """
    # Get current date for today's transactions
    today = timezone.now().date()

    # 1. Calculate Stats
    # Total inventory items
    total_inventory = sum(inv.quantity for inv in inventoryModel.objects.all())

    # Today's inbound transactions
    todays_inbound = Inbound.objects.filter(created_at__date=today).count()

    # Today's outbound transactions
    todays_outbound = Outbound.objects.filter(created_at__date=today).count()

    # Low stock alerts (products below threshold)
    low_stock_products = []
    for inventory in inventoryModel.objects.all():
        if inventory.quantity < inventory.product.threshold:
            low_stock_products.append({
                'product': inventory.product,
                'current_stock': inventory.quantity,
                'threshold': inventory.product.threshold,
                'shortage' : inventory.product.threshold - inventory.quantity,
                'warehouse': inventory.warehouse
            })

    # 2. Recent Activity Stream (focused on inbounds, outbounds, and product operations)
    recent_activities = ReportModel.objects.filter(
        activity__in=['CREATE', 'EDIT', 'DELETE'],
        object_model__in=['Inbound', 'Outbound', 'Product']
    ).order_by('-performed_at')[:10]

    # Format activity messages
    formatted_activities = []
    for activity in recent_activities:
        if activity.object_model == 'Inbound':
            message = f"Created inbound {activity.details.get('reference_number', 'N/A')} from {activity.details.get('supplier', 'Unknown')}"
        elif activity.object_model == 'Outbound':
            message = f"Created outbound {activity.details.get('reference_number', 'N/A')} for {activity.details.get('client', 'Unknown')}"
        elif activity.object_model == 'Product':
            if activity.activity == 'CREATE':
                message = f"Created product {activity.details.get('name', 'N/A')} (SKU: {activity.details.get('sku', 'N/A')})"
            elif activity.activity == 'EDIT':
                message = f"Edited product {activity.details.get('name', 'N/A')} (SKU: {activity.details.get('sku', 'N/A')})"
            elif activity.activity == 'DELETE':
                message = f"Deleted product {activity.details.get('name', 'N/A')} (SKU: {activity.details.get('sku', 'N/A')})"

        formatted_activities.append({
            'user': activity.user.username if activity.user else 'System',
            'activity': activity.get_activity_display(),
            'message': message,
            'timestamp': activity.performed_at,
            'status': activity.status
        })

    # 3. Daily Transaction Volume Chart (last 30 days)
    end_date = today
    start_date = today - timedelta(days=29)

    # Initialize date range
    date_range = [start_date + timedelta(days=i) for i in range(30)]
    transaction_data = {date: {'inbound': 0, 'outbound': 0} for date in date_range}

    # Get inbound data
    inbound_data = Inbound.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).extra({'date': "date(created_at)"}).values('date').annotate(count=models.Count('id'))

    for item in inbound_data:
        date = item['date']
        if date in transaction_data:
            transaction_data[date]['inbound'] = item['count']

    # Get outbound data
    outbound_data = Outbound.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).extra({'date': "date(created_at)"}).values('date').annotate(count=models.Count('id'))

    for item in outbound_data:
        date = item['date']
        if date in transaction_data:
            transaction_data[date]['outbound'] = item['count']

    # Prepare chart data
    chart_labels = [date.strftime('%Y-%m-%d') for date in date_range]
    chart_inbound_data = [transaction_data[date]['inbound'] for date in date_range]
    chart_outbound_data = [transaction_data[date]['outbound'] for date in date_range]

    context = {
        'user': request.user,
        'stats': {
            'total_inventory': total_inventory,
            'todays_inbound': todays_inbound,
            'todays_outbound': todays_outbound,
            'low_stock_count': len(low_stock_products),
            'low_stock_products': low_stock_products
        },
        'recent_activities': formatted_activities,
        'chart_data': {
            'labels': chart_labels,
            'inbound_data': chart_inbound_data,
            'outbound_data': chart_outbound_data
        }
    }

    return render(request, 'dashboard.html', context)

@login_required
@role_required(['admin', 'manager'])
def inventory_valuation_view(request):
    """
    Inventory Valuation Dashboard
    - Track product cost by average
    - Show total stock valuation per product category
    """
    # Calculate average cost for each product
    product_average_costs = {}

    # Get all inbound items to calculate average purchase price
    inbound_items = InboundItem.objects.values('product').annotate(
        total_cost=Sum('purshased_price'),
        total_quantity=Sum('quantity')
    )

    # Calculate average cost per product
    for item in inbound_items:
        product_id = item['product']
        total_cost = item['total_cost'] or 0
        total_quantity = item['total_quantity'] or 1  # Avoid division by zero

        average_cost = total_cost / total_quantity
        product_average_costs[product_id] = average_cost

    # Get current inventory with product details
    inventory_items = inventoryModel.objects.select_related('product').all()

    # Calculate individual product valuations
    product_valuations = []
    total_inventory_value = 0

    for inventory in inventory_items:
        product = inventory.product
        product_id = product.id
        quantity = inventory.quantity

        # Get average cost for this product
        average_cost = product_average_costs.get(product_id, 0)

        # Calculate valuation
        product_value = average_cost * quantity
        total_inventory_value += product_value

        product_valuations.append({
            'product': product,
            'sku': product.sku,
            'name': product.name,
            'category': product.category,
            'quantity': quantity,
            'average_cost': average_cost,
            'total_value': product_value,
            'current_price': product.price,
            'potential_value': product.price * quantity
        })

    # Calculate category-based valuations
    category_valuations = defaultdict(lambda: {
        'total_value': 0,
        'total_quantity': 0,
        'products': []
    })
    for valuation in product_valuations:
        category = valuation['category']
        category_valuations[category]['total_value'] += valuation['total_value']
        category_valuations[category]['total_quantity'] += valuation['quantity']
        category_valuations[category]['products'].append(valuation)

    # Convert to list and sort by value (descending)
    sorted_category_valuations = sorted(
        category_valuations.items(),
        key=lambda x: x[1]['total_value'],
        reverse=True
    )

    # Prepare category data for template
    categories_data = []
    for category_name, category_data in sorted_category_valuations:
        categories_data.append({
            'category': category_name,
            'total_value': category_data['total_value'],
            'total_quantity': category_data['total_quantity'],
            'percentage': (category_data['total_value'] / total_inventory_value * 100) if total_inventory_value > 0 else 0,
            'products': category_data['products']
        })

    # Calculate valuation metrics
    valuation_metrics = {
        'total_inventory_value': total_inventory_value,
        'total_potential_value': sum(p['potential_value'] for p in product_valuations),
        'valuation_ratio': (total_inventory_value / sum(p['potential_value'] for p in product_valuations) * 100) if sum(p['potential_value'] for p in product_valuations) > 0 else 0,
        'average_cost_across_inventory': total_inventory_value / sum(p['quantity'] for p in product_valuations) if sum(p['quantity'] for p in product_valuations) > 0 else 0,
        'category_count': len(categories_data)
    }

    context = {
        'user': request.user,
        'product_valuations': product_valuations,
        'category_valuations': categories_data,
        'valuation_metrics': valuation_metrics,
        'last_updated': timezone.now()
    }

    return render(request, 'inventory_valuation.html', context)

@login_required
@role_required(['admin', 'manager'])
def warehouse_management(request):
    """Warehouse management page - list, add, edit, delete warehouses"""
    warehouses = WarehouseModel.objects.all()

    # Handle search/filter
    search_query = request.GET.get('search', '')
    if search_query:
        warehouses = warehouses.filter(
            models.Q(name__icontains=search_query) |
            models.Q(location__icontains=search_query)
        )

    context = {
        'warehouses': warehouses,
        'search_query': search_query,
        'user': request.user
    }
    return render(request, 'warehouse_management.html', context)

@login_required
@role_required(['admin', 'manager'])
def add_warehouse(request):
    """Add a new warehouse"""
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            warehouse = form.save()

            # Log the warehouse creation
            log_create(
                user=request.user,
                request=request,
                model_name='Warehouse',
                object_id=warehouse.id,
                name=warehouse.name,
                location=warehouse.location
            )

            messages.success(request, f"Warehouse '{warehouse.name}' added successfully!")
            return redirect('warehouse-management')
    else:
        form = WarehouseForm()

    context = {
        'form': form,
        'user': request.user
    }
    return render(request, 'add_warehouse.html', context)

@login_required
@role_required(['admin', 'manager'])
def edit_warehouse(request, warehouse_id):
    """Edit an existing warehouse"""
    warehouse = get_object_or_404(WarehouseModel, id=warehouse_id)

    if request.method == 'POST':
        form = WarehouseForm(request.POST, instance=warehouse)
        if form.is_valid():
            updated_warehouse = form.save()

            # Log the warehouse update
            log_create(
                user=request.user,
                request=request,
                model_name='Warehouse',
                object_id=updated_warehouse.id,
                name=updated_warehouse.name,
                location=updated_warehouse.location
            )

            messages.success(request, f"Warehouse '{updated_warehouse.name}' updated successfully!")
            return redirect('warehouse-management')
    else:
        form = WarehouseForm(instance=warehouse)

    context = {
        'form': form,
        'warehouse': warehouse,
        'user': request.user
    }
    return render(request, 'edit_warehouse.html', context)

@login_required
@role_required(['admin', 'manager'])
def delete_warehouse(request, warehouse_id):
    """Delete a warehouse"""
    warehouse = get_object_or_404(WarehouseModel, id=warehouse_id)

    if request.method == 'POST':
        # Log the warehouse deletion
        log_create(
            user=request.user,
            request=request,
            model_name='Warehouse',
            object_id=warehouse.id,
            name=warehouse.name,
            location=warehouse.location
        )

        warehouse.delete()
        messages.success(request, f"Warehouse '{warehouse.name}' deleted successfully!")
        return redirect('warehouse-management')

    context = {
        'warehouse': warehouse,
        'user': request.user
    }
    return render(request, 'delete_warehouse.html', context)

def permission_denied_view(request, exception=None):
    """Custom 403 Forbidden page"""
    return render(request, 'forbidden.html', status=403)

def login_required_view(request):
    """Custom login required page"""
    return render(request, 'login_required.html', status=401)
