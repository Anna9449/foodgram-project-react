from django.contrib.auth.models import AbstractUser
from django.db import models

from api.const import (LENGTH_TEXT_OUTPUT, MAX_LENGTH_INPUT,
                       MAX_LENGTH_INPUT_EMAIL)


class FoodgramUser(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    first_name = models.CharField('Имя', max_length=MAX_LENGTH_INPUT)
    last_name = models.CharField('Фамилия', max_length=MAX_LENGTH_INPUT)
    email = models.EmailField('email', max_length=MAX_LENGTH_INPUT_EMAIL,
                              unique=True)

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username[:LENGTH_TEXT_OUTPUT]
