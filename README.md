# ⬡ TaskFlow — Team Task Manager

A full-stack collaborative task management web app built with **Python/Flask**. Create projects, manage teams, assign tasks, and track progress on a Kanban board — all in a clean dark-themed UI.

🚀 **Live:** [https://taskflow-production-50d9.up.railway.app](https://taskflow-production-50d9.up.railway.app)
📦 **Repo:** [https://github.com/kushika-ethara/Task_flow](https://github.com/kushika-ethara/Task_flow)

### Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | alice@test.com | 123456 |
| Member | bob@test.com | 123456 |

---

## Features

- **Authentication** — Signup, login, logout with hashed passwords (bcrypt via Werkzeug)
- **Projects** — Create projects, invite members by email, manage roles
- **Role-Based Access Control**
  - **Admin** — Full CRUD on tasks, add/remove members, edit/delete the project
  - **Member** — View project and Kanban board, update status on their own assigned tasks
- **Tasks** — Title, description, due date, priority (Low / Medium / High), status, assignee
- **Kanban Board** — Drag-free To Do / In Progress / Done columns per project
- **Dashboard** — Stats: total tasks, by status, overdue count, tasks assigned to you, recent activity
- **My Tasks** — Personal view of all tasks assigned to the current user, sorted by due date
- **Overdue Detection** — Tasks past their due date and not Done are flagged automatically
- **Responsive UI** — Dark theme, sidebar layout, mobile-friendly

---

## Tech Stack

| Layer | Tech | Version |
|-------|------|---------|
| Language | Python | 3.11 |
| Web Framework | Flask | 3.0.3 |
| ORM | Flask-SQLAlchemy | 3.1.1 |
| Auth | Flask-Login + Werkzeug | 0.6.3 / 3.0.3 |
| Forms | Flask-WTF + WTForms | 1.2.1 / 3.1.2 |
| Email Validation | email-validator | 2.1.1 |
| Database (local) | SQLite | — |
| Database (production) | PostgreSQL | Railway managed |
| DB Driver | psycopg2-binary | 2.9.9 |
| WSGI Server | Gunicorn | 22.0.0 |
| Frontend | Jinja2 + vanilla CSS + vanilla JS | — |
| Env Config | python-dotenv | 1.0.1 |
| Deployment | Railway (Nixpacks) | — |

---

## Data Models

### User
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | Primary key |
| name | String(100) | Display name |
| email | String(150) | Unique, used for login |
| password_hash | String(256) | bcrypt hash |
| created_at | DateTime | Auto |

### Project
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | Primary key |
| name | String(150) | Required |
| description | Text | Optional |
| owner_id | FK → User | Creator |
| created_at | DateTime | Auto |

### Task
| Field | Type | Notes |
|-------|------|-------|
| id | Integer | Primary key |
| title | String(200) | Required |
| description | Text | Optional |
| due_date | Date | Optional |
| priority | String(20) | Low / Medium / High (default: Medium) |
| status | String(20) | To Do / In Progress / Done (default: To Do) |
| project_id | FK → Project | Cascade delete |
| assignee_id | FK → User | Optional |
| created_at | DateTime | Auto |

### project_members (association table)
| Field | Type | Notes |
|-------|------|-------|
| user_id | FK → User | Composite PK |
| project_id | FK → Project | Composite PK |
| role | String(20) | Admin / Member |

---

## Project Structure

```
taskflow/
├── app.py                   # Flask app — models, routes, config
├── seed.py                  # Demo data seeder
├── requirements.txt         # Pinned Python dependencies
├── Procfile                 # Gunicorn process declaration
├── railway.toml             # Railway build + deploy config
├── .python-version          # Pins Python 3.11 for Nixpacks
├── .env.example             # Environment variable template
├── instance/
│   └── taskmanager.db       # SQLite DB (local only, git-ignored in prod)
├── static/
│   ├── css/style.css        # All styles (dark theme, sidebar, responsive)
│   └── js/app.js            # Minimal JS (status drag, flash dismiss)
└── templates/
    ├── base.html            # Sidebar layout shell
    ├── landing.html         # Public landing page
    ├── auth.html            # Login / Signup (shared template, mode param)
    ├── dashboard.html       # Stats cards + recent tasks
    ├── projects.html        # Projects list
    ├── project_detail.html  # Kanban board + member management
    ├── project_form.html    # Create / edit project
    ├── task_form.html       # Create / edit task
    ├── my_tasks.html        # Current user's assigned tasks
    └── error.html           # 403 / 404 error page
```

---

## API Endpoints

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET | `/` | No | Landing page (redirects to dashboard if logged in) |
| GET/POST | `/signup` | No | User registration |
| GET/POST | `/login` | No | User login |
| GET | `/logout` | Yes | Logout and redirect to landing |
| GET | `/dashboard` | Yes | Stats overview + recent tasks |
| GET | `/projects` | Yes | List all projects the user belongs to |
| GET/POST | `/projects/new` | Yes | Create a new project |
| GET | `/projects/<id>` | Yes | Project detail + Kanban board |
| GET/POST | `/projects/<id>/edit` | Admin | Edit project name/description |
| POST | `/projects/<id>/delete` | Admin | Delete project and all its tasks |
| POST | `/projects/<id>/members/add` | Admin | Add member by email |
| POST | `/projects/<id>/members/<uid>/remove` | Admin | Remove a member |
| GET/POST | `/projects/<id>/tasks/new` | Admin | Create a task in a project |
| GET/POST | `/tasks/<id>/edit` | Admin/Assignee | Edit task (admin: all fields; assignee: status only) |
| POST | `/tasks/<id>/status` | Admin/Assignee | Update task status — JSON API (`{"status": "Done"}`) |
| POST | `/tasks/<id>/delete` | Admin | Delete a task |
| GET | `/my-tasks` | Yes | All tasks assigned to the current user |

---

## Local Setup

### 1. Clone the repo
```bash
git clone https://github.com/kushika-ethara/Task_flow.git
cd Task_flow
```

### 2. Create a virtual environment
```bash
python -m venv venv
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Open .env and set a strong SECRET_KEY
```

`.env.example` contents:
```env
SECRET_KEY=your-very-secret-key-here-change-this
DATABASE_URL=sqlite:///taskmanager.db
FLASK_DEBUG=false
PORT=5000
```

### 5. (Optional) Seed demo data
```bash
python seed.py
```

This creates a sample project with 5 tasks and two accounts:

| Role | Email | Password |
|------|-------|----------|
| Admin | alice@test.com | 123456 |
| Member | bob@test.com | 123456 |

### 6. Run the app
```bash
python app.py
```

Visit: [http://localhost:5000](http://localhost:5000)

---

## Deployment on Railway

### Live URL
**[https://taskflow-production-50d9.up.railway.app](https://taskflow-production-50d9.up.railway.app)**

### Infrastructure
- **Platform:** Railway (Nixpacks builder)
- **Runtime:** Python 3.11
- **WSGI:** Gunicorn 22.0.0
- **Database:** Railway managed PostgreSQL
- **Region:** `iad` (US East)
- **Replicas:** 1
- **Restart policy:** On failure, max 3 retries

### Environment Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `SECRET_KEY` | Set manually | Flask session signing key |
| `DATABASE_URL` | Auto-injected by Railway Postgres | Full PostgreSQL connection string |
| `PORT` | Auto-injected by Railway | Port Gunicorn binds to |
| `FLASK_DEBUG` | Optional | Set `true` only for local dev |

> The app normalises `postgres://` → `postgresql://` automatically so Railway's injected URL works with SQLAlchemy 1.4+.

### railway.toml
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "gunicorn app:app --bind 0.0.0.0:$PORT"
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

### How to re-deploy
```bash
# Make your changes, then:
railway up --detach
```

### First-time deploy from scratch (Railway CLI)
```bash
railway login
railway init --name TaskFlow
railway add --database postgres
railway add --service TaskFlow
railway service link TaskFlow
railway variables --set "SECRET_KEY=your-secret-key"
railway up --detach
railway domain
```

> Tables are created automatically on first boot via `db.create_all()` — no migration step needed.

---

## License

MIT
