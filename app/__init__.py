
from flask import Flask, jsonify
from app.models import db
import os


def create_app(test_config=None):
    app = Flask(__name__)

    basedir = os.path.abspath(
        os.path.dirname(os.path.dirname(__file__))
    )

    app.config.update({
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + os.path.join(
            basedir, 'team9.db'
        ),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': os.environ.get(
            'SECRET_KEY', 'project47-development-key'
        ),
        'NOTIFICATION_MAX_RETRIES': 3
    })

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from app.auth import auth_bp
    from app.medicine import medicine_bp
    from app.inventory import inventory_bp
    from app.prescription import prescription_bp
    from app.booking import booking_bp
    from app.waitlist import waitlist_bp
    from app.notification import notification_bp
    from app.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(medicine_bp, url_prefix='/api/medicines')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    app.register_blueprint(prescription_bp, url_prefix='/api/prescriptions')
    app.register_blueprint(booking_bp, url_prefix='/api/bookings')
    app.register_blueprint(waitlist_bp, url_prefix='/api/waitlist')
    app.register_blueprint(notification_bp,url_prefix='/api/notifications')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    with app.app_context():
        db.create_all()

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            "status": "healthy",
            "project": "Project 47 Booking Engine"
        }), 200

    return app
