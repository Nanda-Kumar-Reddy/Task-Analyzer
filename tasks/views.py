from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import StrategySerializer, TaskOutputSerializer
from .scoring import calculate_task_score


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
