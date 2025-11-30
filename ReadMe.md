# Smart Task Analyzer

A Django-based task prioritization system that actually understands how people work. Instead of just sorting by due date or importance, it combines multiple factors using smooth mathematical models to figure out what you should work on next.

---

## Setup Instructions

### What You'll Need

- Python 3.8 or higher
- Git
- A code editor (I use VS Code, but whatever works for you)
- Optional: Postman or curl if you want to test the API directly

### Getting Started

**1. Clone and navigate to the project**

```bash
git clone <your-repo-url>
cd task-analyzer
```

**2. Set up a virtual environment**

On Mac/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows (PowerShell):

```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

On Windows (CMD):

```bash
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If you're installing manually for some reason:

```bash
pip install Django==5.0.3 djangorestframework==3.16.1
```

**4. Database setup**

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

**5. Fire it up**

```bash
python manage.py runserver
```

Then open your browser to `http://127.0.0.1:8000/`

The frontend is just static files (HTML/CSS/JS) that Django serves automatically when you're in development mode, so there's no separate build step needed.

### API Endpoints

Base URL: `http://127.0.0.1:8000/api/tasks/`

| Endpoint        | Method | What it does                       |
| --------------- | ------ | ---------------------------------- |
| `/save/`        | POST   | Save tasks to database             |
| `/analyze/`     | POST   | Run the scoring algorithm on tasks |
| `/suggest/`     | POST   | Get top 3 recommended tasks        |
| `/today/`       | GET    | Quick view of today's priorities   |
| `/all/`         | GET    | Fetch all stored tasks             |
| `/delete/<id>/` | DELETE | Remove a task                      |

**Quick test with curl:**

```bash
curl -X POST http://127.0.0.1:8000/api/tasks/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"strategy":"smart","tasks":[{"title":"Demo","due_date":"2025-12-01","estimated_hours":2,"importance":7,"dependencies":[]}]}'
```

**Run tests:**

```bash
python manage.py test
```

---

## How The Algorithm Works

### The Big Picture

The algorithm doesn't just look at one thing and decide "this task is most important." Instead, it scores each task across four different dimensions and then combines them based on what kind of prioritization strategy you want to use.

Think of it like this: some days you need to focus on deadlines, other days you want to knock out quick wins, and sometimes you just need to tackle the most important stuff regardless of when it's due. The algorithm adapts to all of these modes.

### The Four Scoring Dimensions

**1. Urgency (based on working days)**

This is where it gets interesting. Instead of just counting calendar days until the due date, I calculate the actual number of _working days_ you have left. Weekends and holidays don't count because, well, most people don't work on those days.

The urgency score uses a sigmoid function (basically an S-curve):

```
U = 100 × sigmoid(-days / τ)
```

This means urgency ramps up gradually at first, then accelerates sharply as you get close to the deadline. It matches how people actually feel about deadlines—the difference between "due in 20 days" and "due in 21 days" doesn't matter much, but the difference between "due tomorrow" and "due in 2 days" feels huge.

Overdue tasks get hit with an exponential penalty that can multiply their urgency score by up to 2x, because let's be honest, overdue stuff creates real stress.

**2. Importance (exponentially scaled)**

You rate tasks from 1-10, but I don't use those numbers directly. Instead:

```
I = 100 × (rating/10)^2.5
```

Why the power function? Because in real life, a task rated 10 isn't just twice as important as a task rated 5—it's way more important. This exponential scaling reflects that psychology. A task rated 9 or 10 will dominate medium-priority tasks (4-6) in a way that feels natural.

**3. Effort (rewarding quick wins, but not too much)**

Lower effort tasks get higher scores, but I had to be careful here. A pure exponential decay would make 1-hour tasks score ~88 and 40-hour tasks score ~1, which would train you to only ever do tiny tasks. That's not productive.

So I use a hybrid model:

```
E = 50 + 50 × e^(-hours/8)
```

This gives quick tasks (1-2 hours) a nice boost while ensuring longer tasks still maintain a reasonable baseline score. You still get rewarded for quick wins, but you won't completely ignore that important project just because it takes 20 hours.

**4. Dependency Score (the complex one)**

This is probably the most sophisticated part. Tasks can both unlock other work and be blocked by other work, and both of these things should affect priority.

- If completing this task unblocks 3 other tasks, it gets +60 points (up to +100 max)
- If this task is blocked by other tasks, it takes a penalty based on how urgent/important those blocking tasks are

The blocking penalty considers the blocker's urgency, importance, and effort:

```
penalty = Σ[(blocker_urgency/100)^0.5 × (blocker_importance/10)^1.5 × (1 + blocker_hours/20)]
```

So being blocked by an overdue, critical, 8-hour task hits you way harder than being blocked by a low-priority task due in 3 weeks. This makes sense—if you can't even start a task yet, why would it be high priority?

Oh, and if you accidentally create circular dependencies (Task A depends on B, B depends on C, C depends on A), the system detects it using depth-first search and caps the score to prevent weird infinity loops.

### Putting It All Together

All four subscores get weighted and combined:

```
Final Score = w_u×Urgency + w_i×Importance + w_e×Effort + w_d×Dependency
```

The weights change based on which strategy mode you pick:

- **Smart Balance** (35% urgency, 35% importance, 20% effort, 10% dependency) - Default mode, tries to balance everything
- **Deadline Driven** (60% urgency, 25% importance, 5% effort, 10% dependency) - When you're in crunch mode
- **Fastest Wins** (15% urgency, 20% importance, 55% effort, 10% dependency) - Knock out quick tasks to build momentum
- **High Impact** (15% urgency, 60% importance, 15% effort, 10% dependency) - Focus on what matters most, deadlines be damned

Every scored task also gets a human-readable explanation like "2 working days overdue • Critical importance (10/10) • Unblocks 2 tasks" so you understand _why_ it scored that way.

---

## Design Decisions (And Why I Made Them)

### Working Days Instead of Calendar Days

**The tradeoff:** More complexity, need to maintain holiday lists  
**Why I did it anyway:** Because a task "due in 7 days" that spans a weekend actually only gives you 5 workable days. Using calendar days would systematically underestimate urgency. Yes, it means maintaining a holiday calendar, but the accuracy gain is worth it for real-world use.

### Smooth Math Functions Instead of If/Else Thresholds

**The tradeoff:** Slightly harder to understand the code  
**Why I did it anyway:** Threshold systems create weird cliff effects. Like, imagine a task scores 85 when it's due in 1 day but only 45 when due in 2 days. That's a 40-point jump for a single day difference, which feels arbitrary and can be gamed. Smooth functions (sigmoid, exponential) eliminate this and match how humans actually perceive urgency—as a gradient, not a series of cliffs.

### Hybrid Effort Formula

**The tradeoff:** Quick tasks don't get quite as dramatic a boost  
**Why I did it anyway:** With pure exponential decay, you end up with a system that basically tells you to only do 1-hour tasks because they score 95+ while anything over 10 hours scores under 30. That's not realistic. The hybrid approach ensures you still get rewarded for quick wins without falling into "quick win addiction" where you never tackle substantial work.

### Two-Pass Scoring for Dependencies

**The tradeoff:** Goes from O(n) to O(2n) complexity  
**Why I did it anyway:** To figure out how much being blocked by Task A hurts you, you need to know Task A's urgency score first. But calculating Task A's score might require knowing Task B's score if they're chained. The two-pass approach (first pass: calculate all basic scores, second pass: recalculate with dependency context) cleanly solves this without getting into recursive complexity hell. For typical task lists under 100 tasks, we're talking maybe 10ms total, which is fine.

### Allowing Negative Dependency Scores

**The tradeoff:** Explaining negative numbers to users is harder  
**Why I did it anyway:** If you're blocked by multiple critical overdue tasks totaling 30+ hours of work, your task genuinely should be deprioritized. You literally can't start it yet! Allowing dependency contributions to go negative (down to -50) captures this reality. It's more honest than artificially keeping everything positive.

### Strategy Presets Instead of Full Customization

**The tradeoff:** Less flexibility for power users  
**Why I did it anyway:** Decision fatigue is real. Too many knobs and sliders leads to analysis paralysis. The four presets cover the main mental models people use ("knock out quick stuff," "focus on important work," "chase deadlines," "balanced approach"). It's like camera modes—most people prefer "Portrait/Landscape/Night" over manually setting ISO and aperture.

### Circular Dependency Detection Instead of Auto-Fix

**The tradeoff:** System doesn't automatically resolve the problem  
**Why I did it anyway:** If I automatically broke circular dependencies by removing the "weakest link," I might violate the user's intent. Maybe they made a logical error they need to fix manually. By detecting, flagging with warnings, and capping scores, I alert users to the issue without making destructive changes to their data structure.

### Different Time Sensitivity (τ) Per Strategy

**The tradeoff:** Behavior varies across strategies in subtle ways  
**Why I did it anyway:** A deadline-focused user should see urgency spike quickly (τ=4 gives you 50% urgency at 4 days out), while an impact-focused user can tolerate longer horizons (τ=10 means 50% urgency at 10 days out). This makes each strategy mode actually feel different instead of just being weighted versions of the same thing.

### Only Showing High-Contribution Factors in Explanations

**The tradeoff:** Some subscores aren't explicitly mentioned  
**Why I did it anyway:** Nobody wants to read "Due in 15 days • Lower importance (3/10) • Quick task (2h) • No dependencies • Medium effort." That's information overload. By only showing factors that contribute more than 12% to the final score, explanations stay concise and actionable—typically 2-3 factors, which is what humans can actually process.

---

## Time Breakdown

This took me about 8-9 hours total, split roughly like this:

- **Project setup** (45 min) - Django/DRF initialization, routing, basic models
- **Frontend UI** (1 hour) - Two-panel layout, responsive styling, task cards
- **Algorithm design** (2.5 hours) - Working through the math for all four scoring dimensions, dependency graphs, cycle detection
- **Algorithm implementation** (1 hour) - Turning the math into clean Python code in `scoring.py`
- **Backend API** (1 hour) - Building the endpoints, integrating with Django, validation
- **Frontend JS** (1.25 hours) - Form handling, API integration, results display
- **Polish and fixes** (45 min) - Cleaning up edge cases, improving explanations, git cleanup

**Total: ~8.25 hours**

Pretty solid for a single focused session.

---

## Bonus Features I Added

### 1. Circular Dependency Detection (~30-45 min)

Instead of just counting dependencies, I built a full graph engine that:

- Constructs forward (depends-on) and reverse (unblocks) graphs
- Runs DFS with three-color marking (WHITE/GRAY/BLACK) to find cycles
- Flags any task involved in a cycle with warnings
- Caps dependency scores at 25 for cyclic tasks to prevent score inflation

If you accidentally create tasks that logically block each other (A→B→C→A), the system catches it and warns you.

### 2. Weekend and Holiday Intelligence (~30 min)

Urgency calculations use working days instead of calendar days:

- Automatically skips weekends (Saturday/Sunday)
- Skips predefined national holidays
- Provides explanations like "Due in 2 working days (4 calendar days)"
- Correctly handles overdue periods with working-day precision

This makes urgency way more accurate for real-world scheduling where weekends and holidays actually matter.

These two features push the system from a simple scoring engine to something that's genuinely context-aware and harder to fool.

---

## What I'd Build Next

If I had more time, here's where I'd take this:

**Machine learning weight optimization** - Learn from actual user behavior (what they complete, what they snooze, what they edit) to automatically tune the weights. Over time, it would learn if you tend to underestimate effort, procrastinate on long-term tasks, etc.

**Time-of-day awareness** - Adjust scores based on energy levels. High-effort tasks score higher in the morning, creative tasks boost in the evening, low-focus tasks rank higher during fatigue periods.

**Collaborative filtering** - "Users similar to you prioritized tasks like this..." Using anonymized patterns from similar workflows to improve recommendations.

**Risk modeling** - Most effort estimates are wrong. Add confidence intervals ("2-4 hours"), penalize tasks with high variance, boost predictable work.

**Recurring task decay** - Daily/weekly tasks should gradually lose importance unless forgotten, so they don't permanently dominate your list.

**Live calendar integration** - Pull holidays from Google Calendar, Outlook, or government APIs instead of maintaining a hardcoded list.

**Parallel dependency analysis** - For massive task lists (hundreds to thousands), parallelize the graph traversal to drop computation from milliseconds to microseconds.

**Eisenhower Matrix View** – Visualize tasks on a 2×2 grid (Urgent vs Important) to provide an intuitive strategic overview of priorities, helping users instantly spot critical work and low-value distractions.

**Learning System** – Allow users to mark suggested tasks as “Helpful” or “Not Helpful,” storing this feedback to adjust future scoring weights and gradually personalize prioritization to each user’s behavior.

Basically, turn this from a rules-based engine into a fully personalized productivity assistant that learns and adapts.

---

## Running Tests

```bash
python manage.py test
```

That's it. Feel free to reach out if something breaks or if you have questions about the algorithm design!
