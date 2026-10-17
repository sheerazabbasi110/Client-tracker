from datetime import datetime, timezone
from sqlalchemy import func
from app import db


class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now())

    projects = db.relationship(
        'Project', backref='client', lazy=True,
        cascade='all, delete-orphan'
    )
    invoices = db.relationship(
        'Invoice', backref='client', lazy=True,
        cascade='all, delete-orphan'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'company': self.company or '',
            'email': self.email,
            'phone': self.phone or '',
            'address': self.address or '',
        }

    def __repr__(self):
        return '<Client {}>'.format(self.name)


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_id = db.Column(
        db.Integer,
        db.ForeignKey('clients.id', ondelete='CASCADE'),
        nullable=False,
    )
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(30), default='In Progress')
    deadline = db.Column(db.Date)
    budget = db.Column(db.Numeric(10, 2), default=0.00)
    created_at = db.Column(db.DateTime, server_default=func.now())

    invoices = db.relationship(
        'Invoice', backref='project', lazy=True,
        passive_deletes=True
    )

    STATUSES = ['Not Started', 'In Progress', 'Under Review', 'Completed']

    def __repr__(self):
        return '<Project {}>'.format(self.title)


class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    client_id = db.Column(
        db.Integer,
        db.ForeignKey('clients.id', ondelete='CASCADE'),
        nullable=False,
    )
    project_id = db.Column(
        db.Integer,
        db.ForeignKey('projects.id', ondelete='SET NULL'),
        nullable=True,
    )
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Unpaid')
    tax_rate = db.Column(db.Numeric(5, 2), default=0.00)
    subtotal = db.Column(db.Numeric(10, 2), default=0.00)
    total_amount = db.Column(db.Numeric(10, 2), default=0.00)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now())

    items = db.relationship(
        'InvoiceItem', backref='invoice', lazy=True,
        cascade='all, delete-orphan'
    )

    STATUSES = ['Draft', 'Unpaid', 'Paid', 'Overdue']

    def recalculate(self):
        sub = sum(float(i.subtotal or 0) for i in self.items)
        self.subtotal = round(sub, 2)
        tax = round(sub * (float(self.tax_rate or 0) / 100.0), 2)
        self.total_amount = round(sub + tax, 2)

    def __repr__(self):
        return '<Invoice {}>'.format(self.invoice_number)


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_id = db.Column(
        db.Integer,
        db.ForeignKey('invoices.id', ondelete='CASCADE'),
        nullable=False,
    )
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)

    def __repr__(self):
        return '<InvoiceItem {}>'.format(self.description)