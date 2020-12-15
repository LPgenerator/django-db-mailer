from __future__ import absolute_import

from rest_framework import permissions, status
from rest_framework.fields import IntegerField
from rest_framework.response import Response
from rest_framework.serializers import (ModelSerializer, Serializer,
                                        ValidationError)
from rest_framework.viewsets import ModelViewSet

from dbmail.models import MailSubscription


# Fields
class HexIntegerField(IntegerField):
    """
    Store an integer represented as a hex string of form "0x01".
    """

    def to_internal_value(self, data):
        # validate hex string and convert it to the unsigned
        # integer representation for internal use
        try:
            data = int(data, 16) if type(data) != int else data
        except ValueError:
            raise ValidationError("Device ID is not a valid hex number")
        return super(HexIntegerField, self).to_internal_value(data)

    def to_representation(self, value):
        return value


class UniqueRegistrationSerializerMixin(Serializer):
    def validate(self, attrs):
        devices = None
        primary_key = None
        request_method = None

        if self.initial_data.get("address", None):
            if self.instance:
                request_method = "update"
                primary_key = self.instance.id
            else:
                request_method = "create"
        else:
            if self.context["request"].method in ["PUT", "PATCH"]:
                request_method = "update"
                primary_key = self.instance.id
            elif self.context["request"].method == "POST":
                request_method = "create"

        Device = self.Meta.model
        if request_method == "update":
            address = attrs.get("address", self.instance.address)
            devices = Device.objects.filter(address=address) \
                            .exclude(id=primary_key)
        elif request_method == "create":
            devices = Device.objects.filter(address=attrs["address"])

        if devices:
            raise ValidationError({'address': 'This field must be unique.'})
        return attrs


# Serializers
class MailSubscriptionSerializer(UniqueRegistrationSerializerMixin, ModelSerializer):
    class Meta:
        model = MailSubscription
        fields = ("id", "title", "address", "is_enabled")


# Permissions
class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # must be the owner to view the object
        return obj.user == request.user


class AuthorizedMixin(object):
    permission_classes = (permissions.IsAuthenticated, IsOwner)

    def get_queryset(self):
        # filter all devices to only those belonging to the current user
        return self.queryset.filter(user=self.request.user)


# Mixins
class DeviceViewSet(AuthorizedMixin, ModelViewSet):
    queryset = MailSubscription.objects.all()
    serializer_class = MailSubscriptionSerializer
    lookup_field = "address"

    def create(self, request, *args, **kwargs):
        serializer = None
        is_update = False
        from dbmail.defaults import UPDATE_ON_DUPLICATE_REG_ID
        if UPDATE_ON_DUPLICATE_REG_ID and 'address' in request.data:
            instance = self.queryset.model.objects.filter(
                address=request.data['address']).first()
            if instance:
                serializer = self.get_serializer(instance, data=request.data)
                is_update = True
        if not serializer:
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        if is_update:
            self.perform_update(serializer)
            return Response(serializer.data)
        else:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        if self.request.user.is_authenticated():
            serializer.save(user=self.request.user)
        return super(DeviceViewSet, self).perform_create(serializer)

    def perform_update(self, serializer):
        if self.request.user.is_authenticated():
            serializer.save(user=self.request.user)
        return super(DeviceViewSet, self).perform_update(serializer)
