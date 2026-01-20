from rest_framework import serializers
from apps.base.serializer_mixins import ModelCleanValidationMixin
from apps.branch.models import Branch


class BranchSerializer(ModelCleanValidationMixin, serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'
        extra_kwargs = {
            'tenant': {'read_only': True},
        }
