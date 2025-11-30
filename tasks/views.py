from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import StrategySerializer, TaskOutputSerializer
from .scoring import calculate_task_score

from .models import Task
from .serializers import TaskModelSerializer


class AnalyzeTasksView(APIView):
    def post(self, request):
        serializer = StrategySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        strategy = serializer.validated_data["strategy"]
        tasks = serializer.validated_data["tasks"]

        results = []
        for task in tasks:
            score_data = calculate_task_score(task, strategy=strategy)
            results.append({
                **task,
                "score": score_data["score"],
                "explanation": score_data["explanation"]
            })

        results.sort(key=lambda x: (x["score"], x["importance"]), reverse=True)

        output = TaskOutputSerializer(results, many=True)
        return Response(output.data, status=status.HTTP_200_OK)


class SuggestTasksView(APIView):
    def post(self, request):
        serializer = StrategySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        strategy = serializer.validated_data["strategy"]
        tasks = serializer.validated_data["tasks"]

        results = []
        for task in tasks:
            score_data = calculate_task_score(task, strategy=strategy)
            results.append({
                **task,
                "score": score_data["score"],
                "explanation": score_data["explanation"]
            })

        results.sort(key=lambda x: (x["score"], x["importance"]), reverse=True)

        top_three = results[:3]
        output = TaskOutputSerializer(top_three, many=True)
        return Response(output.data, status=status.HTTP_200_OK)



class SaveTasksView(APIView):
    def post(self, request):
        tasks = request.data.get("tasks", [])
        saved = []

        for t in tasks:
            obj = Task.objects.create(
                title=t.get("title"),
                due_date=t.get("due_date"),
                importance=t.get("importance", 5),
                estimated_hours=t.get("estimated_hours", 1),
                dependencies=t.get("dependencies", [])
            )
            saved.append(obj)

        serializer = TaskModelSerializer(saved, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AllTasksView(APIView):
    def get(self, request):
        tasks = Task.objects.all().order_by("id")
        serializer = TaskModelSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TodayTasksView(APIView):
    def get(self, request):
        tasks = Task.objects.all()
        scored = []

        for task in tasks:
            data = {
                "title": task.title,
                "due_date": str(task.due_date),
                "importance": task.importance,
                "estimated_hours": task.estimated_hours,
                "dependencies": task.dependencies,
            }
            score_data = calculate_task_score(data)
            scored.append((task, score_data["score"]))

        scored.sort(key=lambda x: x[1], reverse=True)
        top_three = [x[0] for x in scored[:3]]

        serializer = TaskModelSerializer(top_three, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DeleteTaskView(APIView):
    def delete(self, request, id):
        try:
            task = Task.objects.get(id=id)
            task.delete()
            return Response({"message": "Deleted"}, status=status.HTTP_200_OK)
        except Task.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
