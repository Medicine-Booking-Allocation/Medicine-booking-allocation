from flask import Blueprint, request, jsonify
from app.models import db, Medicine, Inventory

medicine_bp = Blueprint('medicine', __name__)

@medicine_bp.route('/search', methods=['GET'])
def search_medicines():
    query = request.args.get('q', '').strip()
    
    if not query:
        medicines = Medicine.query.filter_by(status='Active').all()
    else:
        # Search by name or category
        medicines = Medicine.query.filter(
            (Medicine.medicine_name.ilike(f"%{query}%")) | 
            (Medicine.category.ilike(f"%{query}%"))
        ).filter_by(status='Active').all()

    results = []
    for med in medicines:
        inv = Inventory.query.filter_by(medicine_id=med.medicine_id).first()
        available_qty = inv.available_quantity if inv else 0
        results.append({
            "medicine_id": med.medicine_id,
            "medicine_name": med.medicine_name,
            "category": med.category,
            "strength": med.strength,
            "prescription_required": med.prescription_required,
            "available_quantity": available_qty
        })

    return jsonify({"medicines": results}), 200