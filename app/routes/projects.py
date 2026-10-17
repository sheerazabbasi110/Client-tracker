from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash
)
from app import db
from app.models import Project, Client

projects_bp = Blueprint('projects', __name__)


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def _parse_decimal(value, default=0.0):
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return default


@projects_bp.route('/')
def list_projects():
    status_filter = request.args.get('status', '').strip()
    query = Project.query
    if status_filter and status_filter in Project.STATUSES:
        query = query.filter_by(status=status_filter)
    projects = query.order_by(Project.created_at.desc()).all()

    counts = {}
    for s in Project.STATUSES:
        counts[s] = Project.query.filter_by(status=s).count()

    return render_template(
        'projects/list.html',
        projects=projects,
        statuses=Project.STATUSES,
        status_filter=status_filter,
        counts=counts,
    )


@projects_bp.route('/create', methods=['GET', 'POST'])
def create_project():
    clients = Client.query.order_by(Client.name.asc()).all()

    if request.method == 'POST':
        client_id = request.form.get('client_id', type=int)
        title = request.form.get('title', '').strip()

        if not client_id or not title:
            flash('Client and title are required.', 'danger')
            return render_template('projects/form.html', project=None,
                                   clients=clients, form=request.form)

        project = Project(
            client_id=client_id,
            title=title,
            description=request.form.get('description', '').strip(),
            status=request.form.get('status', 'In Progress'),
            deadline=_parse_date(request.form.get('deadline')),
            budget=_parse_decimal(request.form.get('budget')),
        )
        db.session.add(project)
        db.session.commit()
        flash('Project created successfully.', 'success')
        return redirect(url_for('projects.list_projects'))

    return render_template('projects/form.html', project=None,
                           clients=clients, form={})


@projects_bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    clients = Client.query.order_by(Client.name.asc()).all()

    if request.method == 'POST':
        client_id = request.form.get('client_id', type=int)
        title = request.form.get('title', '').strip()
        if not client_id or not title:
            flash('Client and title are required.', 'danger')
            return render_template('projects/form.html', project=project,
                                   clients=clients, form=request.form)

        project.client_id = client_id
        project.title = title
        project.description = request.form.get('description', '').strip()
        project.status = request.form.get('status', project.status)
        project.deadline = _parse_date(request.form.get('deadline'))
        project.budget = _parse_decimal(request.form.get('budget'))
        db.session.commit()
        flash('Project updated.', 'success')
        return redirect(url_for('projects.list_projects'))

    return render_template('projects/form.html', project=project,
                           clients=clients, form={})


@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    try:
        db.session.delete(project)
        db.session.commit()
        flash('Project deleted.', 'success')
    except Exception:
        db.session.rollback()
        flash('Unable to delete project.', 'danger')
    return redirect(url_for('projects.list_projects'))