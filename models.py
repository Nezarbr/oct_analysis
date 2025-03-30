#models.py
"""
Module containing data models and utility functions for OCT Master application.
"""
import os
import json
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

# Default users that will always be available
DEFAULT_USERS = [
    {
        "identifiant": "Elamri_Ayoub",
        "nom": "Dr Elamri Ayoub",
        "password_hash": generate_password_hash("password123", method='pbkdf2:sha256'),
        "role": "doctor"
    },
    {
        "identifiant": "Nezar",
        "nom": "Eng Nezar",
        "password_hash": generate_password_hash("password123", method='pbkdf2:sha256'),
        "role": "doctor"
    },
    {
        "identifiant": "admin",
        "nom": "Administrateur",
        "password_hash": generate_password_hash("admin123", method='pbkdf2:sha256'),
        "role": "admin"
    }
]

# Default patients that will always be available
DEFAULT_PATIENTS = [
    {
        "nom": "El Amrani",
        "prenom": "Ahmed",
        "sexe": "Homme",
        "age": 65,
        "ivt_recu": "Oui",
        "type_ivt": "anti_vegf",
        "nb_injections": 3,
        "molecule": "Aflibercept",
        "doctor": "Elamri_Ayoub"
    },
    {
        "nom": "Benkirane",
        "prenom": "Fatima",
        "sexe": "Femme",
        "age": 72,
        "ivt_recu": "Oui",
        "type_ivt": "corticoid",
        "nb_injections": 2,
        "molecule": "Dexaméthasone",
        "doctor": "Elamri_Ayoub"
    },
    {
        "nom": "Tazi",
        "prenom": "Mohammed",
        "sexe": "Homme",
        "age": 58,
        "ivt_recu": "Non",
        "type_ivt": "",
        "nb_injections": 0,
        "molecule": "",
        "doctor": "Elamri_Ayoub"
    },
    {
        "nom": "Alaoui",
        "prenom": "Laila",
        "sexe": "Femme",
        "age": 63,
        "ivt_recu": "Oui",
        "type_ivt": "anti_vegf",
        "nb_injections": 4,
        "molecule": "Ranibizumab",
        "doctor": "Elamri_Ayoub"
    },
    {
        "nom": "Idrissi",
        "prenom": "Younes",
        "sexe": "Homme",
        "age": 70,
        "ivt_recu": "Oui",
        "type_ivt": "anti_vegf",
        "nb_injections": 5,
        "molecule": "Bevacizumab",
        "doctor": "Elamri_Ayoub"
    }
]

# In-memory storage for users, patients and OCT analyses
USERS = DEFAULT_USERS.copy()
PATIENTS = DEFAULT_PATIENTS.copy()
OCT_ANALYSES = {}  # Format: {patient_id: [analysis1, analysis2, ...]}

def load_users():
    """Return the users list."""
    return USERS

def save_users(users):
    """Update the users list."""
    global USERS
    USERS = users

def load_patients():
    """Return the patients list."""
    return PATIENTS

def save_patients(patients):
    """Update the patients list."""
    global PATIENTS
    PATIENTS = patients

def authenticate_user(identifiant, password):
    """Authenticate a user by checking identifiant and password."""
    users = load_users()
    
    for user in users:
        if user['identifiant'].lower() == identifiant.lower():
            if check_password_hash(user['password_hash'], password):
                return user
    
    return None

def get_patients_for_doctor(doctor_id):
    """Get all patients for a specific doctor."""
    patients = load_patients()
    doctor_patients = [p for p in patients if p.get('doctor') == doctor_id]
    # Sort patients with newest first (assuming newest are at the end of the list)
    doctor_patients.reverse()
    return doctor_patients

def add_patient(patient_data):
    """Add a new patient to the database."""
    patients = load_patients()
    # Add new patient
    patients.append(patient_data)
    save_patients(patients)
    return True

def get_patient_by_id(patient_id):
    """Get a patient by their ID (in this case, a combination of nom and prenom)."""
    patients = load_patients()
    for i, patient in enumerate(patients):
        if f"{patient['nom']}_{patient['prenom']}" == patient_id:
            return i, patient
    return None, None

def update_patient(patient_id, updated_data):
    """Update a patient's information."""
    patients = load_patients()
    index, _ = get_patient_by_id(patient_id)
    
    if index is not None:
        patients[index] = updated_data
        save_patients(patients)
        return True
    
    return False

# OCT Analysis storage functions
def save_oct_analysis(patient_id, analysis_data):
    """
    Save an OCT analysis for a patient.
    
    Args:
        patient_id (str): The patient ID
        analysis_data (dict): The analysis data to save
    
    Returns:
        bool: True if successfully saved, False otherwise
    """
    global OCT_ANALYSES
    
    # Create a timestamp for the analysis
    timestamp = datetime.now().isoformat()
    
    # Initialize patient's analyses if needed
    if patient_id not in OCT_ANALYSES:
        OCT_ANALYSES[patient_id] = []
    
    # Add new analysis with timestamp
    OCT_ANALYSES[patient_id].append({
        "timestamp": timestamp,
        "data": analysis_data
    })
    
    return True

def get_patient_analyses(patient_id):
    """
    Get all OCT analyses for a patient.
    
    Args:
        patient_id (str): The patient ID
    
    Returns:
        list: List of analyses for the patient, or empty list if none
    """
    return OCT_ANALYSES.get(patient_id, [])

def get_latest_analysis(patient_id):
    """
    Get the most recent OCT analysis for a patient.
    
    Args:
        patient_id (str): The patient ID
    
    Returns:
        dict: The most recent analysis or None if no analyses exist
    """
    analyses = get_patient_analyses(patient_id)
    
    if not analyses:
        return None
    
    # Sort by timestamp and return the most recent
    sorted_analyses = sorted(analyses, key=lambda x: x["timestamp"], reverse=True)
    return sorted_analyses[0]
