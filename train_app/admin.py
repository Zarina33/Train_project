from django.contrib import admin
from .models import Train, TrainDetail

@admin.register(Train)
class TrainAdmin(admin.ModelAdmin):
    list_display = ('train_id', 'location', 'direction', 'date', 'time')
    fields = ('train_id', 'location', 'direction', 'date', 'time')  # Поля для редактирования

@admin.register(TrainDetail)
class TrainDetailAdmin(admin.ModelAdmin):
    list_display = ('train', 'serial_number', 'image_link')
    fields = ('train', 'serial_number', 'image_link')  # Поля для редактирования
