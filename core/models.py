from django.db import models
from django.contrib.auth.models import AbstractUser

import logging

logging.basicConfig(level=logging.DEBUG)

class User(AbstractUser):
    nick_name = models.CharField(max_length=30)

    def __str__(self):
        return self.get_username()

class Page:
    pass


