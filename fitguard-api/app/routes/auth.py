from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from app.models.athlete import Athlete
from app.models.athlete_profile import AthleteProfile
from app.models.sport_setting import SportSetting
from app import db

auth_bp = Blueprint('auth', __name__)


def _safe_profile_lookup(athlete_id):
    try:
        return AthleteProfile.query.filter_by(athlete_id=athlete_id).first()
    except SQLAlchemyError:
        db.session.rollback()
        return None


def _safe_sport_setting_lookup(athlete_id):
    try:
        return SportSetting.query.filter_by(athlete_id=athlete_id).first()
    except SQLAlchemyError:
        db.session.rollback()
        return None

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'message': 'Missing required fields (email, password, name)'}), 400

    if Athlete.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400

    athlete = Athlete(
        name=data['name'],
        email=data['email'],
        age=data.get('age', 25),
        sport=data.get('sport', 'General Fitness'),
        weight=data.get('weight', 70.0),
        height=data.get('height', 175.0)
    )
    athlete.set_password(data['password'])
    db.session.add(athlete)
    db.session.flush()

    profile = AthleteProfile(
        athlete_id=athlete.id,
        injury_history=data.get('injury_history'),
        previous_injuries_count=int(data.get('previous_injuries_count', 0) or 0)
    )
    setting = SportSetting(
        athlete_id=athlete.id,
        sport=athlete.sport
    )
    db.session.add(profile)
    db.session.add(setting)
    db.session.commit()

    return jsonify({'message': 'Athlete created successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing email or password'}), 400

    athlete = Athlete.query.filter_by(email=data['email']).first()
    if not athlete or not athlete.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=str(athlete.id))
    profile = _safe_profile_lookup(athlete.id)
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'athlete': {
            **athlete.to_dict(),
            'profile': profile.to_dict() if profile else None
        }
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    current_user_id = int(get_jwt_identity())
    athlete = Athlete.query.get(current_user_id)
    if not athlete:
        return jsonify({'message': 'User not found'}), 404

    profile = _safe_profile_lookup(current_user_id)
    setting = _safe_sport_setting_lookup(current_user_id)

    payload = athlete.to_dict()
    payload['profile'] = profile.to_dict() if profile else None
    payload['sport_settings'] = setting.to_dict() if setting else None
    return jsonify(payload), 200
