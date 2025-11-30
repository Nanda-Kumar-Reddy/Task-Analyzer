let formTasks = [];

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("modeJson").addEventListener("change", toggleInputMode);
    document.getElementById("modeForm").addEventListener("change", toggleInputMode);
    fetchStoredTasks();
});

function toggleInputMode() {
    const mode = document.querySelector('input[name="inputMode"]:checked').value;
    document.getElementById("jsonSection").style.display = mode === "json" ? "" : "none";
    document.getElementById("formSection").style.display = mode === "form" ? "" : "none";
}

async function analyzeTasks() {
    const mode = document.querySelector('input[name="inputMode"]:checked').value;
    const strategy = document.getElementById("strategy").value;
    let tasks = [];

    if (mode === "json") {
        const input = document.getElementById("taskInput").value.trim();
        try {
            tasks = JSON.parse(input);
            if (!Array.isArray(tasks)) return alert("Input must be a JSON array.");
        } catch (e) {
            return alert("Invalid JSON format.");
        }
    } else {
        if (formTasks.length === 0) return alert("No form tasks added.");
        tasks = formTasks.map(t => ({
            id: t.temp_id,
            title: t.title,
            due_date: t.due_date,
            estimated_hours: t.estimated_hours,
            importance: t.importance,
            dependencies: t.dependencies
        }));
    }

    let responseData;
    try {
        const response = await fetch("http://127.0.0.1:8000/api/tasks/analyze/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ strategy: strategy, tasks: tasks })
        });
        responseData = await response.json();
    } catch (error) {
        responseData = mockAnalyze(tasks, strategy);
    }

    displayResults(responseData);
}

async function saveTasks() {
    const mode = document.querySelector('input[name="inputMode"]:checked').value;
    let tasks = [];

    if (mode === "json") {
        const input = document.getElementById("taskInput").value.trim();
        try {
            tasks = JSON.parse(input);
            if (!Array.isArray(tasks)) return alert("Input must be a JSON array.");
        } catch (e) {
            return alert("Invalid JSON format.");
        }
    } else {
        if (formTasks.length === 0) return alert("No form tasks added.");
        tasks = formTasks.map(t => ({
            title: t.title,
            due_date: t.due_date,
            estimated_hours: t.estimated_hours,
            importance: t.importance,
            dependencies: t.dependencies
        }));
    }

    const response = await fetch("http://127.0.0.1:8000/api/tasks/save/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tasks: tasks })
    });

    if (response.ok) {
        alert("Tasks saved successfully.");
        formTasks = [];
        renderFormTasks();
        fetchStoredTasks();
    } else {
        alert("Failed to save tasks.");
    }
}

async function saveAndAnalyze() {
    const mode = document.querySelector('input[name="inputMode"]:checked').value;
    const strategy = document.getElementById("strategy").value;
    let tasks = [];

    if (mode === "json") {
        const input = document.getElementById("taskInput").value.trim();
        try {
            tasks = JSON.parse(input);
            if (!Array.isArray(tasks)) return alert("Input must be a JSON array.");
        } catch (e) {
            return alert("Invalid JSON format.");
        }
    } else {
        if (formTasks.length === 0) return alert("No form tasks added.");
        tasks = formTasks.map(t => ({
            title: t.title,
            due_date: t.due_date,
            estimated_hours: t.estimated_hours,
            importance: t.importance,
            dependencies: t.dependencies
        }));
    }

    await fetch("http://127.0.0.1:8000/api/tasks/save/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tasks: tasks })
    });

    const response = await fetch("http://127.0.0.1:8000/api/tasks/analyze/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ strategy: strategy, tasks: tasks })
    });

    if (response.ok) {
        const data = await response.json();
        displayResults(data);
        formTasks = [];
        renderFormTasks();
        fetchStoredTasks();
    } else {
        alert("Analysis failed.");
    }
}

async function fetchStoredTasks() {
    const mode = document.getElementById("taskToggle").value;
    const url = mode === "today"
        ? "http://127.0.0.1:8000/api/tasks/today/"
        : "http://127.0.0.1:8000/api/tasks/all/";

    const response = await fetch(url);
    const data = await response.json();
    displayDBResults(data);
    populateDependencies(data);
}

async function deleteTask(id) {
    await fetch(`http://127.0.0.1:8000/api/tasks/delete/${id}/`, {
        method: "DELETE"
    });
    fetchStoredTasks();
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

function displayDBResults(tasks) {
    const container = document.getElementById("dbResults");
    container.innerHTML = "";

    if (!tasks || tasks.length === 0) {
        container.innerHTML = "<p>No stored tasks.</p>";
        return;
    }

    tasks.forEach(task => {
        const card = document.createElement("div");
        card.classList.add("db-card");

        const title = document.createElement("div");
        title.classList.add("db-title");
        title.textContent = task.title;

        const details = document.createElement("div");
        details.classList.add("db-details");
        details.innerHTML =
            "Due: " + (task.due_date || "N/A") +
            "<br>Importance: " + task.importance +
            "<br>Hours: " + task.estimated_hours;

        const delBtn = document.createElement("button");
        delBtn.classList.add("delete-btn");
        delBtn.textContent = "Delete";
        delBtn.onclick = () => deleteTask(task.id);

        card.appendChild(title);
        card.appendChild(details);
        card.appendChild(delBtn);
        container.appendChild(card);
    });
}

function populateDependencies(tasks) {
    const sel = document.getElementById("formDependencies");
    if (!sel) return;
    sel.innerHTML = "";
    tasks.forEach(t => {
        const opt = document.createElement("option");
        opt.value = t.id;
        opt.textContent = `${t.title} (id:${t.id})`;
        sel.appendChild(opt);
    });
}

function addFormTask() {
    const title = document.getElementById("formTitle").value.trim();
    const due_date = document.getElementById("formDueDate").value || null;
    const estimated_hours = parseInt(document.getElementById("formHours").value) || 1;
    const importance = parseInt(document.getElementById("formImportance").value) || 5;
    const depsSel = document.getElementById("formDependencies");
    const dependencies = Array.from(depsSel.selectedOptions).map(o => parseInt(o.value));

    if (!title) return alert("Title is required.");

    
    const temp_id = Date.now() + Math.floor(Math.random() * 1000);
    const task = { temp_id, title, due_date, estimated_hours, importance, dependencies };
    formTasks.push(task);
    renderFormTasks();

    document.getElementById("formTitle").value = "";
    document.getElementById("formDueDate").value = "";
    document.getElementById("formHours").value = "1";
    document.getElementById("formImportance").value = "5";
    depsSel.selectedIndex = -1;
}

function renderFormTasks() {
    const container = document.getElementById("formTasksList");
    container.innerHTML = "";
    if (formTasks.length === 0) {
        container.innerHTML = "<p>No tasks added.</p>";
        return;
    }

    formTasks.forEach(t => {
        const card = document.createElement("div");
        card.classList.add("form-task-card");

        const info = document.createElement("div");
        info.classList.add("form-task-info");
        info.innerHTML = `${t.title} <br> Due: ${t.due_date || "N/A"} • Importance: ${t.importance} • Hours: ${t.estimated_hours}`;

        const actions = document.createElement("div");
        actions.classList.add("form-task-actions");

        const del = document.createElement("button");
        del.classList.add("form-delete-btn");
        del.textContent = "Delete";
        del.onclick = () => {
            formTasks = formTasks.filter(x => x.temp_id !== t.temp_id);
            renderFormTasks();
        };

        actions.appendChild(del);
        card.appendChild(info);
        card.appendChild(actions);
        container.appendChild(card);
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
