from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"

class TaskInputSerializer(serializers.Serializer):
    title = serializers.CharField()
    due_date = serializers.DateField()
    importance = serializers.IntegerField(min_value=1, max_value=10)
    estimated_hours = serializers.IntegerField(min_value=1)
    dependencies = serializers.ListField(child=serializers.IntegerField(), required=False)
