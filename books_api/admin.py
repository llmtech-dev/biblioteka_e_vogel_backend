from django.contrib import admin
from .models import Book, BookPage, PageElement


class PageElementInline(admin.TabularInline):
    model = PageElement
    extra = 1


class BookPageInline(admin.TabularInline):
    model = BookPage
    extra = 1
    show_change_link = True


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'author']
    inlines = [BookPageInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(BookPage)
class BookPageAdmin(admin.ModelAdmin):
    list_display = ['book', 'page_number']
    list_filter = ['book']
    inlines = [PageElementInline]