from django.contrib import admin
from .models import Notebook, Page, Remainder, Activity, StickyNotes, SharedNotebook, SubPage, Todo, TodoGroup

@admin.register(Notebook)
class NotebookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_favourite', 'is_shared', 'is_public', 'created_at', 'updated_at')
    list_filter = ('is_favourite', 'is_shared', 'is_public', 'created_at', 'updated_at')
    search_fields = ('title', 'body', 'author__user__first_name', 'author__user__last_name', 'author__user__id')

@admin.register(SharedNotebook)
class SharedNotebookAdmin(admin.ModelAdmin):
    list_display = ('notebook', 'owner', 'is_notebook_public','shared_at', 'can_edit', 'shareable_link')
    list_filter = ('shared_at', 'can_edit','notebook__is_favourite', 'notebook__is_shared', 'notebook__is_public')
    search_fields = ('notebook__title', 'owner__user__first_name', 'owner__user__last_name', 'owner__user__id')
    ordering = ('-shared_at',)

    def is_notebook_public(self, obj):
        return obj.notebook.is_public

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'notebook', 'order', 'created_at', 'updated_at')
    list_filter = ('notebook__is_favourite', 'created_at', 'updated_at')
    search_fields = ('title', 'body', 'notebook__title', 'notebook__body', 'notebook__author__user__first_name', 'notebook__author__user__last_name', 'notebook__author__user__id')
    ordering = ('-created_at','-updated_at')

@admin.register(SubPage)
class SubPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'page', 'notebook', 'created_at', 'updated_at')
    list_filter = ('notebook__is_favourite', 'created_at', 'updated_at')
    search_fields = ('title', 'body', 'page__title', 'page__body', 'notebook__title', 'notebook__body', 'notebook__author__user__first_name', 'notebook__author__user__last_name', 'notebook__author__user__id')
    ordering = ('-created_at','-updated_at')

@admin.register(Remainder)
class RemainderAdmin(admin.ModelAdmin):
    list_display = ('title', 'alert_time', 'is_over', 'is_completed', 'created_at', 'updated_at')
    list_filter = ('is_over', 'is_completed', 'created_at')
    search_fields = ('title', 'body', 'author__user__first_name', 'author__user__last_name','author__user__id')
    ordering = ('-created_at','-updated_at')

@admin.register(StickyNotes)
class StickyNotesAdmin(admin.ModelAdmin):
    list_display = ('title', 'body', 'created_at', 'updated_at')
    search_fields = ('title', 'body', 'author__user__first_name', 'author__user__last_name','author__user__id')
    list_filter = ('created_at', 'updated_at')
    ordering = ('-created_at','-updated_at')

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at', 'author')
    search_fields = ('title', 'body', 'author__user__first_name', 'author__user__last_name','author__user__id')
    list_filter = ('created_at', 'updated_at')
    ordering = ('-created_at','-updated_at')

@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_completed', 'completed_at','created_at', 'updated_at', 'author')
    list_filter = ('is_completed', 'created_at', 'updated_at','completed_at')
    search_fields = ('title', 'author__user__first_name', 'author__user__last_name', 'author__user__id')
    ordering = ('-created_at', '-updated_at')

@admin.register(TodoGroup)
class TodoGroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at', 'author')
    search_fields = ('title', 'author__user__first_name', 'author__user__last_name', 'author__user__id')
    list_filter = ('created_at', 'updated_at')
    ordering = ('-created_at', '-updated_at')