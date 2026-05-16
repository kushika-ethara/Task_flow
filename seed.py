"""
Run this script once to populate demo data:
    python seed.py
"""
from app import app, db, User, Project, Task, project_members
from datetime import date, timedelta

with app.app_context():
    db.drop_all()
    db.create_all()

    # Create users
    admin = User(name='Alice Admin', email='alice@demo.com')
    admin.set_password('password')
    member = User(name='Bob Member', email='bob@demo.com')
    member.set_password('password')
    db.session.add_all([admin, member])
    db.session.flush()

    # Create project
    project = Project(name='Website Redesign', description='Revamping the company website with a modern look.', owner_id=admin.id)
    db.session.add(project)
    db.session.flush()

    # Add members
    db.session.execute(project_members.insert().values(user_id=admin.id, project_id=project.id, role='Admin'))
    db.session.execute(project_members.insert().values(user_id=member.id, project_id=project.id, role='Member'))

    # Add tasks
    tasks = [
        Task(title='Create wireframes', description='Design wireframes for all main pages.', priority='High', status='Done',
             due_date=date.today() - timedelta(days=5), project_id=project.id, assignee_id=admin.id),
        Task(title='Set up CI/CD pipeline', description='Configure GitHub Actions for deployment.', priority='High', status='In Progress',
             due_date=date.today() + timedelta(days=3), project_id=project.id, assignee_id=member.id),
        Task(title='Write unit tests', description='Cover all API endpoints with tests.', priority='Medium', status='To Do',
             due_date=date.today() + timedelta(days=7), project_id=project.id, assignee_id=member.id),
        Task(title='Update homepage copy', description='Rewrite homepage hero text and CTAs.', priority='Low', status='To Do',
             due_date=date.today() - timedelta(days=1), project_id=project.id, assignee_id=None),
        Task(title='Deploy to production', description='Final deployment after QA sign-off.', priority='High', status='To Do',
             due_date=date.today() + timedelta(days=14), project_id=project.id, assignee_id=admin.id),
    ]
    db.session.add_all(tasks)
    db.session.commit()

    print("✅ Demo data seeded!")
    print("   Admin:  alice@demo.com / password")
    print("   Member: bob@demo.com   / password")
