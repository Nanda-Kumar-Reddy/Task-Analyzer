from django.test import TestCase
from rest_framework.test import APIClient
from datetime import date, timedelta
from .scoring import calculate_task_score, analyze_tasks_batch

class ScoringAdvancedTests(TestCase):
    def test_overdue_task_scores_higher(self):
        older = {
            "title": "Old task",
            "due_date": (date.today() - timedelta(days=5)).strftime("%Y-%m-%d"),
            "importance": 5,
            "estimated_hours": 3,
            "dependencies": []
        }
        future = {
            "title": "Future task",
            "due_date": (date.today() + timedelta(days=10)).strftime("%Y-%m-%d"),
            "importance": 5,
            "estimated_hours": 3,
            "dependencies": []
        }
        r1 = calculate_task_score(older, strategy="smart")
        r2 = calculate_task_score(future, strategy="smart")
        self.assertTrue(r1["score"] > r2["score"])

    def test_quick_task_gets_effort_bonus(self):
        quick = {
            "title": "Quick",
            "due_date": (date.today() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "importance": 5,
            "estimated_hours": 1,
            "dependencies": []
        }
        slow = {
            "title": "Slow",
            "due_date": (date.today() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "importance": 5,
            "estimated_hours": 10,
            "dependencies": []
        }
        rq = calculate_task_score(quick)
        rs = calculate_task_score(slow)
        self.assertTrue(rq["subscores"]["effort"] > rs["subscores"]["effort"])

class APISortingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.analyze_url = "/api/tasks/analyze/"
        self.suggest_url = "/api/tasks/suggest/"

    def test_analyze_endpoint_sorted(self):
        body = {
            "strategy": "smart",
            "tasks": [
                {"id": 1, "title": "A", "due_date": (date.today() + timedelta(days=2)).strftime("%Y-%m-%d"), "importance": 5, "estimated_hours": 3, "dependencies": []},
                {"id": 2, "title": "B", "due_date": (date.today() - timedelta(days=1)).strftime("%Y-%m-%d"), "importance": 8, "estimated_hours": 2, "dependencies": []}
            ]
        }
        response = self.client.post(self.analyze_url, body, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        scores = [item["score"] for item in data]
        self.assertTrue(all(isinstance(s, (int, float)) for s in scores))
        self.assertTrue(scores[0] >= scores[1])

    def test_suggest_returns_top_three(self):
        tasks = []
        for i in range(6):
            tasks.append({"id": i, "title": f"T{i}", "due_date": (date.today() + timedelta(days=i)).strftime("%Y-%m-%d"), "importance": 5 + i % 5, "estimated_hours": 2, "dependencies": []})
        body = {"strategy": "smart", "tasks": tasks}
        response = self.client.post(self.suggest_url, body, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 3)
        scores = [item["score"] for item in data]
        self.assertTrue(all(scores[i] >= scores[i+1] for i in range(len(scores)-1)))
