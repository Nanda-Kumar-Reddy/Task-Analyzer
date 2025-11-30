from django.contrib import admin
from django.urls import path, include
from .views import frontend

urlpatterns = [
    path("", frontend, name="frontend"),
    path("admin/", admin.site.urls),
    path("api/tasks/", include("tasks.urls")),
]
