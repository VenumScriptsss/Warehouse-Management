from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from users.models import UserModel

class productsModel(models.Model):
	#product_id = models.AutoField(verbose_name='id',primary_key=True)
	name         			= models.CharField(verbose_name='Product Name', max_length=50, null=False, unique=True)
	category				= models.CharField(verbose_name='Product Category', max_length=50, default='Other')
	price					= models.IntegerField(verbose_name='Product Price',null=False, default=0)
	sku                 	= models.CharField(max_length=100, unique=True)
	description         	= models.TextField(default="No Description", max_length=150)
	threshold				= models.PositiveIntegerField(default=10)
	is_active           	= models.BooleanField(default=True)

	def __str__(self):
		return self.sku

	class Meta:
		# add ordering by active status
		# ordering = ['date_delivered'] 
		verbose_name = 'product list'
		verbose_name_plural = 'products'


class WarehouseModel(models.Model):
	name 					= models.CharField(max_length=100)
	location 				= models.CharField(max_length=255, blank=True)
	# manager 	= models.ForeignKey(UserModel, on_delete=models.SET_NULL, blank=True, null=True)

	def __str__(self):
	    return self.name



class inventoryModel(models.Model):
	#product_id = models.AutoField(verbose_name='id',primary_key=True)
	warehouse 				= models.ForeignKey(WarehouseModel, on_delete=models.CASCADE, null=True, blank=True)
	product 	    		= models.ForeignKey(productsModel, on_delete=models.CASCADE)
	quantity				= models.IntegerField(verbose_name='Quantity', null=False, default=0)
	expiry_date 			= models.DateField(blank=True, null=True)

	updated_at  			= models.DateField(verbose_name='Updated at ', auto_now= True)

	class Meta:
		ordering = ['updated_at']
		verbose_name = 'Inventory'
		verbose_name_plural = 'Products'



class Inbound(models.Model):
	supplier				= models.CharField(max_length=255)
	reference_number		= models.CharField(unique=True, max_length=100)
	warehouse 				= models.ForeignKey(WarehouseModel, on_delete=models.CASCADE)
	received_date			= models.DateField()
	total_price				= models.DecimalField(null=False, default=0, max_digits=10, decimal_places=2)

	created_at 				= models.DateTimeField(auto_now_add=True)
	created_by 				= models.ForeignKey(UserModel, on_delete=models.SET_NULL, null=True, blank=True)
	def __str__(self):
		return self.reference_number
		


class InboundItem(models.Model):
	inbound 				= models.ForeignKey(Inbound, related_name='items', on_delete=models.CASCADE)
	product 				= models.ForeignKey(productsModel, on_delete=models.CASCADE)
	quantity 				= models.PositiveIntegerField()
    # batch_id = models.CharField(max_length=100, blank=True, null=True)
	expiry_date 			= models.DateField(blank=True, null=True)
	purshased_price			= models.IntegerField(null=False, default=0)

	def __str__(self):
		return self.product.sku
	
class Outbound(models.Model):
	client					= models.CharField(max_length=255)
	reference_number		= models.CharField(unique=True, max_length=100)
	warehouse 				= models.ForeignKey(WarehouseModel, on_delete=models.CASCADE)
	issue_date				= models.DateField()
	total_amount			= models.IntegerField(null=False, default=0)
	created_at 				= models.DateTimeField(auto_now_add=True)
	created_by 				= models.ForeignKey(UserModel, on_delete=models.SET_NULL, null=True, blank=True)

	def __str__(self):
		return self.reference_number
		


class OutboundItem(models.Model):
	outbound 				= models.ForeignKey(Outbound, related_name='items', on_delete=models.CASCADE)
	product 				= models.ForeignKey(productsModel, on_delete=models.CASCADE)
	quantity 				= models.PositiveIntegerField()
    # batch_id = models.CharField(max_length=100, blank=True, null=True)
	def __str__(self):
		return self.product.sku
