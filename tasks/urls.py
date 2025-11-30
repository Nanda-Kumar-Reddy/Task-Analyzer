from django.urls import path
from .views import (
    AnalyzeTasksView,
    SuggestTasksView,
    SaveTasksView,
    AllTasksView,
    TodayTasksView,
    DeleteTaskView,
)

urlpatterns = [
    path("analyze/", AnalyzeTasksView.as_view()),
    path("suggest/", SuggestTasksView.as_view()),
    path("save/", SaveTasksView.as_view()),
    path("all/", AllTasksView.as_view()),
    path("today/", TodayTasksView.as_view()),
    path("delete/<int:id>/", DeleteTaskView.as_view()),
]
