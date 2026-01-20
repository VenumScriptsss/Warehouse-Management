from django import forms

from inventory.models import productsModel, WarehouseModel

class createProductFrom(forms.ModelForm):

	class Meta:
		model= productsModel
		# fields= ['name', 'category', 'price', 'sku']
		fields= '__all__'

class WarehouseForm(forms.ModelForm):
    class Meta:
        model = WarehouseModel
        fields = '__all__'
