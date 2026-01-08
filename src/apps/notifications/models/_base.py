from django.db import models

# Create your models here.
class BaseUniqueNameModel(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name='Назва',
        unique=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата створення'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата оновлення'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активний'
    )

    def __str__(self):
        return self.title

    class Meta:
        abstract = True
