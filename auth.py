# auth.py
"""
Module for authentication and login functionality for DeepOCT application.
"""
from dash import html, dcc, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
from flask_login import login_user, logout_user, current_user, UserMixin, LoginManager
import flask
from functools import wraps
import base64
import os

# Import from models
from models import authenticate_user

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, identifiant, nom, role):
        self.id = id
        self.identifiant = identifiant
        self.nom = nom
        self.role = role

def setup_login_manager(server):
    """Setup LoginManager for the Flask server."""
    login_manager = LoginManager()
    login_manager.init_app(server)
    login_manager.login_view = '/login'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import load_users
        users = load_users()
        
        for user in users:
            if user['identifiant'] == user_id:
                return User(
                    id=user['identifiant'],
                    identifiant=user['identifiant'],
                    nom=user['nom'],
                    role=user['role']
                )
        return None
    
    return login_manager

def login_layout():
    """Create the login page layout."""
    # Encode logo image
    logo_path = os.path.join("assets", "oct_logo.png")
    encoded_logo = ""
    
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as image_file:
            encoded_logo = base64.b64encode(image_file.read()).decode()
    
    return html.Div([
        # Full height container with centered content
        html.Div([
            # Card container with max width
            html.Div([
                # Logo (if exists)
                html.Div([
                    html.Img(
                        src=f'data:image/png;base64,{encoded_logo}' if encoded_logo else None,
                        style={
                            'height': '120px',
                            'margin': '0 auto 30px auto',
                            'display': 'block',
                        } if encoded_logo else {'display': 'none'}
                    ),
                ], className="text-center"),
                
                # App title and subtitle
                html.Div([
                    html.H1("DeepOCT", className="text-primary fw-bold"),
                    html.H5("Plateforme d'analyse d'images OCT maculaire", 
                           className="text-muted mb-4"),
                ], className="text-center mb-4"),
                
                # Login card
                dbc.Card([
                    dbc.CardHeader([
                        html.H3("Connexion", className="text-center mb-0")
                    ], className="bg-primary text-white"),
                    dbc.CardBody([
                        # Username input
                        dbc.Label("Identifiant", html_for="identifiant-input", className="mb-2"),
                        dbc.InputGroup([
                            dbc.InputGroupText(html.I(className="fas fa-user")),
                            dbc.Input(
                                id="identifiant-input", 
                                placeholder="Saisissez votre identifiant", 
                                type="text",
                            )
                        ], className="mb-4"),
                        
                        # Password input
                        dbc.Label("Mot de passe", html_for="password-input", className="mb-2"),
                        dbc.InputGroup([
                            dbc.InputGroupText(html.I(className="fas fa-lock")),
                            dbc.Input(
                                id="password-input", 
                                placeholder="Saisissez votre mot de passe", 
                                type="password"
                            )
                        ], className="mb-4"),
                        
                        # Alert for login messages
                        dbc.Alert(id="login-alert", is_open=False, className="mb-4"),
                        
                        # Login button
                        dbc.Button(
                            "Se connecter", 
                            id="login-button", 
                            color="primary", 
                            className="w-100 mb-3",
                            size="lg"
                        ),
                        
                        # Help text
                        html.Div([
                            html.P([
                                "Pour obtenir des identifiants, veuillez contacter l'administrateur"
                            ], className="text-muted small text-center")
                        ], className="mt-3")
                    ], className="px-4 py-4")
                ], className="shadow-sm"),
                
                # Footer
                html.Footer([
                    html.P("© 2025 DeepOCT. Tous droits réservés.", 
                          className="text-center text-muted mt-4 small")
                ])
            ], className="login-card")
        ], className="login-container")
    ], className="login-page")

def register_auth_callbacks(app):
    """Register authentication-related callbacks."""
    
    @app.callback(
        [Output('login-alert', 'children'),
         Output('login-alert', 'is_open'),
         Output('login-alert', 'color'),
         Output('url', 'pathname')],
        [Input('login-button', 'n_clicks')],
        [State('identifiant-input', 'value'),
         State('password-input', 'value')],
        prevent_initial_call=True
    )
    def process_login(n_clicks, identifiant, password):
        if not n_clicks:
            return "", False, "danger", "/"
        
        if not identifiant or not password:
            return "Veuillez saisir un identifiant et un mot de passe.", True, "danger", "/"
        
        user = authenticate_user(identifiant, password)
        
        if user:
            user_obj = User(
                id=user['identifiant'],
                identifiant=user['identifiant'],
                nom=user['nom'],
                role=user['role']
            )
            login_user(user_obj)
            return "Connexion réussie !", True, "success", "/dashboard"
        else:
            return "Identifiant ou mot de passe incorrect.", True, "danger", "/"

    @app.callback(
        Output('url', 'pathname', allow_duplicate=True),
        [Input('logout-button', 'n_clicks')],
        prevent_initial_call=True
    )
    def process_logout(n_clicks):
        if n_clicks:
            logout_user()
            return "/"
        return "/"

def require_login(func):
    """Decorator to require login for a page."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return dcc.Location(pathname='/', id='redirect-to-login')
        return func(*args, **kwargs)
    return wrapper
