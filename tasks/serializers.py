from rest_framework import serializers
from .models import Task


class TaskInputSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    title = serializers.CharField()
    due_date = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    importance = serializers.IntegerField(required=False, default=5)
    estimated_hours = serializers.IntegerField(required=False, default=1)
    dependencies = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list
    )


class StrategySerializer(serializers.Serializer):
    strategy = serializers.CharField()
    tasks = TaskInputSerializer(many=True)


class TaskOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    title = serializers.CharField()
    due_date = serializers.CharField(required=False, allow_null=True)
    importance = serializers.IntegerField()
    estimated_hours = serializers.IntegerField()
    dependencies = serializers.ListField(child=serializers.IntegerField())
    score = serializers.FloatField()
    explanation = serializers.CharField()


class TaskModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"
