from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify
)
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import Client

clients_bp = Blueprint('clients', __name__)


@clients_bp.route('/')
def list_clients():
    q = request.args.get('q', '').strip()
    query = Client.query
    if q:
        like = '%{}%'.format(q)
        query = query.filter(
            db.or_(
                Client.name.ilike(like),
                Client.company.ilike(like),
                Client.email.ilike(like),
            )
        )
    clients = query.order_by(Client.name.asc()).all()
    return render_template('clients/list.html', clients=clients, q=q)


@clients_bp.route('/search')
def search_clients():
    q = request.args.get('q', '').strip()
    query = Client.query
    if q:
        like = '%{}%'.format(q)
        query = query.filter(
            db.or_(
                Client.name.ilike(like),
                Client.company.ilike(like),
                Client.email.ilike(like),
            )
        )
    clients = query.order_by(Client.name.asc()).limit(20).all()
    return jsonify([c.to_dict() for c in clients])


@clients_bp.route('/create', methods=['GET', 'POST'])
def create_client():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()

        if not name or not email:
            flash('Name and email are required.', 'danger')
            return render_template('clients/form.html', client=None,
                                   form=request.form)

        existing = Client.query.filter_by(email=email).first()
        if existing:
            flash('A client with this email already exists.', 'warning')
            return render_template('clients/form.html', client=None,
                                   form=request.form)

        client = Client(
            name=name,
            company=request.form.get('company', '').strip(),
            email=email,
            phone=request.form.get('phone', '').strip(),
            address=request.form.get('address', '').strip(),
        )
        try:
            db.session.add(client)
            db.session.commit()
            flash('Client created successfully.', 'success')
            return redirect(url_for('clients.list_clients'))
        except IntegrityError:
            db.session.rollback()
            flash('Database error: email must be unique.', 'danger')

    return render_template('clients/form.html', client=None, form={})


@clients_bp.route('/<int:client_id>/edit', methods=['GET', 'POST'])
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()

        if not name or not email:
            flash('Name and email are required.', 'danger')
            return render_template('clients/form.html', client=client,
                                   form=request.form)

        dup = Client.query.filter(
            Client.email == email, Client.id != client.id
        ).first()
        if dup:
            flash('Another client already uses this email.', 'warning')
            return render_template('clients/form.html', client=client,
                                   form=request.form)

        client.name = name
        client.company = request.form.get('company', '').strip()
        client.email = email
        client.phone = request.form.get('phone', '').strip()
        client.address = request.form.get('address', '').strip()
        try:
            db.session.commit()
            flash('Client updated successfully.', 'success')
            return redirect(url_for('clients.list_clients'))
        except IntegrityError:
            db.session.rollback()
            flash('Database error updating client.', 'danger')

    return render_template('clients/form.html', client=client, form={})


@clients_bp.route('/<int:client_id>/delete', methods=['POST'])
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    try:
        db.session.delete(client)
        db.session.commit()
        flash('Client deleted.', 'success')
    except Exception:
        db.session.rollback()
        flash('Unable to delete client.', 'danger')
    return redirect(url_for('clients.list_clients'))