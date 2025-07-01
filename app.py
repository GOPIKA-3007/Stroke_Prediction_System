import os
import numpy as np
from flask import Flask, request, jsonify, session, send_from_directory, render_template, redirect, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image
import tensorflow as tf
from datetime import datetime
import json
from typing import Optional
import cv2

# Initialize Flask app with static folder configuration
app = Flask(__name__, 
            static_url_path='',
            static_folder='.',  # Serve static files from current directory
            template_folder='.')  # Use current directory for templates

# Configure CORS to allow credentials
CORS(app, 
     supports_credentials=True,
     resources={
         r"/*": {
             "origins": "*",
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"]
         }
     })

app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'

# Configure upload folder and file size limits
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'dcm'}

# In-memory storage for users and predictions
USERS = {
    'doctor1': {'password': 'doctor123', 'role': 'doctor'},
    'patient1': {'password': 'patient123', 'role': 'patient'},
    'krishna': {'password': 'krishna123', 'role': 'doctor'}  # Test user
}
predictions = {}

def load_model_safe():
    """Safely load the model with multiple format support and error handling"""
    try:
        # First try loading as .keras format
        if os.path.exists('model.keras'):
            print("Found .keras model, attempting to load...")
            model = tf.keras.models.load_model('model.keras')
            print("Successfully loaded .keras model!")
            return model
    except Exception as e:
        print(f"Error loading .keras model: {e}")

    try:
        # Then try loading as .h5 format
        if os.path.exists('model.h5'):
            print("Found .h5 model, attempting to load...")
            model = tf.keras.models.load_model('model.h5')
            print("Successfully loaded .h5 model!")
            return model
    except Exception as e:
        print(f"Error loading .h5 model: {e}")
        
    print("Failed to load model. Please ensure model files exist and are valid.")
    return None

# Load the model globally
MODEL = load_model_safe()

# Route for the root URL
@app.route('/')
def serve_index():
    # Clear any existing session to ensure fresh login
    session.clear()
    return send_from_directory('.', 'login.html')

@app.route('/<path:path>')
def serve_static(path):
    # For security, prevent direct access to protected pages without auth
    if path in ['doctor.html', 'patient.html'] and 'username' not in session:
        return redirect('/login.html')
    if path == 'CT_upload.html' and ('username' not in session or session.get('role') != 'doctor'):
        return redirect('/login.html')
    return send_from_directory('.', path)

# Route for login page
@app.route('/login')
def login_page():
    return send_from_directory('.', 'login.html')

# Route for patient page
@app.route('/patient')
def patient_page():
    return send_from_directory('.', 'patient.html')

# Route for doctor page
@app.route('/doctor')
def doctor_page():
    return send_from_directory('.', 'doctor.html')

# Route for admin page
@app.route('/admin')
def admin_page():
    return send_from_directory('.', 'admin.html')

# Route for CT upload page
@app.route('/ct-upload')
def ct_upload_page():
    return send_from_directory('.', 'CT_upload.html')

# Route for contact page
@app.route('/contact')
def contact_page():
    return send_from_directory('.', 'contact.html')

# Route for about page
@app.route('/about')
def about_page():
    return send_from_directory('.', 'about.html')

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image_path):
    """Preprocess the image for CNN prediction"""
    try:
        # Read image using cv2
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print("Failed to read image with cv2, trying PIL...")
            # Fallback to PIL if cv2 fails
            img = Image.open(image_path).convert('L')
            img = np.array(img)
        
        # Resize to 650x650
        img = cv2.resize(img, (650, 650))
        
        # Normalize to [0,1]
        img = img.astype('float32') / 255.0
        
        # Add batch and channel dimensions
        img = np.expand_dims(img, axis=0)  # Add batch dimension
        img = np.expand_dims(img, axis=-1)  # Add channel dimension
        
        return img
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None

def get_risk_level(probability):
    """Convert probability to risk level"""
    if probability < 0.3:
        return "Low Risk"
    elif probability < 0.7:
        return "Medium Risk"
    else:
        return "High Risk"

def get_medical_advice(risk_level):
    """Generate medical advice based on risk level"""
    advice = {
        "Low Risk": "Regular check-ups recommended. Maintain healthy lifestyle.",
        "Medium Risk": "Schedule follow-up with doctor. Consider preventive measures.",
        "High Risk": "Immediate medical attention recommended. Contact your healthcare provider."
    }
    return advice.get(risk_level, "Please consult with your healthcare provider.")

def predict_stroke(image_array: np.ndarray) -> float:
    """Make a prediction with proper error handling"""
    global MODEL
    try:
        # Ensure the model is loaded
        if MODEL is None:
            print("Model not loaded, attempting to reload...")
            MODEL = load_model_safe()
        
        if MODEL is None:
            print("Failed to load model, using random prediction")
            return float(np.random.random())
        
        # Ensure image array is the correct shape and type
        if not isinstance(image_array, np.ndarray):
            print("Input is not a numpy array")
            return float(np.random.random())
            
        # Add batch dimension if needed
        if len(image_array.shape) == 3:
            image_array = np.expand_dims(image_array, axis=0)
            
        # Ensure correct data type
        image_array = image_array.astype('float32')
        
        # Make prediction with error handling for different TensorFlow versions
        try:
            # First try the newer TensorFlow 2.x syntax
            prediction = MODEL.predict(image_array, verbose='auto')
        except TypeError:
            try:
                # Try without verbose parameter
                prediction = MODEL.predict(image_array)
            except Exception as e:
                print(f"Error during model prediction: {e}")
                return float(np.random.random())
        
        # Ensure we get a valid probability
        if isinstance(prediction, np.ndarray):
            probability = float(prediction[0][0])
        else:
            probability = float(prediction[0])
            
        probability = max(0.0, min(1.0, probability))  # Clip to [0,1]
        
        return probability
    except Exception as e:
        print(f"Error during prediction: {e}")
        # Return a random prediction for testing
        return float(np.random.random())

def get_secure_filename(file) -> Optional[str]:
    """Safely get a secure filename from a file object"""
    if not file or not file.filename:
        return None
    try:
        filename = secure_filename(str(file.filename))
        if not filename:
            return None
        return filename
    except Exception as e:
        print(f"Error securing filename: {e}")
        return None

@app.route('/api/register', methods=['POST'])
def register():
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
            
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'No data received'}), 400

        username = str(data.get('username', ''))
        password = str(data.get('password', ''))
        role = str(data.get('role', ''))

        if not username or not password or not role:
            return jsonify({'error': 'Missing registration data'}), 400

        if username in USERS:
            return jsonify({'error': 'Username already exists'}), 400

        USERS[username] = {
            'password': password,
            'role': role
        }

        return jsonify({'message': 'Registration successful'})
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({'error': 'Server error during registration'}), 500

@app.route('/api/verify-credentials', methods=['POST'])
def verify_credentials():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400
            
        username = data.get('username', '')
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        if username in USERS and USERS[username]['password'] == password:
            # Set session data immediately with role
            session['username'] = username
            session['role'] = USERS[username]['role']
            return jsonify({
                'message': 'Credentials verified',
                'role': USERS[username]['role']
            }), 200
        
        return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        print(f"Error in verify_credentials: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400

        username = data.get('username', '')
        password = data.get('password', '')
        role = data.get('role', '')

        if not all([username, password, role]):
            return jsonify({'error': 'All fields are required'}), 400

        if username not in USERS:
            return jsonify({'error': 'Invalid credentials'}), 401

        user = USERS[username]
        if user['password'] != password:
            return jsonify({'error': 'Invalid credentials'}), 401

        if user['role'] != role:
            return jsonify({'error': f'User is not registered as a {role}'}), 401

        # Set session data
        session['username'] = username
        session['role'] = role
        session.permanent = True  # Make session last longer
        
        return jsonify({
            'message': 'Login successful',
            'username': username,
            'role': role
        }), 200

    except Exception as e:
        print(f"Error in login: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    username = session.get('username')
    role = session.get('role')
    
    if username and role:
        return jsonify({
            'authenticated': True,
            'username': username,
            'role': role
        })
    
    return jsonify({'authenticated': False}), 401

# Add a new endpoint to get initial auth state
@app.route('/api/initial-auth', methods=['GET'])
def initial_auth():
    """Lightweight auth check that doesn't redirect"""
    username = session.get('username')
    role = session.get('role')
    
    return jsonify({
        'authenticated': bool(username and role),
        'username': username,
        'role': role
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file:
            filename = get_secure_filename(file)
            if not filename:
                return jsonify({'error': 'Invalid filename'}), 400
            
            if not allowed_file(filename):
                return jsonify({'error': 'File type not allowed'}), 400
            
            try:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Save the file
                file.save(filepath)
                
                # Process the image
                processed_image = preprocess_image(filepath)
                if processed_image is None:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return jsonify({'error': 'Error processing image'}), 500
                
                # Make prediction
                if MODEL is None:
                    return jsonify({'error': 'Model not loaded'}), 500
                
                prediction = MODEL.predict(processed_image, verbose=0)
                probability = float(prediction[0][0])
                probability = max(0.0, min(1.0, probability))  # Clip to [0,1]
                
                # Generate results
                risk_level = get_risk_level(probability)
                medical_advice = get_medical_advice(risk_level)
                
                # Store prediction
                prediction_id = len(predictions)
                prediction_data = {
                    'id': prediction_id,
                    'username': session['username'],
                    'filename': filename,
                    'riskLevel': risk_level,
                    'confidenceScore': f"{probability * 100:.1f}%",
                    'keyFindings': medical_advice,
                    'timestamp': datetime.now().isoformat(),
                    'doctor_notes': ''
                }
                predictions[prediction_id] = prediction_data
                
                # Clean up
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                return jsonify(prediction_data), 200
                
            except Exception as e:
                print(f"Error during prediction: {e}")
                # Clean up on error
                if os.path.exists(filepath):
                    os.remove(filepath)
                return jsonify({'error': str(e)}), 500
                
    except Exception as e:
        print(f"Error in predict route: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        user = USERS.get(session['username'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if user['role'] == 'doctor':
            # Doctors can see all predictions
            return jsonify(list(predictions.values())), 200
        else:
            # Patients can only see their own predictions
            user_predictions = [p for p in predictions.values() 
                              if p['username'] == session['username']]
            return jsonify(user_predictions), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predictions/<int:prediction_id>/notes', methods=['POST'])
def add_notes(prediction_id):
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        user = USERS.get(session['username'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if user['role'] != 'doctor':
            return jsonify({'error': 'Only doctors can add notes'}), 403
        
        if prediction_id not in predictions:
            return jsonify({'error': 'Prediction not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        notes = data.get('notes')
        if notes is None:
            return jsonify({'error': 'Notes field is required'}), 400
        
        predictions[prediction_id]['doctor_notes'] = notes
        return jsonify({'message': 'Notes updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/patient-dashboard', methods=['GET'])
def get_patient_dashboard():
    if 'username' not in session or session.get('role') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        username = session.get('username')
        # Here you would normally fetch data from a database
        # For now, returning mock data
        return jsonify({
            'latestAssessment': {
                'date': '2024-03-20',
                'result': 'Low Risk'
            },
            'totalAssessments': 3,
            'nextAppointment': '2024-03-25'
        })
    except Exception as e:
        print(f"Error in get_patient_dashboard: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/patient-reports', methods=['GET'])
def get_patient_reports():
    if 'username' not in session or session.get('role') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        username = session.get('username')
        # Here you would normally fetch data from a database
        # For now, returning mock data
        return jsonify({
            'reports': [
                {
                    'id': '1',
                    'date': '2024-03-20',
                    'doctor': 'Dr. Smith',
                    'result': 'Low Risk',
                    'notes': 'Regular follow-up recommended'
                }
            ]
        })
    except Exception as e:
        print(f"Error in get_patient_reports: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/patient-profile', methods=['GET'])
def get_patient_profile():
    if 'username' not in session or session.get('role') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        username = session.get('username')
        # Here you would normally fetch data from a database
        # For now, returning mock data
        return jsonify({
            'name': 'John Doe',
            'id': 'PAT001',
            'age': '45',
            'gender': 'Male',
            'contact': '+1234567890',
            'email': 'john@example.com'
        })
    except Exception as e:
        print(f"Error in get_patient_profile: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/save-notes', methods=['POST'])
def save_notes():
    if 'username' not in session or session.get('role') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400

        patient_id = data.get('patientId', '')
        notes = data.get('notes', '')

        if not patient_id or not notes:
            return jsonify({'error': 'Patient ID and notes are required'}), 400

        # Here you would normally save the notes to a database
        # For now, just returning success
        return jsonify({'message': 'Notes saved successfully'}), 200

    except Exception as e:
        print(f"Error in save_notes: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/patients', methods=['GET'])
def get_patients():
    """Get list of patients for doctor's view"""
    if 'username' not in session or session.get('role') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get all users with role 'patient'
        patients = [user for user in USERS.values() if user['role'] == 'patient']
        return jsonify(patients), 200
    except Exception as e:
        print(f"Error getting patients: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/store-prediction', methods=['POST'])
def store_prediction():
    """Store a prediction in the database"""
    if 'username' not in session or session.get('role') != 'doctor':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        patient_username = data.get('patient_username')
        prediction_data = data.get('prediction_data')
        
        if not patient_username or not prediction_data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Store prediction in database
        prediction_id = len(predictions)
        prediction_data['id'] = prediction_id
        prediction_data['username'] = patient_username
        predictions[prediction_id] = prediction_data
        
        return jsonify({'message': 'Prediction stored successfully'}), 200
    except Exception as e:
        print(f"Error storing prediction: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/patient-predictions/<username>', methods=['GET'])
def get_patient_predictions(username):
    """Get predictions for a specific patient"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # If patient, can only view own predictions
        if session.get('role') == 'patient' and session.get('username') != username:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Get predictions for the patient
        patient_predictions = [p for p in predictions.values() if p['username'] == username]
        return jsonify(patient_predictions), 200
    except Exception as e:
        print(f"Error getting patient predictions: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Server starting with debug mode...")
    app.run(debug=True, host='0.0.0.0', port=5000) 