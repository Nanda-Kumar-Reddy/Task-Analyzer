import math
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple, Optional

STRATEGY_PRESETS = {
    "smart": {"name": "Smart Balance", "w_u": 0.35, "w_i": 0.35, "w_e": 0.20, "w_d": 0.10, "tau": 7, "effort_mode": "hybrid"},
    "fastest": {"name": "Fastest Wins", "w_u": 0.15, "w_i": 0.20, "w_e": 0.55, "w_d": 0.10, "tau": 10, "effort_mode": "pure"},
    "impact": {"name": "High Impact", "w_u": 0.15, "w_i": 0.60, "w_e": 0.15, "w_d": 0.10, "tau": 10, "effort_mode": "hybrid"},
    "deadline": {"name": "Deadline Driven", "w_u": 0.60, "w_i": 0.25, "w_e": 0.05, "w_d": 0.10, "tau": 4, "effort_mode": "hybrid"},
    "advanced": {"name": "Advanced", "w_u": 0.35, "w_i": 0.35, "w_e": 0.20, "w_d": 0.10, "tau": 7, "effort_mode": "hybrid"}
}

HOLIDAYS = {
    date(2025, 1, 1), date(2025, 1, 26), date(2025, 3, 14), date(2025, 4, 18),
    date(2025, 8, 15), date(2025, 10, 2), date(2025, 10, 24), date(2025, 11, 12),
    date(2025, 12, 25), date(2026, 1, 1), date(2026, 1, 26)
}

def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1 / (1 + z)
    else:
        z = math.exp(x)
        return z / (1 + z)

def is_working_day(d: date) -> bool:
    if d.weekday() >= 5:
        return False
    if d in HOLIDAYS:
        return False
    return True

def count_working_days(start_date: date, end_date: date) -> int:
    if start_date == end_date:
        return 0
    if start_date > end_date:
        return -count_working_days(end_date, start_date)
    working_days = 0
    current = start_date
    while current < end_date:
        if is_working_day(current):
            working_days += 1
        current += timedelta(days=1)
    return working_days

def parse_date(date_str: Optional[str]) -> Optional[date]:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return None

class DependencyGraph:
    def __init__(self, tasks: List[Dict]):
        self.tasks = {}
        for i, t in enumerate(tasks):
            tid = t.get("id", i)
            self.tasks[tid] = t
        self.graph = {}
        self.reverse_graph = {}
        self.cycles = []
        self._build_graph()
        self._detect_all_cycles()
    def _build_graph(self):
        for tid, task in self.tasks.items():
            deps = task.get("dependencies", []) or []
            self.graph[tid] = deps
            if tid not in self.reverse_graph:
                self.reverse_graph[tid] = []
            for d in deps:
                if d not in self.reverse_graph:
                    self.reverse_graph[d] = []
                self.reverse_graph[d].append(tid)
    def _detect_cycle_from(self, node, colors, stack):
        if colors.get(node) == "GRAY":
            idx = stack.index(node) if node in stack else 0
            return True, stack[idx:] + [node]
        if colors.get(node) == "BLACK":
            return False, []
        colors[node] = "GRAY"
        stack.append(node)
        for nei in self.graph.get(node, []):
            if nei not in colors:
                colors[nei] = "WHITE"
            has, path = self._detect_cycle_from(nei, colors, stack)
            if has:
                return True, path
        colors[node] = "BLACK"
        stack.pop()
        return False, []
    def _detect_all_cycles(self):
        colors = {k: "WHITE" for k in self.tasks.keys()}
        for node in list(self.tasks.keys()):
            if colors[node] == "WHITE":
                has, path = self._detect_cycle_from(node, colors, [])
                if has:
                    self.cycles.append(path)
    def has_cycle(self, task_id) -> bool:
        for c in self.cycles:
            if task_id in c:
                return True
        return False
    def get_blocked_by_tasks(self, task_id):
        return [self.tasks.get(d) for d in self.graph.get(task_id, []) if d in self.tasks]
    def get_unblocks_tasks(self, task_id):
        return [self.tasks.get(u) for u in self.reverse_graph.get(task_id, []) if u in self.tasks]

def calculate_urgency_score(due_date: Optional[date], tau: float = 7) -> Tuple[float, str]:
    if due_date is None:
        return 20.0, "No deadline set"
    today = date.today()
    working_days = count_working_days(today, due_date)
    calendar_days = (due_date - today).days
    base = 100 * sigmoid(-working_days / tau)
    if working_days < 0:
        penalty = 1 + 0.5 * min(abs(working_days) / 20, 2)
        urgency = min(100, base * penalty)
        explanation = f"{abs(working_days)} working days overdue"
    else:
        urgency = base
        if working_days == 0:
            explanation = "Due today"
        elif working_days == 1:
            explanation = "Due tomorrow (1 working day)"
        else:
            explanation = f"Due in {working_days} working days ({calendar_days} calendar days)"
    return urgency, explanation

def calculate_importance_score(importance: Optional[int]) -> Tuple[float, str]:
    if importance is None:
        importance = 5
    importance = max(1, min(10, importance))
    score = 100 * ((importance / 10) ** 2.5)
    if importance >= 9:
        explanation = f"Critical importance ({importance}/10)"
    elif importance >= 7:
        explanation = f"High importance ({importance}/10)"
    elif importance >= 5:
        explanation = f"Moderate importance ({importance}/10)"
    else:
        explanation = f"Lower importance ({importance}/10)"
    return score, explanation

def calculate_effort_score(hours: Optional[float], mode: str = "hybrid") -> Tuple[float, str]:
    if hours is None or hours < 0:
        hours = 1
    h0 = 8.0
    if mode == "pure":
        score = 100 * math.exp(-hours / h0)
    else:
        score = 50 + 50 * math.exp(-hours / h0)
    if hours <= 0.5:
        explanation = f"Instant task ({hours}h)"
    elif hours <= 2:
        explanation = f"Quick win ({hours}h)"
    elif hours <= 4:
        explanation = f"Short task ({hours}h)"
    elif hours <= 8:
        explanation = f"Moderate effort ({hours}h)"
    else:
        explanation = f"Long project ({hours}h)"
    return score, explanation

def calculate_dependency_score(task_id, dependency_graph: DependencyGraph, task_scores: Dict) -> Tuple[float, str]:
    if dependency_graph.has_cycle(task_id):
        return 25.0, "Part of circular dependency (capped)"
    unblocks = dependency_graph.get_unblocks_tasks(task_id) or []
    n_unblocks = len([u for u in unblocks if u])
    blocked_by = dependency_graph.get_blocked_by_tasks(task_id) or []
    blocking_penalty = 0.0
    for dep_task in blocked_by:
        if not dep_task:
            continue
        dep_id = dep_task.get("id")
        dep_score = task_scores.get(dep_id)
        dep_urgency = dep_score["subscores"]["urgency"] if dep_score else 50
        dep_importance = dep_task.get("importance", 5)
        dep_hours = dep_task.get("estimated_hours", 1)
        block_weight = (dep_urgency / 100) ** 0.5 * (dep_importance / 10) ** 1.5
        effort_penalty = 1 + (dep_hours / 20)
        blocking_penalty += block_weight * effort_penalty
    unblocking_benefit = min(100, n_unblocks * 20)
    dependency_score = unblocking_benefit - min(50, blocking_penalty * 10)
    explanations = []
    if n_unblocks > 0:
        explanations.append(f"Unblocks {n_unblocks} task{'s' if n_unblocks > 1 else ''}")
    if len(blocked_by) > 0:
        explanations.append(f"Blocked by {len(blocked_by)} task{'s' if len(blocked_by) > 1 else ''}")
    explanation = " • ".join(explanations) if explanations else "No dependencies"
    return dependency_score, explanation

def calculate_task_score(task_data: Dict, strategy: str = "smart") -> Dict:
    params = STRATEGY_PRESETS.get(strategy, STRATEGY_PRESETS["smart"])
    w_u, w_i, w_e, w_d = params["w_u"], params["w_i"], params["w_e"], params["w_d"]
    tau = params["tau"]
    effort_mode = params.get("effort_mode", "hybrid")
    title = task_data.get("title", "Untitled")
    importance = task_data.get("importance", 5)
    hours = task_data.get("estimated_hours", 1)
    due = parse_date(task_data.get("due_date"))
    U, u_text = calculate_urgency_score(due, tau)
    I, i_text = calculate_importance_score(importance)
    E, e_text = calculate_effort_score(hours, effort_mode)
    deps = task_data.get("dependencies", []) or []
    if deps:
        D = min(50, len(deps) * 15)
        d_text = f"Has {len(deps)} dependencies"
    else:
        D = 0.0
        d_text = "No dependencies"
    final_score = w_u * U + w_i * I + w_e * E + w_d * D
    final_score = max(0.0, min(100.0, final_score))
    contributions = {"urgency": round(w_u * U, 1), "importance": round(w_i * I, 1), "effort": round(w_e * E, 1), "dependency": round(w_d * D, 1)}
    subscores = {"urgency": round(U, 1), "importance": round(I, 1), "effort": round(E, 1), "dependency": round(D, 1)}
    sorted_contrib = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
    explanation_parts = []
    for factor, val in sorted_contrib:
        if val >= 12:
            if factor == "urgency":
                explanation_parts.append(u_text)
            elif factor == "importance":
                explanation_parts.append(i_text)
            elif factor == "effort":
                explanation_parts.append(e_text)
            elif factor == "dependency" and D != 0:
                explanation_parts.append(d_text)
    explanation = " • ".join(explanation_parts) if explanation_parts else "Standard priority"
    return {"score": round(final_score, 2), "explanation": explanation, "subscores": subscores, "contributions": contributions, "strategy": params["name"]}

def calculate_task_priority(task: Dict, task_id, dependency_graph: Optional[DependencyGraph], task_scores: Optional[Dict], strategy: str = "smart") -> Dict:
    params = STRATEGY_PRESETS.get(strategy, STRATEGY_PRESETS["smart"])
    w_u, w_i, w_e, w_d = params["w_u"], params["w_i"], params["w_e"], params["w_d"]
    tau = params["tau"]
    effort_mode = params.get("effort_mode", "hybrid")
    due = parse_date(task.get("due_date"))
    I_val = task.get("importance", 5)
    hours = task.get("estimated_hours", 1)
    U, u_text = calculate_urgency_score(due, tau)
    I, i_text = calculate_importance_score(I_val)
    E, e_text = calculate_effort_score(hours, effort_mode)
    if dependency_graph and task_scores is not None:
        D, d_text = calculate_dependency_score(task_id, dependency_graph, task_scores)
    else:
        deps = task.get("dependencies", []) or []
        if deps:
            D = min(50, len(deps) * 15)
            d_text = f"Has {len(deps)} dependencies"
        else:
            D = 0.0
            d_text = "No dependencies"
    final_score = w_u * U + w_i * I + w_e * E + w_d * D
    final_score = max(0.0, min(100.0, final_score))
    contributions = {"urgency": round(w_u * U, 1), "importance": round(w_i * I, 1), "effort": round(w_e * E, 1), "dependency": round(w_d * D, 1)}
    subscores = {"urgency": round(U, 1), "importance": round(I, 1), "effort": round(E, 1), "dependency": round(D, 1)}
    sorted_contrib = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
    explanation_parts = []
    for factor, val in sorted_contrib:
        if val >= 12:
            if factor == "urgency":
                explanation_parts.append(u_text)
            elif factor == "importance":
                explanation_parts.append(i_text)
            elif factor == "effort":
                explanation_parts.append(e_text)
            elif factor == "dependency" and D != 0:
                explanation_parts.append(d_text)
    explanation = " • ".join(explanation_parts) if explanation_parts else "Standard priority"
    return {"score": round(final_score, 2), "explanation": explanation, "subscores": subscores, "contributions": contributions, "strategy": params["name"]}

def analyze_tasks_batch(tasks: List[Dict], strategy: str = "smart") -> List[Dict]:
    for i, t in enumerate(tasks):
        if "id" not in t:
            t["id"] = i
    dep_graph = DependencyGraph(tasks)
    task_scores = {}
    for t in tasks:
        tid = t.get("id")
        task_scores[tid] = calculate_task_priority(t, tid, None, None, strategy)
    results = []
    for t in tasks:
        tid = t.get("id")
        score_data = calculate_task_priority(t, tid, dep_graph, task_scores, strategy)
        warnings = []
        if dep_graph.has_cycle(tid):
            warnings.append("Circular dependency detected")
        results.append({**t, "priority_score": score_data["score"], "score_explanation": score_data["explanation"], "score_details": score_data, "warnings": warnings})
    results.sort(key=lambda x: x["priority_score"], reverse=True)
    return results
