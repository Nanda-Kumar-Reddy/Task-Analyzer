async function analyzeTasks() {
    const input = document.getElementById("taskInput").value.trim();
    const strategy = document.getElementById("strategy").value;
    let tasks = [];

    try {
        tasks = JSON.parse(input);
        if (!Array.isArray(tasks)) {
            alert("Input must be a JSON array of tasks.");
            return;
        }
    } catch (e) {
        alert("Invalid JSON format.");
        return;
    }

    let responseData;
    try {
        const response = await fetch("http://127.0.0.1:8000/api/tasks/analyze/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                strategy: strategy,
                tasks: tasks
            })
        });
        responseData = await response.json();
    } catch (error) {
        responseData = mockAnalyze(tasks, strategy);
    }

    displayResults(responseData);
}

function displayResults(sortedTasks) {
    const results = document.getElementById("results");
    results.innerHTML = "";

    if (!sortedTasks || sortedTasks.length === 0) {
        results.innerHTML = "<p>No tasks to display.</p>";
        return;
    }

    sortedTasks.forEach(task => {
        const card = document.createElement("div");
        card.classList.add("task-card");

        if (task.score >= 80) card.classList.add("priority-high");
        else if (task.score >= 50) card.classList.add("priority-medium");
        else card.classList.add("priority-low");

        const title = document.createElement("div");
        title.classList.add("task-title");
        title.textContent = task.title;

        const details = document.createElement("div");
        details.classList.add("task-details");
        details.innerHTML =
            "Score: " + task.score +
            "<br>Due: " + (task.due_date || "N/A") +
            "<br>Importance: " + task.importance +
            "<br>Hours: " + task.estimated_hours +
            "<br>Explanation: " + (task.explanation || "N/A");

        card.appendChild(title);
        card.appendChild(details);
        results.appendChild(card);
    });
}

function mockAnalyze(tasks, strategy) {
    return tasks.map(t => {
        let base = (t.importance || 5) * 10;
        let quick = t.estimated_hours <= 2 ? 15 : 0;
        let deadlineBoost = strategy === "deadline" ? 20 : 0;
        let impactBoost = strategy === "impact" ? 25 : 0;
        let fastBoost = strategy === "fastest" ? (t.estimated_hours <= 2 ? 40 : 0) : 0;

        const score = base + quick + deadlineBoost + impactBoost + fastBoost;

        return {
            ...t,
            score: score,
            explanation: "Mock scoring applied (backend not running)"
        };
    }).sort((a, b) => b.score - a.score);
}
