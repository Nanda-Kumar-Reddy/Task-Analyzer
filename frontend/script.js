let formTasks = [];
let dependencyMap = {};

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
        try {
            tasks = JSON.parse(document.getElementById("taskInput").value.trim());
            if (!Array.isArray(tasks)) return alert("Input must be a JSON array.");
        } catch {
            return alert("Invalid JSON format.");
        }
    } else {
        if (!formTasks.length) return alert("No form tasks added.");
        tasks = formTasks.map(t => ({
            id: t.temp_id,
            title: t.title,
            due_date: t.due_date,
            estimated_hours: t.estimated_hours,
            importance: t.importance,
            dependencies: t.dependencies
        }));
    }

    let result;
    try {
        const resp = await fetch("http://127.0.0.1:8000/api/tasks/analyze/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ strategy, tasks })
        });
        result = await resp.json();
    } catch {
        result = { tasks: mockAnalyze(tasks, strategy) };
    }

    displayResults(result.tasks ?? []);
}

async function saveTasks() {
    const mode = document.querySelector('input[name="inputMode"]:checked').value;
    let tasks = [];

    if (mode === "json") {
        try {
            tasks = JSON.parse(document.getElementById("taskInput").value.trim());
        } catch {
            return alert("Invalid JSON format.");
        }
    } else {
        if (!formTasks.length) return alert("No form tasks added.");
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
        resetFormInputs();
        fetchStoredTasks();
    }
}

async function saveAndAnalyze() {
    const strategy = document.getElementById("strategy").value;
    const mode = document.querySelector('input[name="inputMode"]:checked').value;
    let tasks = [];

    if (mode === "json") {
        try {
            tasks = JSON.parse(document.getElementById("taskInput").value.trim());
        } catch {
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

    formTasks = [];
    renderFormTasks();
    resetFormInputs();
    fetchStoredTasks();
}

async function fetchStoredTasks() {
    const allTasksResp = await fetch("http://127.0.0.1:8000/api/tasks/all/");
    const allTasks = await allTasksResp.json();
    buildDependencyMap(allTasks);
    populateDependencies(allTasks);

    const mode = document.getElementById("taskToggle").value;
    const url = mode === "today" ?
        "http://127.0.0.1:8000/api/tasks/today/" :
        "http://127.0.0.1:8000/api/tasks/all/";

    const resp = await fetch(url);
    displayDBResults(await resp.json());
}

function deleteTask(id) {
    fetch(`http://127.0.0.1:8000/api/tasks/delete/${id}/`, { method: "DELETE" })
        .then(fetchStoredTasks);
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
    <strong>Due Date:</strong> ${task.due_date ?? "N/A"}<br>
    <strong>Reason:</strong> ${task.score_explanation || "N/A"}<br><br>
    <strong>Urgency:</strong> ${subs.urgency ?? "N/A"}<br>
    <strong>Importance:</strong> ${subs.importance ?? "N/A"}<br>
    <strong>Effort:</strong> ${subs.effort ?? "N/A"}<br>
    <strong>Dependency:</strong> ${subs.dependency ?? "N/A"}
    <br>
    ${task.warnings && task.warnings.length
        ? `<br><span style='color:red;'>⚠ ${task.warnings.join(", ")}</span>`
        : ""
    }
`;


        const reasonBtn = document.createElement("button");
        reasonBtn.classList.add("reason-toggle-btn");
        reasonBtn.textContent = "View Detailed Reasoning";

        const reasonBox = document.createElement("div");
        reasonBox.classList.add("reason-box");
        reasonBox.style.display = "none";

        const r = task.reason || {};
        reasonBox.innerHTML = `
            <div class="reason-row"><strong>Summary:</strong> ${r.summary ?? "N/A"}</div>
            <div class="reason-row"><strong>Urgency:</strong> ${r.urgency_reason ?? "N/A"}</div>
            <div class="reason-row"><strong>Importance:</strong> ${r.importance_reason ?? "N/A"}</div>
            <div class="reason-row"><strong>Effort:</strong> ${r.effort_reason ?? "N/A"}</div>
            <div class="reason-row"><strong>Dependencies:</strong> ${r.dependency_reason ?? "N/A"}</div>
            <div class="reason-row"><strong>Final Priority:</strong> ${r.final_priority_reason ?? "N/A"}</div>
        `;

        reasonBtn.onclick = () => {
            reasonBox.style.display = reasonBox.style.display === "none" ? "block" : "none";
        };

        card.appendChild(title);
        card.appendChild(details);
        card.appendChild(reasonBtn);
        card.appendChild(reasonBox);

        results.appendChild(card);
    });
}


function displayDBResults(tasks) {
    const container = document.getElementById("dbResults");
    container.innerHTML = "";

    if (!tasks.length) {
        container.innerHTML = "<p>No stored tasks.</p>";
        return;
    }

    tasks.forEach(task => {
        const depNames = (task.dependencies || [])
            .map(id => dependencyMap[id] || `Task ${id}`)
            .join(", ") || "None";

        const card = document.createElement("div");
        card.classList.add("db-card");
        card.innerHTML = `
            <div class="db-title">${task.title}</div>
            <div class="db-details">
                Due: ${task.due_date || "N/A"}<br>
                Importance: ${task.importance}<br>
                Hours: ${task.estimated_hours}<br>
                <strong>Depends on:</strong> ${depNames}
            </div>
        `;

        const del = document.createElement("button");
        del.classList.add("delete-btn");
        del.textContent = "Delete";
        del.onclick = () => deleteTask(task.id);

        card.appendChild(del);
        container.appendChild(card);
    });
}

function buildDependencyMap(allTasks) {
    dependencyMap = {};
    allTasks.forEach(t => dependencyMap[t.id] = t.title);
}

function populateDependencies(tasks) {
    const select = document.getElementById("formDependencies");
    select.innerHTML = "";
    tasks.forEach(t => {
        const opt = document.createElement("option");
        opt.value = t.id;
        opt.textContent = `${t.title} (id:${t.id})`;
        select.appendChild(opt);
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
    if (importance < 1 || importance > 10) return alert("Importance must be 1-10.");
    if (estimated_hours < 1) return alert("Estimated hours must be at least 1.");
    const temp_id = Date.now();
    formTasks.push({ temp_id, title, due_date, estimated_hours, importance, dependencies });

    renderFormTasks();
    resetFormInputs();
}

function renderFormTasks() {
    const div = document.getElementById("formTasksList");
    div.innerHTML = "";

    if (!formTasks.length) {
        div.innerHTML = "<p>No tasks added.</p>";
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
        del.classList.add("small-delete-btn");
        del.textContent = "Delete";
        del.onclick = () => {
            formTasks = formTasks.filter(x => x.temp_id !== t.temp_id);
            renderFormTasks();
        };

        card.appendChild(del);
        div.appendChild(card);
    });
}

function resetFormInputs() {
    document.getElementById("formTitle").value = "";
    document.getElementById("formDueDate").value = "";
    document.getElementById("formHours").value = "1";
    document.getElementById("formImportance").value = "5";
    document.getElementById("formDependencies").selectedIndex = -1;
}

function mockAnalyze(tasks) {
    return tasks.map(t => ({
        ...t,
        priority_score: (t.importance || 5) * 10,
        score_explanation: "Offline mock scoring"
    }));
}
