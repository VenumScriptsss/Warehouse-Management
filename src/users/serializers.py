from rest_framework import serializers
from users.models import UserModel
from inventory.models import WarehouseModel

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehouseModel
        fields = ['id', 'name', 'location']

class UserSerializer(serializers.ModelSerializer):
    warehouse = WarehouseSerializer(read_only=True)

    class Meta:
        model = UserModel
        fields = ['id', 'username', 'email', 'role', 'warehouse']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    warehouse_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = UserModel
        fields = ['username', 'email', 'password', 'confirm_password', 'role', 'warehouse_id']
        extra_kwargs = {
            'password': {'write_only': True},
            'confirm_password': {'write_only': True}
        }

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        warehouse_id = validated_data.pop('warehouse_id', None)

        user = UserModel.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'operator')
        )

        if warehouse_id:
            try:
                warehouse = WarehouseModel.objects.get(id=warehouse_id)
                user.warehouse = warehouse
                user.save()
            except WarehouseModel.DoesNotExist:
                pass

        return user
