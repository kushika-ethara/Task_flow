# ⬡ TaskFlow — Team Task Manager

A full-stack collaborative task management web application built with **Python/Flask**.

## Features

- **Authentication** — Signup, Login, Logout with hashed passwords (Flask-Login + Werkzeug)
- **Projects** — Create projects, manage members, role-based access (Admin / Member)
- **Tasks** — Create, assign, update tasks with priority, due date, and status
- **Kanban Board** — Visual To Do / In Progress / Done columns per project
- **Dashboard** — Stats overview: total tasks, by status, overdue, and per-user
- **Role-Based Access Control**
  - **Admin**: Full CRUD on tasks, add/remove members, edit/delete project
  - **Member**: View project, update status on assigned tasks only
- **Responsive UI** — Dark theme, sidebar layout, mobile-friendly

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.10+, Flask 3.0 |
| ORM | Flask-SQLAlchemy |
| Auth | Flask-Login, Werkzeug |
| Database | SQLite (local) / PostgreSQL (production) |
| Frontend | Jinja2 templates, vanilla CSS, vanilla JS |
| Deployment | Railway |

---

## Local Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/taskflow.git
cd taskflow
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env and set a strong SECRET_KEY
```

### 5. (Optional) Seed demo data
```bash
python seed.py
# Admin: alice@demo.com / password
# Member: bob@demo.com / password
```

### 6. Run the app
```bash
python app.py
```

Visit: http://localhost:5000

---

## Deployment on Railway

### Steps

1. Push your code to GitHub.

2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**.

3. Add a **PostgreSQL** plugin in Railway dashboard.

4. Set these **Environment Variables** in Railway:
   ```
   SECRET_KEY=your-very-secret-key
   DATABASE_URL=<auto-filled by Railway PostgreSQL plugin>
   PORT=5000
   ```

5. Railway auto-detects the `Procfile` and deploys.

6. Your app is live at the Railway-provided URL!

> **Note**: The app auto-creates tables on startup via `db.create_all()` — no migration needed.

---

## Project Structure

```
taskflow/
├── app.py              # Main Flask app (models + routes)
├── seed.py             # Demo data seeder
├── requirements.txt    # Python dependencies
├── Procfile            # Railway/Heroku process file
├── .env.example        # Environment variable template
├── static/
│   ├── css/style.css   # All styles
│   └── js/app.js       # Minimal JS
└── templates/
    ├── base.html        # Sidebar layout shell
    ├── landing.html     # Public landing page
    ├── auth.html        # Login / Signup form
    ├── dashboard.html   # Stats + recent tasks
    ├── projects.html    # Projects list
    ├── project_detail.html  # Kanban board + members
    ├── project_form.html    # Create/edit project
    ├── task_form.html       # Create/edit task
    ├── my_tasks.html        # Assigned tasks list
    └── error.html           # 403/404 error page
```

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Landing page |
| GET/POST | `/signup` | User registration |
| GET/POST | `/login` | User login |
| GET | `/logout` | Logout |
| GET | `/dashboard` | Dashboard |
| GET | `/projects` | All projects |
| GET/POST | `/projects/new` | Create project |
| GET | `/projects/<id>` | Project detail + Kanban |
| GET/POST | `/projects/<id>/edit` | Edit project |
| POST | `/projects/<id>/delete` | Delete project |
| POST | `/projects/<id>/members/add` | Add member |
| POST | `/projects/<id>/members/<uid>/remove` | Remove member |
| GET/POST | `/projects/<id>/tasks/new` | Create task |
| GET/POST | `/tasks/<id>/edit` | Edit task |
| POST | `/tasks/<id>/status` | Update status (JSON API) |
| POST | `/tasks/<id>/delete` | Delete task |
| GET | `/my-tasks` | Current user's tasks |

---

## License

MIT
