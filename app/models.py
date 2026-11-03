from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

def generate_uuid():
    return str(uuid.uuid4())

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    account_status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Medicine(db.Model):
    __tablename__ = 'medicines'
    medicine_id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    medicine_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80))
    strength = db.Column(db.String(50))
    prescription_required = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(20), default='Active')

class Inventory(db.Model):
    __tablename__ = 'inventory'
    inventory_id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    medicine_id = db.Column(db.String(36), db.ForeignKey('medicines.medicine_id'), nullable=False)
    available_quantity = db.Column(db.Integer, default=0, nullable=False)
    reserved_quantity = db.Column(db.Integer, default=0, nullable=False)
    fulfilled_quantity = db.Column(db.Integer, default=0, nullable=False)
    last_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)