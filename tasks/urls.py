from django.urls import path
from .views import (
    analyze_tasks,
    suggest_top_tasks,
    save_tasks,
    get_all_tasks,
    get_today_top_tasks,
    delete_task
)

urlpatterns = [
    path("analyze/", analyze_tasks, name="analyze_tasks"),
    path("suggest/", suggest_top_tasks, name="suggest_top_tasks"),

    path("save/", save_tasks, name="save_tasks"),
    path("all/", get_all_tasks, name="get_all_tasks"),
    path("today/", get_today_top_tasks, name="get_today_top_tasks"),

    path("delete/<int:task_id>/", delete_task, name="delete_task"),
]
