from flask import Flask, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Railway PostgreSQL plugin provides DATABASE_URL with "postgres://" scheme;
# SQLAlchemy 1.4+ requires "postgresql://" — fix it transparently.
_db_url = os.environ.get('DATABASE_URL', 'sqlite:///taskmanager.db')
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# ─── Models ──────────────────────────────────────────────────────────────────

project_members = db.Table('project_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('role', db.String(20), default='Member')
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owned_projects = db.relationship('Project', backref='owner', lazy=True)
    assigned_tasks = db.relationship('Task', backref='assignee', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_role_in(self, project):
        stmt = project_members.select().where(
            project_members.c.user_id == self.id,
            project_members.c.project_id == project.id
        )
        result = db.session.execute(stmt).fetchone()
        return result.role if result else None

    def is_admin_of(self, project):
        return self.get_role_in(project) == 'Admin'


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship('User', secondary=project_members,
                              backref=db.backref('projects', lazy='dynamic'))
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    priority = db.Column(db.String(20), default='Medium')  # Low, Medium, High
    status = db.Column(db.String(20), default='To Do')      # To Do, In Progress, Done
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_overdue(self):
        return self.due_date and self.due_date < date.today() and self.status != 'Done'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ─── Auth Routes ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not all([name, email, password]):
            flash('All fields are required.', 'error')
        elif password != confirm:
            flash('Passwords do not match.', 'error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
        else:
            user = User(name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash(f'Welcome, {name}!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('auth.html', mode='signup')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember'))
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('auth.html', mode='login')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# ─── Dashboard ───────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    user_projects = current_user.projects.all()
    all_tasks = Task.query.filter(
        Task.project_id.in_([p.id for p in user_projects])
    ).all()

    stats = {
        'total': len(all_tasks),
        'todo': sum(1 for t in all_tasks if t.status == 'To Do'),
        'in_progress': sum(1 for t in all_tasks if t.status == 'In Progress'),
        'done': sum(1 for t in all_tasks if t.status == 'Done'),
        'overdue': sum(1 for t in all_tasks if t.is_overdue),
        'my_tasks': sum(1 for t in all_tasks if t.assignee_id == current_user.id),
    }

    recent_tasks = Task.query.filter(
        Task.project_id.in_([p.id for p in user_projects])
    ).order_by(Task.created_at.desc()).limit(5).all()

    return render_template('dashboard.html', stats=stats, projects=user_projects,
                           recent_tasks=recent_tasks, today=date.today())


# ─── Project Routes ───────────────────────────────────────────────────────────

@app.route('/projects')
@login_required
def projects():
    user_projects = current_user.projects.all()
    return render_template('projects.html', projects=user_projects)


@app.route('/projects/new', methods=['GET', 'POST'])
@login_required
def new_project():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        if not name:
            flash('Project name is required.', 'error')
        else:
            project = Project(name=name, description=description, owner_id=current_user.id)
            db.session.add(project)
            db.session.flush()
            # Creator becomes Admin
            stmt = project_members.insert().values(
                user_id=current_user.id, project_id=project.id, role='Admin'
            )
            db.session.execute(stmt)
            db.session.commit()
            flash('Project created!', 'success')
            return redirect(url_for('project_detail', project_id=project.id))
    return render_template('project_form.html', project=None)


@app.route('/projects/<int:project_id>')
@login_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    if current_user not in project.members:
        abort(403)
    role = current_user.get_role_in(project)
    tasks = Task.query.filter_by(project_id=project_id).order_by(Task.created_at.desc()).all()

    # Group tasks by status
    task_groups = {
        'To Do': [t for t in tasks if t.status == 'To Do'],
        'In Progress': [t for t in tasks if t.status == 'In Progress'],
        'Done': [t for t in tasks if t.status == 'Done'],
    }

    member_roles = []
    for m in project.members:
        member_roles.append({'user': m, 'role': m.get_role_in(project)})

    return render_template('project_detail.html', project=project, task_groups=task_groups,
                           role=role, member_roles=member_roles, today=date.today())


@app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    if not current_user.is_admin_of(project):
        abort(403)
    if request.method == 'POST':
        project.name = request.form.get('name', '').strip()
        project.description = request.form.get('description', '').strip()
        db.session.commit()
        flash('Project updated!', 'success')
        return redirect(url_for('project_detail', project_id=project_id))
    return render_template('project_form.html', project=project)


@app.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if not current_user.is_admin_of(project):
        abort(403)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted.', 'success')
    return redirect(url_for('projects'))


@app.route('/projects/<int:project_id>/members/add', methods=['POST'])
@login_required
def add_member(project_id):
    project = Project.query.get_or_404(project_id)
    if not current_user.is_admin_of(project):
        abort(403)
    email = request.form.get('email', '').strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found.', 'error')
    elif user in project.members:
        flash('User is already a member.', 'info')
    else:
        stmt = project_members.insert().values(
            user_id=user.id, project_id=project.id, role='Member'
        )
        db.session.execute(stmt)
        db.session.commit()
        flash(f'{user.name} added to project.', 'success')
    return redirect(url_for('project_detail', project_id=project_id))


@app.route('/projects/<int:project_id>/members/<int:user_id>/remove', methods=['POST'])
@login_required
def remove_member(project_id, user_id):
    project = Project.query.get_or_404(project_id)
    if not current_user.is_admin_of(project):
        abort(403)
    if user_id == project.owner_id:
        flash("Cannot remove the project owner.", 'error')
        return redirect(url_for('project_detail', project_id=project_id))
    stmt = project_members.delete().where(
        project_members.c.user_id == user_id,
        project_members.c.project_id == project_id
    )
    db.session.execute(stmt)
    db.session.commit()
    flash('Member removed.', 'success')
    return redirect(url_for('project_detail', project_id=project_id))


# ─── Task Routes ─────────────────────────────────────────────────────────────

@app.route('/projects/<int:project_id>/tasks/new', methods=['GET', 'POST'])
@login_required
def new_task(project_id):
    project = Project.query.get_or_404(project_id)
    if not current_user.is_admin_of(project):
        abort(403)
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date_str = request.form.get('due_date')
        priority = request.form.get('priority', 'Medium')
        assignee_id = request.form.get('assignee_id') or None

        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        if not title:
            flash('Task title is required.', 'error')
        else:
            task = Task(title=title, description=description, due_date=due_date,
                        priority=priority, project_id=project_id,
                        assignee_id=int(assignee_id) if assignee_id else None)
            db.session.add(task)
            db.session.commit()
            flash('Task created!', 'success')
            return redirect(url_for('project_detail', project_id=project_id))
    return render_template('task_form.html', project=project, task=None)


@app.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    project = task.project
    is_admin = current_user.is_admin_of(project)
    is_assignee = task.assignee_id == current_user.id

    if current_user not in project.members:
        abort(403)

    if request.method == 'POST':
        if is_admin:
            task.title = request.form.get('title', '').strip()
            task.description = request.form.get('description', '').strip()
            due_date_str = request.form.get('due_date')
            task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
            task.priority = request.form.get('priority', 'Medium')
            assignee_id = request.form.get('assignee_id') or None
            task.assignee_id = int(assignee_id) if assignee_id else None

        # Both admin and assignee can update status
        if is_admin or is_assignee:
            task.status = request.form.get('status', task.status)

        db.session.commit()
        flash('Task updated!', 'success')
        return redirect(url_for('project_detail', project_id=project.id))
    return render_template('task_form.html', project=project, task=task, is_admin=is_admin)


@app.route('/tasks/<int:task_id>/status', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    project = task.project
    is_admin = current_user.is_admin_of(project)
    is_assignee = task.assignee_id == current_user.id

    if not (is_admin or is_assignee):
        return jsonify({'error': 'Forbidden'}), 403

    new_status = request.json.get('status')
    if new_status in ['To Do', 'In Progress', 'Done']:
        task.status = new_status
        db.session.commit()
        return jsonify({'success': True, 'status': task.status})
    return jsonify({'error': 'Invalid status'}), 400


@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    project = task.project
    if not current_user.is_admin_of(project):
        abort(403)
    project_id = task.project_id
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted.', 'success')
    return redirect(url_for('project_detail', project_id=project_id))


# ─── My Tasks ────────────────────────────────────────────────────────────────

@app.route('/my-tasks')
@login_required
def my_tasks():
    tasks = Task.query.filter_by(assignee_id=current_user.id).order_by(Task.due_date).all()
    return render_template('my_tasks.html', tasks=tasks, today=date.today())


# ─── Error Handlers ──────────────────────────────────────────────────────────

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', code=403, message="You don't have permission to access this page."), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404, message="Page not found."), 404


# ─── Init ────────────────────────────────────────────────────────────────────

_db_initialized = False

@app.before_request
def init_db():
    global _db_initialized
    if not _db_initialized:
        db.create_all()
        _db_initialized = True

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
