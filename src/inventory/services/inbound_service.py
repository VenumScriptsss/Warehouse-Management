# services/inbound_service.py
from django.db import transaction
from inventory.models import inventoryModel

@transaction.atomic
def process_inbound(inbound):
    for item in inbound.items.all():
        inventory, _ = inventoryModel.objects.select_for_update().get_or_create(
            product=item.product,
            warehouse=inbound.warehouse,
            defaults={'quantity': 0}
        )
        inventory.quantity += item.quantity
        inventory.expiry_date = item.expiry_date
        inventory.save()
