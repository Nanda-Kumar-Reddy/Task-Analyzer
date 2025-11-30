import json
from datetime import date
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Task
from .serializers import TaskSerializer
from .scoring import analyze_tasks_batch, STRATEGY_PRESETS

@csrf_exempt
@require_http_methods(["POST"])
def analyze_tasks(request):
    try:
        data = json.loads(request.body)
        tasks = data.get("tasks", [])
        strategy = data.get("strategy", "smart")
        if strategy not in STRATEGY_PRESETS:
            return JsonResponse({"error": "Invalid strategy"}, status=400)
        results = analyze_tasks_batch(tasks, strategy)
        return JsonResponse({"success": True, "strategy": STRATEGY_PRESETS[strategy]["name"], "tasks": results}, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def suggest_top_tasks(request):
    try:
        data = json.loads(request.body)
        tasks = data.get("tasks", [])
        strategy = data.get("strategy", "smart")
        results = analyze_tasks_batch(tasks, strategy)
        top3 = results[:3]
        formatted = []
        for t in top3:
            formatted.append({
                "rank": len(formatted) + 1,
                "id": t.get("id"),
                "title": t.get("title"),
                "score": t.get("priority_score"),
                "explanation": t.get("score_explanation"),
                "subscores": t.get("score_details", {}).get("subscores", {}),
                "strategy": t.get("score_details", {}).get("strategy", "")
            })
        return JsonResponse(formatted, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def save_tasks(request):
    try:
        data = json.loads(request.body)
        tasks = data.get("tasks", [])
        saved = []
        for t in tasks:
            serializer = TaskSerializer(data=t)
            if serializer.is_valid():
                obj = serializer.save()
                saved.append(TaskSerializer(obj).data)
        return JsonResponse(saved, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_http_methods(["GET"])
def get_all_tasks(request):
    qs = Task.objects.all().order_by("id")
    ser = TaskSerializer(qs, many=True)
    return JsonResponse(ser.data, safe=False)

@require_http_methods(["GET"])
def get_today_top_tasks(request):
    qs = Task.objects.all()
    ser = TaskSerializer(qs, many=True)
    tasks = ser.data
    results = analyze_tasks_batch(tasks, "smart")
    return JsonResponse(results[:3], safe=False)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_task(request, task_id):
    try:
        Task.objects.filter(id=task_id).delete()
        return JsonResponse({"success": True})
    except:
        return JsonResponse({"success": False}, status=400)
