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
            body: JSON.stringify({ strategy, tasks })
        });
        responseData = await response.json();
    } catch (error) {
        alert("Backend not reachable, using fallback scoring.");
        responseData = { tasks: mockAnalyze(tasks, strategy) };
    }

    displayResults(responseData.tasks ?? []);
}

async function saveTasks() {
    const mode = document.querySelector('input[name="inputMode"]:checked').value;
    let tasks = [];

    if (mode === "json") {
        const input = document.getElementById("taskInput").value.trim();
        try {
            tasks = JSON.parse(input);
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

    const resp = await fetch("http://127.0.0.1:8000/api/tasks/save/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tasks })
    });

    if (resp.ok) {
        alert("Tasks saved!");
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
        try {
            tasks = JSON.parse(document.getElementById("taskInput").value.trim());
        } catch (e) {
            return alert("Invalid JSON format.");
        }
    } else {
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
        body: JSON.stringify({ tasks })
    });

    const resp = await fetch("http://127.0.0.1:8000/api/tasks/analyze/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ strategy, tasks })
    });

    const data = await resp.json();
    displayResults(data.tasks ?? []);
    fetchStoredTasks();
}

async function fetchStoredTasks() {
    const mode = document.getElementById("taskToggle").value;
    const url = mode === "today"
        ? "http://127.0.0.1:8000/api/tasks/today/"
        : "http://127.0.0.1:8000/api/tasks/all/";

    const resp = await fetch(url);
    const data = await resp.json();

    displayDBResults(data);
    populateDependencies(data);
}

async function deleteTask(id) {
    await fetch(`http://127.0.0.1:8000/api/tasks/delete/${id}/`, { method: "DELETE" });
    fetchStoredTasks();
}

function displayResults(tasks) {
    const results = document.getElementById("results");
    results.innerHTML = "";

    if (!tasks || tasks.length === 0) {
        results.innerHTML = "<p>No tasks to display.</p>";
        return;
    }

    tasks.forEach(task => {
        const card = document.createElement("div");
        card.classList.add("task-card");

        const score = task.priority_score ?? task.score ?? 0;

        if (score >= 80) card.classList.add("priority-high");
        else if (score >= 50) card.classList.add("priority-medium");
        else card.classList.add("priority-low");

        const title = document.createElement("div");
        title.classList.add("task-title");
        title.textContent = task.title;

        const details = document.createElement("div");
        details.classList.add("task-details");

        const subs = task.score_details?.subscores || {};

        details.innerHTML = `
            <strong>Score:</strong> ${score.toFixed(1)}<br>
            <strong>Reason:</strong> ${task.score_explanation || "N/A"}<br><br>
            <strong>Urgency:</strong> ${subs.urgency ?? "N/A"}<br>
            <strong>Importance:</strong> ${subs.importance ?? "N/A"}<br>
            <strong>Effort:</strong> ${subs.effort ?? "N/A"}<br>
            <strong>Dependency:</strong> ${subs.dependency ?? "N/A"}<br>
            ${task.warnings && task.warnings.length
                ? `<br><span style='color:red'>⚠ ${task.warnings.join(", ")}</span>`
                : ""
            }
        `;

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

        card.innerHTML = `
            <div class="db-title">${task.title}</div>
            <div class="db-details">
                Due: ${task.due_date || "N/A"}<br>
                Importance: ${task.importance}<br>
                Hours: ${task.estimated_hours}
            </div>
        `;

        const delBtn = document.createElement("button");
        delBtn.classList.add("delete-btn");
        delBtn.textContent = "Delete";
        delBtn.onclick = () => deleteTask(task.id);

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
    const due_date = document.getElementById("formDueDate").value;
    const estimated_hours = parseInt(document.getElementById("formHours").value);
    const importance = parseInt(document.getElementById("formImportance").value);
    const dependencies = Array.from(document.getElementById("formDependencies").selectedOptions)
        .map(o => parseInt(o.value));

    if (!title) return alert("Title is required.");
    if (!due_date) return alert("Due date required.");

    const temp_id = Date.now();
    formTasks.push({ temp_id, title, due_date, estimated_hours, importance, dependencies });
    renderFormTasks();
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

        card.innerHTML = `
            <div class="form-task-info">
                ${t.title}<br>
                Due: ${t.due_date} • Importance: ${t.importance} • Hours: ${t.estimated_hours}
            </div>
        `;

        const del = document.createElement("button");
        del.textContent = "Delete";
        del.onclick = () => {
            formTasks = formTasks.filter(x => x.temp_id !== t.temp_id);
            renderFormTasks();
        };

        card.appendChild(del);
        container.appendChild(card);
    });
}

function mockAnalyze(tasks, strategy) {
    return tasks.map(t => ({
        ...t,
        priority_score: (t.importance || 5) * 10,
        score_explanation: "Offline mock scoring"
    }));
}
