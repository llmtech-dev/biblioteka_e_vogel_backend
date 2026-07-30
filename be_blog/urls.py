# be_blog/urls.py
# ZËVENDËSO — shton api/users/

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/',         include('user_api.urls')),       # ← SHTUAR
    path('api/books/',         include('books_api.urls')),
    path('api/quizzes/',       include('quizes_api.urls')),
    path('api/notifications/', include('notifications_api.urls')),
    path('_nested_admin/',     include('nested_admin.urls')),
]

# E shkeputur qellimisht nga settings.DEBUG: /media/ permban permbajtje
# publike (kopertina/PDF librash) qe duhet aksesueshme edhe kur DEBUG=False
# ne prodhim (p.sh. skedare te vjetra te ngarkuar lokalisht para se
# Cloudinary te behej i detyrueshem — shih books_api/serializers.py).
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)