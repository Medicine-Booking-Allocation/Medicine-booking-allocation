
from flask import Blueprint, request, jsonify
from app.models import db, Medicine, Inventory, utc_now
from app.auth_utils import role_required

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/add', methods=['POST'])
@role_required('Pharmacy Staff', 'Administrator')
def add_stock():
    data = request.get_json()

    if not data or not data.get('medicine_id') or 'quantity' not in data:
        return jsonify({"error": "medicine_id and quantity are required"}), 400

    quantity = data.get('quantity')

    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    medicine = db.session.get(Medicine, data['medicine_id'])

    if not medicine or medicine.status != 'Active':
        return jsonify({"error": "Medicine not found or inactive"}), 404

    inventory = Inventory.query.filter_by(
        medicine_id=data['medicine_id']
    ).first()

    if not inventory:
        inventory = Inventory(
            medicine_id=data['medicine_id'],
            available_quantity=0,
            reserved_quantity=0,
            fulfilled_quantity=0
        )
        db.session.add(inventory)

    inventory.available_quantity += quantity
    inventory.last_updated_at = utc_now()

    db.session.commit()

    return jsonify({
        "message": "Stock added successfully",
        "medicine_id": medicine.medicine_id,
        "available_quantity": inventory.available_quantity
    }), 200


@inventory_bp.route('/reserve', methods=['POST'])
def reserve_stock():
    data = request.get_json()

    if not data or not data.get('medicine_id') or 'quantity' not in data:
        return jsonify({"error": "medicine_id and quantity are required"}), 400

    quantity = data.get('quantity')

    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    inventory = Inventory.query.filter_by(
        medicine_id=data['medicine_id']
    ).first()

    if not inventory:
        return jsonify({"error": "Inventory not found"}), 404

    if inventory.available_quantity < quantity:
        return jsonify({"error": "Insufficient available stock"}), 400

    inventory.available_quantity -= quantity
    inventory.reserved_quantity += quantity
    inventory.last_updated_at = utc_now()

    db.session.commit()

    return jsonify({
        "message": "Stock reserved successfully",
        "available_quantity": inventory.available_quantity,
        "reserved_quantity": inventory.reserved_quantity
    }), 200


@inventory_bp.route('/fulfil', methods=['POST'])
def fulfil_stock():
    data = request.get_json()

    if not data or not data.get('medicine_id') or 'quantity' not in data:
        return jsonify({"error": "medicine_id and quantity are required"}), 400

    quantity = data.get('quantity')

    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    inventory = Inventory.query.filter_by(
        medicine_id=data['medicine_id']
    ).first()

    if not inventory:
        return jsonify({"error": "Inventory not found"}), 404

    if inventory.reserved_quantity < quantity:
        return jsonify({"error": "Insufficient reserved stock"}), 400

    inventory.reserved_quantity -= quantity
    inventory.fulfilled_quantity += quantity
    inventory.last_updated_at = utc_now()

    db.session.commit()

    return jsonify({
        "message": "Stock fulfilled successfully",
        "reserved_quantity": inventory.reserved_quantity,
        "fulfilled_quantity": inventory.fulfilled_quantity
    }), 200


@inventory_bp.route('/release', methods=['POST'])
def release_stock():
    data = request.get_json()

    if not data or not data.get('medicine_id') or 'quantity' not in data:
        return jsonify({"error": "medicine_id and quantity are required"}), 400

    quantity = data.get('quantity')

    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    inventory = Inventory.query.filter_by(
        medicine_id=data['medicine_id']
    ).first()

    if not inventory:
        return jsonify({"error": "Inventory not found"}), 404

    if inventory.reserved_quantity < quantity:
        return jsonify({"error": "Insufficient reserved stock"}), 400

    inventory.reserved_quantity -= quantity
    inventory.available_quantity += quantity
    inventory.last_updated_at = utc_now()

    db.session.commit()

    return jsonify({
        "message": "Reserved stock released successfully",
        "available_quantity": inventory.available_quantity,
        "reserved_quantity": inventory.reserved_quantity
    }), 200


@inventory_bp.route('/<medicine_id>', methods=['GET'])
def get_inventory(medicine_id):
    inventory = Inventory.query.filter_by(
        medicine_id=medicine_id
    ).first()

    if not inventory:
        return jsonify({"error": "Inventory not found"}), 404

    return jsonify({
        "medicine_id": inventory.medicine_id,
        "available_quantity": inventory.available_quantity,
        "reserved_quantity": inventory.reserved_quantity,
        "fulfilled_quantity": inventory.fulfilled_quantity,
        "last_updated_at": inventory.last_updated_at.isoformat()
    }), 200
