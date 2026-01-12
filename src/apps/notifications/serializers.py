from rest_framework import serializers
from apps.notifications.models.gradus_models import (
    NotificationType,
    Variable,
    Channel,
    NotificationTemplate
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


class NotificationTypeMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer for nested use"""
    class Meta:
        model = NotificationType
        fields = ['id', 'title', 'is_custom']
        read_only_fields = ['id', 'title', 'is_custom']


class NotificationTemplateReadSerializer(serializers.ModelSerializer):
    notification_type = NotificationTypeMinimalSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)
    
    class Meta:
        model = NotificationTemplate
        fields = ['id', 'notification_type', 'channel', 'name', 'title', 
                 'html', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationTemplateWriteSerializer(serializers.ModelSerializer):
    notification_type = serializers.CharField(help_text='Notification type title')
    channel = serializers.CharField(help_text='Channel title')
    
    class Meta:
        model = NotificationTemplate
        fields = ['id', 'notification_type', 'channel', 'name', 'title', 
                 'html', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_notification_type(self, value):
        try:
            notification_type = NotificationType.objects.get(title=value, is_active=True)
        except NotificationType.DoesNotExist:
            raise serializers.ValidationError(f"Notification type '{value}' not found")
        return notification_type
    
    def validate_channel(self, value):
        try:
            channel = Channel.objects.get(title=value, is_active=True)
        except Channel.DoesNotExist:
            raise serializers.ValidationError(f"Channel '{value}' not found")
        return channel
    
    def validate(self, attrs):
        notification_type = attrs.get('notification_type')
        channel = attrs.get('channel')
        
        if notification_type and channel:
            if channel.title.lower() in ['telegram', 'viber'] and attrs.get('title'):
                raise serializers.ValidationError({
                    'title': 'Title is not allowed for telegram and viber channels'
                })
            
            if notification_type.is_custom and not attrs.get('name'):
                raise serializers.ValidationError({
                    'name': 'Name is required for custom notification types'
                })
        
        return attrs
    
    def create(self, validated_data):
        template = NotificationTemplate(**validated_data)
        template.save()
        return template
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class SendNotificationSerializer(serializers.Serializer):
    """Serializer for sending notifications"""
    notification_type = serializers.CharField(required=True, help_text="Notification type title")
    context = serializers.DictField(required=True, help_text="Variables for template rendering")
    recipient = serializers.EmailField(required=True, help_text="Email address of recipient")
    template_name = serializers.CharField(required=False, allow_null=True, help_text="Template name (only for custom types)")
