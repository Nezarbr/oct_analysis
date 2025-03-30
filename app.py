# app.py
# 
"""
Main application module for DeepOCT.
"""



import dash
from dash import html, dcc, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import flask
import os
import base64
from flask_login import current_user

# Import modules
from models import load_users, load_patients
from auth import setup_login_manager, login_layout, register_auth_callbacks, require_login
from patient_management import dashboard_layout, patient_detail_layout, register_patient_callbacks
from oct_analysis import register_oct_analysis_callbacks

# Initialize server and app
server = flask.Flask(__name__)
server.secret_key = os.environ.get('SECRET_KEY', 'octmaster-secret-key')

# Setup login manager
login_manager = setup_login_manager(server)

# Initialize Dash app
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.FONT_AWESOME,
        'https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap'
    ],
    suppress_callback_exceptions=True
)

# App layout with URL routing
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    # Hidden div for storing OCT analysis data
    html.Div(id='dummy-output', style={'display': 'none'})
])

# Ensure assets directory exists
if not os.path.exists('assets'):
    os.makedirs('assets')

# Create a simple OCT logo if not exists
if not os.path.exists(os.path.join('assets', 'oct_logo.png')):
    try:
        # Creating a blank logo placeholder
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a blank image with a blue background
        img = Image.new('RGB', (200, 200), color=(63, 120, 224))  # Using our theme blue
        draw = ImageDraw.Draw(img)
        
        # Draw a white circle
        draw.ellipse((50, 50, 150, 150), fill=(255, 255, 255))
        
        # Draw a blue inner circle (representing OCT)
        draw.ellipse((70, 70, 130, 130), fill=(63, 120, 224))
        
        # Add text if a font is available
        try:
            font = ImageFont.truetype("arial.ttf", 32)
            draw.text((40, 155), "DeepOCT", fill=(255, 255, 255), font=font)
        except:
            pass
        
        # Save the logo
        img.save(os.path.join('assets', 'oct_logo.png'))
    except Exception as e:
        print(f"Could not create logo: {e}")

# Register URL routing callback
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    # Parse patient ID from pathname
    patient_id = None
    if pathname and pathname.startswith('/patient/'):
        patient_id = pathname.replace('/patient/', '')
    
    # Check if authenticated
    if current_user.is_authenticated:
        if pathname == '/dashboard':
            return dashboard_layout()
        elif patient_id:
            return patient_detail_layout(patient_id)
        else:
            # Default to dashboard if authenticated
            return dash.dcc.Location(pathname='/dashboard', id='redirect-to-dashboard')
    else:
        # Show login page if not authenticated
        return login_layout()

# Register callbacks
register_auth_callbacks(app)
register_patient_callbacks(app)
register_oct_analysis_callbacks(app)

# Add CSS to the app
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>DeepOCT</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Roboto', sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 0;
            }
            
            /* Login page styles */
            .login-page {
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            }
            
            .login-container {
                display: flex;
                justify-content: center;
                align-items: center;
                width: 100%;
                padding: 2rem;
            }
            
            .login-card {
                max-width: 450px;
                width: 100%;
                padding: 2rem;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.05);
            }
            
            /* Improved patient card styles with Moroccan-inspired colors */
            .patient-card {
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                border-radius: 8px;
                overflow: hidden;
                border: none;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                min-width: 280px !important;
            }

            .patient-card .card-body {
                padding: 1.25rem;
            }

            .patient-card .card-title {
                color: #2A6041; /* Moroccan green for names */
                font-weight: 600;
                margin-bottom: 0.5rem;
                border-bottom: 2px solid #F0F0F0;
                padding-bottom: 0.5rem;
            }

            .patient-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 24px rgba(0,0,0,0.12);
            }

            .patient-card .btn-primary {
                background-color: #C19434; /* Moroccan gold for buttons */
                border-color: #C19434;
                transition: all 0.3s ease;
            }

            .patient-card .btn-primary:hover {
                background-color: #A67C2E;
                border-color: #A67C2E;
            }

            /* Style for "IVT reçu: Oui" to stand out */
            .patient-card .fw-bold {
                color: #C19434;
                font-weight: 600 !important;
            }
            
            /* Patient slider improvements */
            .d-flex.overflow-auto {
                padding: 0.5rem 0;
                scrollbar-width: thin;
            }

            .d-flex.overflow-auto::-webkit-scrollbar {
                height: 6px;
            }

            .d-flex.overflow-auto::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 10px;
            }

            .d-flex.overflow-auto::-webkit-scrollbar-thumb {
                background: #C19434;
                border-radius: 10px;
            }
            
            /* Upload box styles */
            .upload-box {
                border: 2px dashed #dee2e6;
                border-radius: 5px;
                padding: 2rem;
                text-align: center;
                cursor: pointer;
                background-color: #f8f9fa;
                transition: background-color 0.3s ease;
            }
            
            .upload-box:hover {
                background-color: #e9ecef;
            }
            
            /* Parameter group styles */
            .parameter-group {
                margin-bottom: 1rem;
                padding-bottom: 1rem;
                border-bottom: 1px solid #dee2e6;
            }
            
            .parameter-group:last-child {
                border-bottom: none;
            }
            
            /* Input group with icons styling */
            .input-group-text {
                background-color: #f8f9fa;
                border-right: none;
            }
            
            .form-control {
                border-left: none;
            }
            
            /* Improved button styling */
            .btn-primary {
                background-color: #3f78e0;
                border-color: #3f78e0;
            }
            
            .btn-primary:hover {
                background-color: #3568c0;
                border-color: #3568c0;
            }
            
            /* Card header styling */
            .card-header.bg-primary {
                background-color: #3f78e0 !important;
            }
            
            /* Add subtle animations */
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            .login-card {
                animation: fadeIn 0.5s ease-out;
            }
            
            /* Decorative bottom border for section headings */
            .dashboard-section h3 {
                position: relative;
                padding-bottom: 0.75rem;
                margin-bottom: 1.5rem;
            }

            .dashboard-section h3:after {
                content: '';
                position: absolute;
                bottom: 0;
                left: 0;
                width: 80px;
                height: 3px;
                background: linear-gradient(90deg, #C19434 0%, #2A6041 100%);
                border-radius: 3px;
            }
            
            /* Success message animations */
            .alert-success {
                animation: slideDown 0.5s ease-out;
            }
            
            @keyframes slideDown {
                from { transform: translateY(-20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            
            /* Navbar customization */
            .navbar-brand {
                font-weight: 500;
                letter-spacing: 0.5px;
            }
            
            /* Form improvements */
            .form-control:focus, .form-select:focus {
                border-color: #C19434;
                box-shadow: 0 0 0 0.25rem rgba(193, 148, 52, 0.25);
            }
            
            /* Style patient detail pages */
            .card-header h4 {
                color: #2A6041;
                font-weight: 500;
            }
            
            /* Improve save button */
            .btn-success {
                background-color: #2A6041;
                border-color: #2A6041;
            }
            
            .btn-success:hover {
                background-color: #224e35;
                border-color: #224e35;
            }
            
            /* Add new patient transition */
            #patient-slider-container {
                transition: all 0.3s ease;
            }
            
            .patient-card {
                position: relative;
                overflow: hidden;
            }
            
            .patient-card.new-patient::before {
                content: 'Nouveau';
                position: absolute;
                top: 10px;
                right: -15px;
                background: #C19434;
                color: white;
                padding: 2px 15px;
                transform: rotate(45deg);
                font-size: 10px;
                font-weight: bold;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            
            /* OCT Analysis styles */
            .radio-group {
                margin-bottom: 1rem;
            }
            
            .radio-group .form-check {
                padding-left: 1.8rem;
            }
            
            .radio-group .form-check-input:checked {
                background-color: #2A6041;
                border-color: #2A6041;
            }
            
            /* Styles for OCT analysis results */
            .parameter-group h5 {
                color: #2A6041;
                font-weight: 500;
                margin-bottom: 0.75rem;
                border-bottom: 1px solid #f0f0f0;
                padding-bottom: 0.5rem;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Run the server
if __name__ == '__main__':
    # Pre-load data
    load_users()
    load_patients()
    
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 8006))
    
    # Run the server
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )
