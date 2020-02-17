import copy
import logging

from django.db import transaction
from django.db.models import Manager, QuerySet
from rest_framework.fields import ModelField

logger = logging.getLogger(__name__)


class ActionLogMixin:
    @staticmethod
    def get_create_log_entity(serializer, instance, action):
        validated_data = copy.copy(serializer.validated_data)
        log_entity = {"pk": instance.pk}
        ModelClass = serializer.Meta.model

        for field_name, field in serializer.fields.items():
            if field.source == "*":
                value = instance
            elif field.source in validated_data:
                value = validated_data.pop(field.source, None)
            else:
                value = getattr(instance, field.source, None)

            if isinstance(field, ModelField):
                log_entity[field_name] = field.to_representation(instance)
            elif isinstance(value, (Manager, QuerySet)):
                log_entity[field_name] = field.to_representation(value.all())
            elif callable(value):
                log_entity[field_name] = field.to_representation(value())
            elif value is not None:
                log_entity[field_name] = field.to_representation(value)
            else:
                log_entity[field_name] = None

        for attr, value in validated_data.items():
            log_entity[attr] = repr(value)

        message = "{} {}".format(ModelClass.__name__, action)
        extra = {"{}.{}".format(ModelClass._meta.app_label, ModelClass.__name__): log_entity}
        return message, extra

    def perform_create(self, serializer):
        with transaction.atomic():
            instance = serializer.save()
            message, extra = self.get_create_log_entity(serializer, instance, "created")
            logger.info(message, extra=extra)

    def perform_update(self, serializer):
        with transaction.atomic():
            instance = serializer.save()
            message, extra = self.get_create_log_entity(serializer, instance, "updated")
            logger.info(message, extra=extra)

    def perform_destroy(self, instance):
        with transaction.atomic():
            msg = {"pk": instance.pk}
            super().perform_destroy(instance)
            logger.info(
                "{} deleted".format(type(instance).__name__),
                extra={"{}.{}".format(instance._meta.app_config.label, type(instance).__name__): msg},
            )
