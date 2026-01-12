from rest_framework import serializers
from apps.notifications.models.gradus_models import (
    NotificationType,
    Variable,
    Channel
)


class VariableSerializer(serializers.ModelSerializer):

    class Meta:
        model = Variable
        fields = ['id', 'title', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChannelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Channel
        fields = ['id', 'title', 'allowed_tags', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationTypeReadSerializer(serializers.ModelSerializer):
    variables = VariableSerializer(many=True, read_only=True)
    channels = ChannelSerializer(many=True, read_only=True)
    variable_names = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationType
        fields = ['id', 'title', 'variables', 'channels', 'is_custom', 
                 'variable_names', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_variable_names(self, obj):
        return obj.variable_names


class NotificationTypeWriteSerializer(serializers.ModelSerializer):
    variables = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
    )
    channels = serializers.ListField(
        child=serializers.CharField(),
        required=True,
    )
    
    class Meta:
        model = NotificationType
        fields = ['id', 'title', 'variables', 'channels', 'is_custom', 
                 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_channels(self, value):
        if not value:
            return value
        
        existing_channels = Channel.objects.filter(title__in=value, is_active=True)
        existing_titles = set(existing_channels.values_list('title', flat=True))
        missing = set(value) - existing_titles
        
        if missing:
            raise serializers.ValidationError(
                f"Channels not found: {', '.join(sorted(missing))}"
            )
        
        return value
    
    def validate_variables(self, value):
        if not value:
            return value
        
        existing_variables = Variable.objects.filter(title__in=value, is_active=True)
        existing_titles = set(existing_variables.values_list('title', flat=True))
        missing = set(value) - existing_titles
        
        if missing:
            raise serializers.ValidationError(
                f"Variables not found: {', '.join(sorted(missing))}"
            )
        
        return value
    
    def create(self, validated_data):
        variable_names = validated_data.pop('variables', [])
        channel_names = validated_data.pop('channels', [])
        
        channel_objs = Channel.objects.filter(title__in=channel_names, is_active=True)
        variable_objs = Variable.objects.filter(title__in=variable_names, is_active=True) if variable_names else []

        notification_type = NotificationType(**validated_data)
        notification_type.save()
        
        notification_type.channels.set(channel_objs)
        if variable_objs:
            notification_type.variables.set(variable_objs)
        
        notification_type.save()
        
        notification_type.refresh_from_db()
        return notification_type
    
    def update(self, instance, validated_data):
        variable_names = validated_data.pop('variables', None)
        channel_names = validated_data.pop('channels', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        if channel_names is not None:
            channel_objs = Channel.objects.filter(title__in=channel_names, is_active=True)
            instance.channels.set(channel_objs)
            instance.save()
        
        if variable_names is not None:
            if variable_names:
                variable_objs = Variable.objects.filter(title__in=variable_names, is_active=True)
                instance.variables.set(variable_objs)
            else:
                instance.variables.clear()
        
        return instance
