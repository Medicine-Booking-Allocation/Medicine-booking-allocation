from flask import Flask, jsonify
from app.models import db
import os

def create_app():
    app = Flask(__name__)
    
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'team9.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Import and register your new blueprints here
    from app.auth import auth_bp
    from app.medicine import medicine_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(medicine_bp, url_prefix='/api/medicines')

    with app.app_context():
        db.create_all()

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy", "project": "Project 47 Booking Engine"}), 200

    return app