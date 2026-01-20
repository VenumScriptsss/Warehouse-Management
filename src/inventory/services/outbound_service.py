from django.db import transaction
from inventory.models import inventoryModel

# @transaction.atomic
# def process_outbound(outbound):
#     for item in outbound.items.select_related("product", "warehouse").all():
#         inventory = Inventory.objects.select_for_update().get(
#             product=item.product,
#             warehouse=item.warehouse
#         )

#         if inventory.quantity < item.quantity:
#             raise ValueError(
#                 f"Insufficient stock for {item.product.sku} "
#                 f"in {item.warehouse.name}"
#             )

#         inventory.quantity -= item.quantity
#         inventory.save()



@transaction.atomic
def process_outbound(outbound):
    for item in outbound.items.select_related("product").all():
        inventory = inventoryModel.objects.select_for_update().get(
            product=item.product,
            warehouse=outbound.warehouse
        )

        if inventory.quantity < item.quantity:
            raise ValueError(
                f"Insufficient stock for {item.product.sku}"
                # f"in {item.warehouse.name}"
            )

        inventory.quantity -= item.quantity

        # If quantity reaches 0, delete the inventory record
        if inventory.quantity == 0:
            inventory.delete()
        else:
            inventory.save()
