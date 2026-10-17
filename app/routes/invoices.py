from datetime import datetime, date
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash
)
from app import db
from app.models import Invoice, InvoiceItem, Client, Project

invoices_bp = Blueprint('invoices', __name__)


def _parse_date(value, default=None):
    if not value:
        return default
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return default


def _parse_decimal(value, default=0.0):
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return default


def _parse_int(value, default=1):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _generate_invoice_number():
    today = date.today()
    prefix = 'INV-{}-'.format(today.strftime('%Y%m%d'))
    last = Invoice.query.filter(
        Invoice.invoice_number.like('{}%'.format(prefix))
    ).order_by(Invoice.id.desc()).first()

    seq = 1
    if last and last.invoice_number:
        try:
            seq = int(last.invoice_number.split('-')[-1]) + 1
        except ValueError:
            seq = 1
    return '{}{:04d}'.format(prefix, seq)


@invoices_bp.route('/')
def list_invoices():
    status_filter = request.args.get('status', '').strip()
    query = Invoice.query
    if status_filter and status_filter in Invoice.STATUSES:
        query = query.filter_by(status=status_filter)
    invoices = query.order_by(Invoice.created_at.desc()).all()

    counts = {}
    for s in Invoice.STATUSES:
        counts[s] = Invoice.query.filter_by(status=s).count()

    return render_template(
        'invoices/list.html',
        invoices=invoices,
        statuses=Invoice.STATUSES,
        status_filter=status_filter,
        counts=counts,
    )


@invoices_bp.route('/create', methods=['GET', 'POST'])
def create_invoice():
    clients = Client.query.order_by(Client.name.asc()).all()
    projects = Project.query.order_by(Project.title.asc()).all()

    if request.method == 'POST':
        client_id = request.form.get('client_id', type=int)
        project_id = request.form.get('project_id', type=int) or None
        issue_date = _parse_date(request.form.get('issue_date'),
                                 date.today())
        due_date = _parse_date(request.form.get('due_date'),
                               date.today())
        status = request.form.get('status', 'Unpaid')
        tax_rate = _parse_decimal(request.form.get('tax_rate'))

        if not client_id:
            flash('Client is required.', 'danger')
            return render_template('invoices/form.html', invoice=None,
                                   clients=clients, projects=projects,
                                   form=request.form, next_number=_generate_invoice_number())

        invoice = Invoice(
            invoice_number=_generate_invoice_number(),
            client_id=client_id,
            project_id=project_id,
            issue_date=issue_date,
            due_date=due_date,
            status=status,
            tax_rate=tax_rate,
            notes=request.form.get('notes', '').strip(),
        )
        db.session.add(invoice)
        db.session.flush()

        descriptions = request.form.getlist('item_description[]')
        quantities = request.form.getlist('item_quantity[]')
        prices = request.form.getlist('item_unit_price[]')

        for i, desc in enumerate(descriptions):
            desc = (desc or '').strip()
            if not desc:
                continue
            qty = _parse_int(quantities[i] if i < len(quantities) else 1, 1)
            price = _parse_decimal(prices[i] if i < len(prices) else 0)
            item = InvoiceItem(
                invoice_id=invoice.id,
                description=desc,
                quantity=qty,
                unit_price=price,
                subtotal=round(qty * price, 2),
            )
            db.session.add(item)

        db.session.flush()
        invoice.items  # refresh
        invoice.recalculate()
        db.session.commit()
        flash('Invoice created successfully.', 'success')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice.id))

    return render_template('invoices/form.html', invoice=None,
                           clients=clients, projects=projects,
                           form={}, next_number=_generate_invoice_number())


@invoices_bp.route('/<int:invoice_id>/edit', methods=['GET', 'POST'])
def edit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    clients = Client.query.order_by(Client.name.asc()).all()
    projects = Project.query.order_by(Project.title.asc()).all()

    if request.method == 'POST':
        client_id = request.form.get('client_id', type=int)
        if not client_id:
            flash('Client is required.', 'danger')
            return render_template('invoices/form.html', invoice=invoice,
                                   clients=clients, projects=projects,
                                   form=request.form,
                                   next_number=invoice.invoice_number)

        invoice.client_id = client_id
        invoice.project_id = request.form.get('project_id', type=int) or None
        invoice.issue_date = _parse_date(request.form.get('issue_date'),
                                         invoice.issue_date)
        invoice.due_date = _parse_date(request.form.get('due_date'),
                                       invoice.due_date)
        invoice.status = request.form.get('status', invoice.status)
        invoice.tax_rate = _parse_decimal(request.form.get('tax_rate'))
        invoice.notes = request.form.get('notes', '').strip()

        # Replace all items
        for item in list(invoice.items):
            db.session.delete(item)
        db.session.flush()

        descriptions = request.form.getlist('item_description[]')
        quantities = request.form.getlist('item_quantity[]')
        prices = request.form.getlist('item_unit_price[]')

        for i, desc in enumerate(descriptions):
            desc = (desc or '').strip()
            if not desc:
                continue
            qty = _parse_int(quantities[i] if i < len(quantities) else 1, 1)
            price = _parse_decimal(prices[i] if i < len(prices) else 0)
            item = InvoiceItem(
                invoice_id=invoice.id,
                description=desc,
                quantity=qty,
                unit_price=price,
                subtotal=round(qty * price, 2),
            )
            db.session.add(item)

        db.session.flush()
        invoice.items
        invoice.recalculate()
        db.session.commit()
        flash('Invoice updated.', 'success')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice.id))

    return render_template('invoices/form.html', invoice=invoice,
                           clients=clients, projects=projects,
                           form={}, next_number=invoice.invoice_number)


@invoices_bp.route('/<int:invoice_id>')
def view_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    tax_amount = round(float(invoice.subtotal or 0) *
                       (float(invoice.tax_rate or 0) / 100.0), 2)
    return render_template('invoices/view.html', invoice=invoice,
                           tax_amount=tax_amount)


@invoices_bp.route('/<int:invoice_id>/delete', methods=['POST'])
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    try:
        db.session.delete(invoice)
        db.session.commit()
        flash('Invoice deleted.', 'success')
    except Exception:
        db.session.rollback()
        flash('Unable to delete invoice.', 'danger')
    return redirect(url_for('invoices.list_invoices'))


@invoices_bp.route('/<int:invoice_id>/mark-paid', methods=['POST'])
def mark_paid(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.status = 'Paid'
    db.session.commit()
    flash('Invoice marked as paid.', 'success')
    return redirect(url_for('invoices.view_invoice', invoice_id=invoice.id))