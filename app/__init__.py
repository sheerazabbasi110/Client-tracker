import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from app.routes.main import main_bp
    from app.routes.clients import clients_bp
    from app.routes.projects import projects_bp
    from app.routes.invoices import invoices_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(clients_bp, url_prefix='/clients')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(invoices_bp, url_prefix='/invoices')

    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()

    @app.template_filter('currency')
    def currency_filter(value):
        try:
            return "{:,.2f}".format(float(value or 0))
        except (TypeError, ValueError):
            return "0.00"

    return app