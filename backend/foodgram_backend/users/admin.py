from django.contrib import admin
from .models import MyUser


@admin.register(MyUser)
class MyUserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'username',
        'email',
    )
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')
    list_display_links = ('username',)
