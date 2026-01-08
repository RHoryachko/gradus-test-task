from django.db import models
from django.core.exceptions import ValidationError

from ._base import BaseUniqueNameModel


class Variable(BaseUniqueNameModel):
    class Meta:
        verbose_name = 'Змінна'
        verbose_name_plural = 'Змінні'
        ordering = ['title']


class Channel(BaseUniqueNameModel):
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

    def clean(self):

        super().clean()
        if not self.channels.exists() and self.pk:
            if not self.channels.all().exists():
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
    html = models.TextField(
        verbose_name='HTML шаблон'
    )

    class Meta:
        verbose_name = 'Шаблон нотифікації'
        verbose_name_plural = 'Шаблони нотифікацій'
        ordering = ['notification_type', 'channel']

    def __str__(self):
        return f'{self.notification_type.title} - {self.channel.title}'