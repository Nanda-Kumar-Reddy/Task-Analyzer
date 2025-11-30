from datetime import date, datetime

def parse_date(value):
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except:
        return None

def calculate_task_score(task_data, strategy="smart"):
    title = task_data.get("title", "")
    importance = task_data.get("importance", 5)
    hours = task_data.get("estimated_hours", 1)
    due_str = task_data.get("due_date", None)
    dependencies = task_data.get("dependencies", [])

    due = parse_date(due_str)
    today = date.today()

    urgency_score = 0
    explanation_parts = []

    if due is None:
        urgency_score += 0
        explanation_parts.append("No due date")
    else:
        diff = (due - today).days
        if diff < 0:
            urgency_score += 100
            explanation_parts.append("Overdue")
        elif diff <= 1:
            urgency_score += 70
            explanation_parts.append("Due very soon")
        elif diff <= 3:
            urgency_score += 50
            explanation_parts.append("Approaching deadline")
        else:
            urgency_score += max(10, 40 - diff)

    importance_score = importance * 10
    if importance >= 8:
        explanation_parts.append("High importance")

    speed_score = 0
    if hours <= 2:
        speed_score += 20
        explanation_parts.append("Quick task")

    dependency_score = 0
    if dependencies:
        dependency_score += 15
        explanation_parts.append("Has dependencies")

    if strategy == "deadline":
        urgency_score *= 1.4
    elif strategy == "fastest":
        speed_score *= 2.0
    elif strategy == "impact":
        importance_score *= 1.5
    else:
        pass

    final_score = urgency_score + importance_score + speed_score + dependency_score
    explanation = ", ".join(explanation_parts) if explanation_parts else "No special factors"

    return {
        "score": round(final_score, 2),
        "explanation": explanation
    }
