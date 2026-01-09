from django.db import models
from django.core.exceptions import ValidationError

from apps.notifications.models._base import BaseUniqueNameModel

from apps.notifications.validators import (
    validate_template, 
    validate_template_uniqueness
)


class Variable(BaseUniqueNameModel):
    class Meta:
        verbose_name = 'Змінна'
        verbose_name_plural = 'Змінні'
        ordering = ['title']


class Channel(BaseUniqueNameModel):
    allowed_tags = models.JSONField(
        default=list,
        verbose_name='Дозволені HTML теги'
    )
    
    class Meta:
        verbose_name = 'Канал'
        verbose_name_plural = 'Канали'
        ordering = ['title']


class NotificationType(BaseUniqueNameModel):
    title = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Назва типу'
    )
    variables = models.ManyToManyField(
        Variable,
        related_name='notification_types',
        verbose_name='Змінні',
        blank=True
    )
    channels = models.ManyToManyField(
        Channel,
        related_name='notification_types',
        verbose_name='Канали',
        blank=True
    )
    is_custom = models.BooleanField(
        default=True,
        verbose_name='Кастомний тип'
    )
    
    @property
    def variable_names(self):
        "Return list of active variable names"
        return list(self.variables.filter(is_active=True).values_list('title', flat=True))

    def clean(self):
        super().clean()
        # Check channels only if object is already saved (has pk)
        # For new objects, channels will be checked after save
        if self.pk and not self.channels.exists():
            raise ValidationError({
                'channels': 'At least one channel is required'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Тип нотифікації'
        verbose_name_plural = 'Типи нотифікацій'
        ordering = ['title']


class NotificationTemplate(BaseUniqueNameModel):
    notification_type = models.ForeignKey(
        NotificationType,
        on_delete=models.CASCADE,
        related_name='templates',
        verbose_name='Тип нотифікації'
    )
    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name='templates',
        verbose_name='Канал'
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Назва шаблону',
        verbose_name='Назва'
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text='Заголовок',
        verbose_name='Заголовок'
    )
    html = models.TextField(
        help_text='HTML шаблон',
        verbose_name='HTML шаблон'
    )

    class Meta:
        verbose_name = 'Шаблон нотифікації'
        verbose_name_plural = 'Шаблони нотифікацій'
        ordering = ['notification_type', 'channel']

    def __str__(self):
        name = self.name or self.notification_type.title
        return f'{name} ({self.channel.title})'

    def clean(self):
        if self.notification_type.is_custom and not self.name:
            raise ValidationError({
                'name': 'Name is required'
            })
        
        if self.channel.title.lower() in ['telegram', 'viber'] and self.title:
            raise ValidationError({
                'title': 'Title is not allowed for telegram and viber channels'
            })
        
        validate_template(
            self.html, 
            self.channel, 
            self.notification_type.variable_names,
            is_custom=self.notification_type.is_custom
        )
        
        validate_template_uniqueness(self)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)