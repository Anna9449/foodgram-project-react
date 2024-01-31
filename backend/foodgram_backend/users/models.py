from django.contrib.auth.models import AbstractUser
from django.db import models


class MyUser(AbstractUser):
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    email = models.EmailField('email', max_length=150, unique=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
