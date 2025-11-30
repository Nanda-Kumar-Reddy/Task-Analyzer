from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import frontend

urlpatterns = [
    path("", frontend),
    path("admin/", admin.site.urls),
    path("api/tasks/", include("tasks.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
