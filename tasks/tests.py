from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from datetime import date, timedelta

from .scoring import calculate_task_score


class ScoringTests(TestCase):
    def test_overdue_task_scores_higher(self):
        task = {
            "title": "Test",
            "due_date": (date.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "importance": 5,
            "estimated_hours": 3,
            "dependencies": []
        }
        result = calculate_task_score(task, strategy="smart")
        self.assertTrue(result["score"] > 100)

    def test_quick_task_gets_speed_bonus(self):
        task = {
            "title": "Quick Task",
            "due_date": (date.today() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "importance": 5,
            "estimated_hours": 1,
            "dependencies": []
        }
        result = calculate_task_score(task)
        self.assertTrue(result["score"] > 50)


class AnalyzeAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/tasks/analyze/"

    def test_analyze_returns_sorted_results(self):
        body = {
            "strategy": "smart",
            "tasks": [
                {
                    "id": 1,
                    "title": "A",
                    "due_date": (date.today() + timedelta(days=2)).strftime("%Y-%m-%d"),
                    "importance": 5,
                    "estimated_hours": 3,
                    "dependencies": []
                },
                {
                    "id": 2,
                    "title": "B",
                    "due_date": (date.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
                    "importance": 8,
                    "estimated_hours": 2,
                    "dependencies": []
                }
            ]
        }
        response = self.client.post(self.url, body, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data[0]["id"], 2)


class SuggestAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/tasks/suggest/"

    def test_suggest_returns_top_three(self):
        tasks = []
        for i in range(5):
            tasks.append({
                "id": i,
                "title": f"Task {i}",
                "due_date": (date.today() + timedelta(days=i)).strftime("%Y-%m-%d"),
                "importance": 5 + i,
                "estimated_hours": 2,
                "dependencies": []
            })
        body = {"strategy": "smart", "tasks": tasks}
        response = self.client.post(self.url, body, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 3)
        self.assertTrue(data[0]["importance"] >= data[1]["importance"])
