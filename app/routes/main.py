from datetime import date
from flask import Blueprint, render_template
from sqlalchemy import func
from app import db
from app.models import Client, Project, Invoice

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def dashboard():
    active_clients = Client.query.count()
    ongoing_projects = Project.query.filter(
        Project.status.in_(['In Progress', 'Under Review'])
    ).count()

    pending_value = db.session.query(
        func.coalesce(func.sum(Invoice.total_amount), 0)
    ).filter(Invoice.status.in_(['Unpaid', 'Overdue', 'Draft'])).scalar()

    paid_value = db.session.query(
        func.coalesce(func.sum(Invoice.total_amount), 0)
    ).filter(Invoice.status == 'Paid').scalar()

    recent_invoices = Invoice.query.order_by(Invoice.created_at.desc()).limit(5).all()
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()

    today = date.today()
    overdue_count = Invoice.query.filter(
        Invoice.status.in_(['Unpaid', 'Overdue']),
        Invoice.due_date < today,
    ).count()

    return render_template(
        'dashboard.html',
        active_clients=active_clients,
        ongoing_projects=ongoing_projects,
        pending_value=float(pending_value or 0),
        paid_value=float(paid_value or 0),
        recent_invoices=recent_invoices,
        recent_projects=recent_projects,
        overdue_count=overdue_count,
    )