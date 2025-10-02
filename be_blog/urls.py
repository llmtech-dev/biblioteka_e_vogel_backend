from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/books/', include('books_api.urls')),
    path('api/quizzes/', include('quizes_api.urls')),
    path('api/notifications/', include('notifications_api.urls')),
]

# Servo media files në development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)