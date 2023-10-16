from django.db import models

# Create your models here.
class Photo(models.Model):
    title = models.CharField(max_length=100)
    state = models.IntegerField(default=0)
    user_name = models.CharField(max_length=50)
    result_name = models.CharField(max_length=50)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'photos'
        verbose_name = 'photo'
        verbose_name_plural = 'photos'
