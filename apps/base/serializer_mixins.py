"""
Mixin classes for Django REST Framework serializers.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


class ModelCleanValidationMixin:
    """
    Mixin to call model's full_clean() method during serializer validation.
    
    This ensures that model-level validation (clean() method) is executed
    and any ValidationErrors are properly caught and converted to DRF format.
    
    Usage:
        class MySerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
            class Meta:
                model = MyModel
                fields = '__all__'
    """
    
    def validate(self, attrs):
        """
        Call parent validate, then run model's full_clean() for create/update.
        """
        attrs = super().validate(attrs)
        
        # Get the model instance
        if self.instance:
            # Update case - apply attrs to existing instance
            instance = self.instance
            for attr, value in attrs.items():
                setattr(instance, attr, value)
        else:
            # Create case - build new instance
            ModelClass = self.Meta.model
            instance = ModelClass(**attrs)
        
        # Run model validation
        try:
            instance.full_clean(exclude=self._get_validation_exclusions())
        except DjangoValidationError as exc:
            # Convert Django ValidationError to DRF ValidationError
            if hasattr(exc, 'message_dict'):
                # Field-specific errors
                raise serializers.ValidationError(exc.message_dict)
            elif hasattr(exc, 'messages'):
                # Non-field errors
                raise serializers.ValidationError({'non_field_errors': exc.messages})
            else:
                raise serializers.ValidationError(str(exc))
        
        return attrs
    
    def _get_validation_exclusions(self):
        """
        Get fields to exclude from model validation.
        Typically includes auto-generated fields and fields not in the serializer.
        """
        exclude = []
        
        # Exclude fields not present in the serializer
        if hasattr(self.Meta, 'model'):
            model_fields = set(self.Meta.model._meta.get_fields())
            serializer_fields = set(self.fields.keys())
            
            for field in model_fields:
                if hasattr(field, 'name') and field.name not in serializer_fields:
                    exclude.append(field.name)
        
        # Exclude auto-generated fields
        exclude.extend(['id', 'created', 'modified', 'created_by', 'modified_by'])
        
        return exclude
