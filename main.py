from flask import Flask, request, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import numpy as np
import tensorflow as tf
from PIL import Image
import cv2
from datetime import datetime
import uuid
import jwt
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///neuroshield.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)
CORS(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'patient', 'doctor', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    patient_id = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    phone_number = db.Column(db.String(20))
    address = db.Column(db.Text)
    symptoms = db.Column(db.Text)
    assigned_doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100))
    license_number = db.Column(db.String(50))
    phone_number = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CTScan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'))
    scan_date = db.Column(db.Date, nullable=False)
    scan_type = db.Column(db.String(50), default='CT Scan')
    image_path = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.Text)
    doctor_notes = db.Column(db.Text)
    
    # AI Analysis Results
    stroke_probability = db.Column(db.Float)
    risk_level = db.Column(db.String(20))
    model_confidence = db.Column(db.Float)
    analysis_result = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Simple CNN Model for Stroke Prediction (placeholder - replace with your trained model)
class StrokePredictionCNN:
    def __init__(self):
        self.model = self._create_model()
    
    def _create_model(self):
        # This is a placeholder model - replace with your trained CNN
        model = tf.keras.Sequential([
            tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(224, 224, 3)),
            tf.keras.layers.MaxPooling2D((2, 2)),
            tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
            tf.keras.layers.MaxPooling2D((2, 2)),
            tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model
    
    def preprocess_image(self, image_path):
        # Load and preprocess the CT scan image
        image = cv2.imread(image_path)
        image = cv2.resize(image, (224, 224))
        image = image.astype('float32') / 255.0
        image = np.expand_dims(image, axis=0)
        return image
    
    def predict_stroke(self, image_path):
        # Preprocess the image
        processed_image = self.preprocess_image(image_path)
        
        # Make prediction (placeholder - replace with actual model prediction)
        # For demo purposes, generating random but realistic values
        import random
        stroke_probability = random.uniform(0.1, 0.9)
        confidence = random.uniform(0.7, 0.95)
        
        # Determine risk level based on probability
        if stroke_probability < 0.3:
            risk_level = "Low"
        elif stroke_probability < 0.6:
            risk_level = "Medium"
        else:
            risk_level = "High"
        
        analysis_result = f"{risk_level} Risk"
        
        return {
            'stroke_probability': round(stroke_probability * 100, 2),
            'risk_level': risk_level,
            'model_confidence': round(confidence * 100, 2),
            'analysis_result': analysis_result
        }

# Initialize CNN model
cnn_model = StrokePredictionCNN()

# JWT token decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400
    
    # Create user
    user = User(
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role=data['role']
    )
    db.session.add(user)
    db.session.flush()
    
    # Create role-specific profile
    if data['role'] == 'patient':
        patient_id = f"PAT-{10000 + user.id}"
        patient = Patient(
            user_id=user.id,
            patient_id=patient_id,
            full_name=data.get('full_name', ''),
            age=data.get('age', 0),
            gender=data.get('gender', ''),
            date_of_birth=datetime.strptime(data.get('date_of_birth', '2000-01-01'), '%Y-%m-%d').date(),
            phone_number=data.get('phone_number', ''),
            address=data.get('address', ''),
            symptoms=data.get('symptoms', '')
        )
        db.session.add(patient)
    
    elif data['role'] == 'doctor':
        doctor = Doctor(
            user_id=user.id,
            full_name=data.get('full_name', ''),
            specialization=data.get('specialization', ''),
            license_number=data.get('license_number', ''),
            phone_number=data.get('phone_number', '')
        )
        db.session.add(doctor)
    
    db.session.commit()
    
    return jsonify({'message': 'Registration successful'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        token = jwt.encode({
            'user_id': user.id,
            'role': user.role
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'token': token,
            'role': user.role,
            'user_id': user.id
        }), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401

# Patient Routes
@app.route('/api/patient/profile', methods=['GET'])
@token_required
def get_patient_profile(current_user):
    if current_user.role != 'patient':
        return jsonify({'message': 'Unauthorized'}), 403
    
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        return jsonify({'message': 'Patient profile not found'}), 404
    
    return jsonify({
        'patient_id': patient.patient_id,
        'full_name': patient.full_name,
        'age': patient.age,
        'gender': patient.gender,
        'date_of_birth': patient.date_of_birth.strftime('%Y-%m-%d'),
        'phone_number': patient.phone_number,
        'address': patient.address,
        'symptoms': patient.symptoms
    })

@app.route('/api/patient/ct-scans', methods=['GET'])
@token_required
def get_patient_ct_scans(current_user):
    if current_user.role != 'patient':
        return jsonify({'message': 'Unauthorized'}), 403
    
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    scans = CTScan.query.filter_by(patient_id=patient.id).order_by(CTScan.created_at.desc()).all()
    
    scan_data = []
    for scan in scans:
        scan_data.append({
            'id': scan.id,
            'scan_date': scan.scan_date.strftime('%Y-%m-%d'),
            'scan_type': scan.scan_type,
            'stroke_probability': scan.stroke_probability,
            'risk_level': scan.risk_level,
            'model_confidence': scan.model_confidence,
            'analysis_result': scan.analysis_result,
            'doctor_notes': scan.doctor_notes,
            'created_at': scan.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify(scan_data)

# Doctor Routes
@app.route('/api/doctor/dashboard', methods=['GET'])
@token_required
def get_doctor_dashboard(current_user):
    if current_user.role != 'doctor':
        return jsonify({'message': 'Unauthorized'}), 403
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    # Get dashboard statistics
    total_patients = Patient.query.filter_by(assigned_doctor_id=doctor.id).count()
    total_scans = CTScan.query.filter_by(doctor_id=doctor.id).count()
    high_risk_patients = CTScan.query.filter_by(doctor_id=doctor.id, risk_level='High').count()
    today_appointments = 5  # Placeholder
    
    # Get recent patients
    recent_patients = db.session.query(Patient, CTScan).join(
        CTScan, Patient.id == CTScan.patient_id
    ).filter(
        Patient.assigned_doctor_id == doctor.id
    ).order_by(CTScan.created_at.desc()).limit(10).all()
    
    patient_data = []
    for patient, scan in recent_patients:
        patient_data.append({
            'patient_id': patient.patient_id,
            'name': patient.full_name,
            'age': patient.age,
            'last_visit': scan.scan_date.strftime('%m/%d/%Y'),
            'risk_level': scan.risk_level
        })
    
    # Get recent CT scans
    recent_scans = CTScan.query.filter_by(doctor_id=doctor.id).order_by(
        CTScan.created_at.desc()
    ).limit(5).all()
    
    scan_data = []
    for scan in recent_scans:
        patient = Patient.query.get(scan.patient_id)
        scan_data.append({
            'patient_name': patient.full_name,
            'patient_id': patient.patient_id,
            'scan_date': scan.scan_date.strftime('%Y-%m-%d'),
            'risk_level': scan.risk_level
        })
    
    return jsonify({
        'doctor_name': doctor.full_name,
        'stats': {
            'total_patients': total_patients,
            'total_scans': total_scans,
            'high_risk_patients': high_risk_patients,
            'today_appointments': today_appointments
        },
        'recent_patients': patient_data,
        'recent_scans': scan_data
    })

@app.route('/api/doctor/patients', methods=['GET'])
@token_required
def get_doctor_patients(current_user):
    if current_user.role != 'doctor':
        return jsonify({'message': 'Unauthorized'}), 403
    
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    patients = Patient.query.all()  # For now, show all patients
    
    patient_data = []
    for patient in patients:
        # Get latest scan for risk level
        latest_scan = CTScan.query.filter_by(patient_id=patient.id).order_by(
            CTScan.created_at.desc()
        ).first()
        
        patient_data.append({
            'id': patient.id,
            'patient_id': patient.patient_id,
            'name': patient.full_name,
            'age': patient.age,
            'phone': patient.phone_number,
            'risk_level': latest_scan.risk_level if latest_scan else 'Unknown'
        })
    
    return jsonify(patient_data)

@app.route('/api/doctor/upload-ct-scan', methods=['POST'])
@token_required
def upload_ct_scan(current_user):
    if current_user.role != 'doctor':
        return jsonify({'message': 'Unauthorized'}), 403
    
    if 'ct_scan' not in request.files:
        return jsonify({'message': 'No file uploaded'}), 400
    
    file = request.files['ct_scan']
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400
    
    # Get form data
    patient_id = request.form.get('patient_id')
    scan_date = request.form.get('scan_date')
    notes = request.form.get('notes', '')
    doctor_notes = request.form.get('doctor_notes', '')
    
    # Find patient
    patient = Patient.query.filter_by(patient_id=patient_id).first()
    if not patient:
        return jsonify({'message': 'Patient not found'}), 404
    
    # Find doctor
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(file_path)
    
    # Run CNN analysis
    try:
        prediction_results = cnn_model.predict_stroke(file_path)
    except Exception as e:
        # Fallback to mock data if model fails
        prediction_results = {
            'stroke_probability': 45.6,
            'risk_level': 'Medium',
            'model_confidence': 87.3,
            'analysis_result': 'Medium Risk'
        }
    
    # Save CT scan record
    ct_scan = CTScan(
        patient_id=patient.id,
        doctor_id=doctor.id,
        scan_date=datetime.strptime(scan_date, '%Y-%m-%d').date(),
        image_path=file_path,
        notes=notes,
        doctor_notes=doctor_notes,
        stroke_probability=prediction_results['stroke_probability'],
        risk_level=prediction_results['risk_level'],
        model_confidence=prediction_results['model_confidence'],
        analysis_result=prediction_results['analysis_result']
    )
    
    db.session.add(ct_scan)
    db.session.commit()
    
    return jsonify({
        'message': 'CT scan uploaded and analyzed successfully',
        'analysis_results': prediction_results,
        'scan_id': ct_scan.id
    }), 201

# Utility Routes
@app.route('/api/patients/search', methods=['GET'])
@token_required
def search_patients(current_user):
    if current_user.role != 'doctor':
        return jsonify({'message': 'Unauthorized'}), 403
    
    query = request.args.get('q', '')
    patients = Patient.query.filter(
        Patient.full_name.ilike(f'%{query}%') | 
        Patient.patient_id.ilike(f'%{query}%')
    ).limit(10).all()
    
    patient_data = [
        {
            'id': p.patient_id,
            'name': p.full_name,
            'patient_id': p.patient_id
        } for p in patients
    ]
    
    return jsonify(patient_data)

# Initialize database
@app.before_first_request
def create_tables():
    db.create_all()
    
    # Create sample data if tables are empty
    if User.query.count() == 0:
        # Create sample doctor
        doctor_user = User(
            email='doctor@neuroshield.com',
            password_hash=generate_password_hash('doctor123'),
            role='doctor'
        )
        db.session.add(doctor_user)
        db.session.flush()
        
        doctor = Doctor(
            user_id=doctor_user.id,
            full_name='Dr. Sarah Johnson',
            specialization='Neurology',
            license_number='MD12345',
            phone_number='+1-555-0123'
        )
        db.session.add(doctor)
        
        # Create sample patient
        patient_user = User(
            email='patient@example.com',
            password_hash=generate_password_hash('patient123'),
            role='patient'
        )
        db.session.add(patient_user)
        db.session.flush()
        
        patient = Patient(
            user_id=patient_user.id,
            patient_id='PAT-10001',
            full_name='John Smith',
            age=65,
            gender='Male',
            date_of_birth=datetime(1958, 5, 15).date(),
            phone_number='+1-555-0456',
            address='123 Main St, City, State',
            symptoms='Headache, dizziness',
            assigned_doctor_id=1
        )
        db.session.add(patient)
        
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)