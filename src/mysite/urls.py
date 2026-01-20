"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from inventory.views import *
from users.views import *
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing_page, name='index'),
    path('login/', login_view, name='login'),
    path('signin/', signin_view, name='signin'),
    path('logout/', logout_view, name='logout'),
    path('home/', homepage, name='home'),
    path('login-required/', login_required_view, name='login-required'),
    
    path('home/inventory/', inventory, name= 'inventory'),
    path('home/inventory/register-inbound', inv_inboundProcess, name= 'inventory-regInbound'),
    path('home/inventory/register-outbound', inv_outboundProcess, name= 'inventory-regOutbound'),
    
    path('home/products/', products, name= 'products'),
    path('home/products/add-product', inv_addProd, name= 'inventory-addProd'),
    path('home/products/bulk-upload-results/', bulk_upload_results, name='bulk_upload_results'),
    path('home/products/edit/<int:product_id>/', edit_product, name='edit-product'),
    path('home/products/delete/<int:product_id>/', delete_product, name='delete-product'),
    
    path('home/admin-control-panel/', admin_control_panel, name='admin-control-panel'),
    path('home/admin-control-panel/warehouse-management/', warehouse_management, name='warehouse-management'),
    path('home/admin-control-panel/warehouse-management/add/', add_warehouse, name='add-warehouse'),
    path('home/admin-control-panel/warehouse-management/edit/<int:warehouse_id>/', edit_warehouse, name='edit-warehouse'),
    path('home/admin-control-panel/warehouse-management/delete/<int:warehouse_id>/', delete_warehouse, name='delete-warehouse'),

    path('home/insights/', insights, name= 'insights'),
    path('home/insights/main-dashboard/', main_dashboard_view, name='main-dashboard'),
    path('home/insights/reports/', activity_reports, name='activity-reports'),
    path('home/insights/audit-dashboard/', audit_dashboard, name='audit-dashboard'),
    path('home/insights/inventory-valuation', inventory_valuation_view, name='inventory-valuation'),
]
