# patient_management.py

"""
Module for patient management functionality for DeepOCT application.
"""
from dash import html, dcc, Input, Output, State, callback, no_update, ALL, MATCH, ctx
import dash_bootstrap_components as dbc
from flask_login import current_user
import uuid
from datetime import datetime

# Import from models
from models import get_patients_for_doctor, add_patient, get_patient_by_id
from oct_analysis import create_eye_section

def navbar():
    """Create the navigation bar."""
    return dbc.Navbar(
        dbc.Container([
            # Logo and brand
            html.A(
                dbc.Row([
                    dbc.Col(html.Img(src="/assets/oct_logo.png", height="40px"), width="auto"),
                    dbc.Col(dbc.NavbarBrand("DeepOCT", className="ms-2"), width="auto"),
                ], align="center", className="g-0"),
                href="/dashboard",
                style={"textDecoration": "none"},
            ),
            
            # Navbar toggle, links and dropdown
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink(f"Dr. {current_user.identifiant.capitalize()}", href="#")),
                    dbc.DropdownMenu(
                        [
                            dbc.DropdownMenuItem("Paramètres", href="#"),
                            dbc.DropdownMenuItem("Aide", href="#"),
                            dbc.DropdownMenuItem(divider=True),
                            dbc.DropdownMenuItem("Déconnexion", id="logout-button", href="#"),
                        ],
                        nav=True,
                        label="Menu",
                    ),
                ], className="ms-auto", navbar=True),
                id="navbar-collapse",
                navbar=True,
            ),
        ], fluid=True),
        color="primary",
        dark=True,
        className="mb-4",
    )

def patients_slider():
    """Create the patients slider with improved styling."""
    patients = get_patients_for_doctor(current_user.identifiant)
    
    if not patients:
        return html.Div([
            html.P("Aucun patient trouvé.", className="text-muted"),
        ], className="text-center p-5 bg-light rounded")
    
    patient_cards = []
    for patient in patients:
        patient_id = f"{patient['nom']}_{patient['prenom']}"
        
        # Customize icon based on IVT status
        ivt_icon = html.I(className="fas fa-syringe me-2") if patient['ivt_recu'] == "Oui" else ""
        
        patient_cards.append(
            dbc.Card([
                dbc.CardBody([
                    html.H5([
                        f"{patient['nom']} {patient['prenom']}"
                    ], className="card-title"),
                    html.P(f"{patient['age']} ans • {patient['sexe']}", className="card-text text-muted small"),
                    html.P([
                        "IVT reçu: ",
                        html.Span([ivt_icon, patient['ivt_recu']], className="fw-bold")
                    ], className="card-text"),
                    dbc.Button([
                        html.I(className="fas fa-folder-open me-2"),
                        "Voir dossier"
                    ], color="primary", id={
                        "type": "view-patient-btn",
                        "index": patient_id
                    }, className="mt-2"),
                ])
            ], className="patient-card me-3")
        )
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div(patient_cards, className="d-flex overflow-auto pb-3")
            ])
        ])
    ])

def new_patient_form():
    """Create the new patient form."""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Nom"),
                    dbc.Input(id="new-patient-nom", type="text", placeholder="Nom"),
                ], width=6),
                dbc.Col([
                    dbc.Label("Prénom"),
                    dbc.Input(id="new-patient-prenom", type="text", placeholder="Prénom"),
                ], width=6),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Sexe"),
                    dbc.RadioItems(
                        options=[
                            {"label": "Homme", "value": "Homme"},
                            {"label": "Femme", "value": "Femme"},
                        ],
                        value="Homme",
                        id="new-patient-sexe",
                        inline=True,
                    ),
                ], width=6),
                dbc.Col([
                    dbc.Label("Âge"),
                    dbc.Input(id="new-patient-age", type="number", placeholder="Âge"),
                ], width=6),
            ], className="mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("IVT reçu"),
                    dbc.RadioItems(
                        options=[
                            {"label": "Oui", "value": "Oui"},
                            {"label": "Non", "value": "Non"},
                        ],
                        value="Non",
                        id="new-patient-ivt",
                        inline=True,
                    ),
                ], width=12),
            ], className="mb-3"),
            
            html.Div([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Type d'IVT"),
                        dbc.RadioItems(
                            options=[
                                {"label": "Anti-VEGF", "value": "anti_vegf"},
                                {"label": "Corticoïde", "value": "corticoid"},
                            ],
                            value="anti_vegf",
                            id="new-patient-ivt-type",
                            inline=True,
                        ),
                    ], width=12),
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Nombre d'injections"),
                        dbc.Input(id="new-patient-nb-injections", type="number", placeholder="Nombre d'injections"),
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Molécule"),
                        dbc.Input(id="new-patient-molecule", type="text", placeholder="Molécule"),
                    ], width=6),
                ], className="mb-3"),
            ], id="ivt-details", style={"display": "none"}),
            
            dbc.Alert(id="new-patient-alert", is_open=False, duration=4000, className="mt-3"),
            dbc.Button("Enregistrer", id="save-patient-btn", color="success", className="mt-3"),
        ])
    ])

def dashboard_layout():
    """Create the dashboard layout."""
    patients_list = patients_slider()  # Generate patients slider directly
    
    return html.Div([
        navbar(),
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H2(f"Bonjour, {current_user.nom}", className="mt-4 mb-4 text-primary"),
                    
                    # Patients Slider - Directly rendering instead of using callback
                    html.Div([
                        html.H3("Patients Suivis", className="mb-3"),
                        html.Div(patients_list, id='patient-slider-container'),
                    ], className="mb-5 dashboard-section"),
                    
                    # New Patient Form
                    html.Div([
                        html.H3("Ajouter un Nouveau Patient", className="mb-3"),
                        new_patient_form(),
                    ], className="mb-4 dashboard-section"),
                    
                ], width=12)
            ])
        ], fluid=True)
    ])

# Update to patient_detail_layout in patient_management.py

# Update the import statement
from oct_analysis import create_eye_section, create_report_section

def patient_detail_layout(patient_id):
    """Create the patient detail layout with OCT analysis capabilities."""
    from models import get_patient_by_id
    
    _, patient = get_patient_by_id(patient_id)
    if not patient:
        return html.Div([
            navbar(),
            dbc.Container([
                dbc.Alert("Patient non trouvé", color="danger"),
                dbc.Button("Retour", id="back-to-dashboard", color="primary"),
            ])
        ])
    
    # Format today's date for last visit
    today = datetime.now().strftime("%d/%m/%Y")
    
    return html.Div([
        navbar(),
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-arrow-left me-2"),
                        "Retour"
                    ], id="back-to-dashboard", color="secondary", className="mb-4"),
                    
                    html.H2([
                        f"Dossier de {patient['nom']} {patient['prenom']}",
                        html.Span(f" ({patient['age']} ans • {patient['sexe']})", className="text-muted fs-5 ms-2")
                    ], className="mb-4"),
                    
                    # Patient summary card
                    dbc.Card([
                        dbc.CardHeader(html.H4("Informations du patient")),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.P([
                                        html.Strong("IVT reçu: "),
                                        patient['ivt_recu']
                                    ]),
                                    html.Div([
                                        html.P([
                                            html.Strong("Type d'IVT: "),
                                            "Anti-VEGF" if patient['type_ivt'] == "anti_vegf" else "Corticoïde" if patient['type_ivt'] else "N/A"
                                        ]),
                                        html.P([
                                            html.Strong("Nombre d'injections: "),
                                            str(patient['nb_injections'])
                                        ]),
                                        html.P([
                                            html.Strong("Molécule: "),
                                            patient['molecule']
                                        ]),
                                    ], style={"display": "block" if patient['ivt_recu'] == "Oui" else "none"})
                                ], width=6),
                                dbc.Col([
                                    html.P([
                                        html.Strong("Dernière visite: "),
                                        today
                                    ]),
                                    html.P([
                                        html.Strong("Suivi par: "),
                                        f"Dr. {patient['doctor'].capitalize()}"
                                    ]),
                                ], width=6),
                            ])
                        ])
                    ], className="mb-4"),
                    
                    # OCT Analysis Section
                    dbc.Card([
                        dbc.CardHeader(html.H4("Analyse OCT")),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.H5("Télécharger une image OCT"),
                                    dcc.Upload(
                                        id='upload-image',
                                        children=html.Div([
                                            html.I(className="fas fa-upload me-2"),
                                            'Glisser-déposer ou ',
                                            html.A('Sélectionner une image OCT', className="text-primary")
                                        ]),
                                        className="upload-box mb-3"
                                    ),
                                    html.Div(id='output-image-upload', className="mt-3"),
                                    dbc.Button(
                                        "Analyser avec DeepOCT",
                                        id="analyze-button",
                                        color="success",
                                        size="lg",
                                        className="w-100 mb-3",
                                        disabled=False
                                    ),
                                ], width=12),
                            ]),
                            
                            # OCT Analysis Results Section
                            html.Div([
                                dbc.Row([
                                    dbc.Col([
                                        html.H5("Résultats d'analyse", className="mt-4 mb-3"),
                                        dbc.Spinner(
                                            html.Div(id="analysis-loading"),
                                            color="primary",
                                            type="grow",
                                            fullscreen=False,
                                        ),
                                    ], width=12)
                                ]),
                                
                                # Biomarkers Section
                                html.Div([
                                    dbc.Row([
                                        dbc.Col([
                                            html.H4("Biomarqueurs", className="text-primary mb-3 mt-4"),
                                        ], width=12),
                                        
                                        # Left Eye
                                        dbc.Col(create_eye_section("Left"), md=6, className="mb-4"),
                                        
                                        # Right Eye
                                        dbc.Col(create_eye_section("Right"), md=6, className="mb-4"),
                                        
                                        # Report Section
                                        dbc.Col([
                                            create_report_section()
                                        ], width=12),
                                        
                                        # Save Analysis Button
                                        dbc.Col([
                                            dbc.Button(
                                                "Enregistrer l'analyse",
                                                id="save-analysis-btn", 
                                                color="primary",
                                                className="w-100 mt-3 mb-3",
                                            ),
                                            dbc.Alert(id="analysis-alert", is_open=False, duration=4000, className="mt-3"),
                                        ], width=12)
                                    ]),
                                ], id="biomarkers-section", style={"display": "none"}),
                            ], id="oct-results")
                        ])
                    ])
                ], width=12)
            ])
        ], fluid=True)
    ])

def register_patient_callbacks(app):
    """Register patient management related callbacks."""
    
    # Toggle IVT details
    @app.callback(
        Output("ivt-details", "style"),
        Input("new-patient-ivt", "value")
    )
    def toggle_ivt_details(ivt_value):
        if ivt_value == "Oui":
            return {"display": "block"}
        return {"display": "none"}
    
    # Save new patient and update the patient list immediately
    @app.callback(
        [Output("new-patient-alert", "children"),
         Output("new-patient-alert", "is_open"),
         Output("new-patient-alert", "color"),
         Output("new-patient-nom", "value"),
         Output("new-patient-prenom", "value"),
         Output("new-patient-age", "value"),
         Output("new-patient-sexe", "value"),
         Output("new-patient-ivt", "value"),
         Output("new-patient-ivt-type", "value"),
         Output("new-patient-nb-injections", "value"),
         Output("new-patient-molecule", "value"),
         Output("patient-slider-container", "children")],
        [Input("save-patient-btn", "n_clicks")],
        [State("new-patient-nom", "value"),
         State("new-patient-prenom", "value"),
         State("new-patient-age", "value"),
         State("new-patient-sexe", "value"),
         State("new-patient-ivt", "value"),
         State("new-patient-ivt-type", "value"),
         State("new-patient-nb-injections", "value"),
         State("new-patient-molecule", "value")],
        prevent_initial_call=True
    )
    def save_new_patient(n_clicks, nom, prenom, age, sexe, ivt_recu, type_ivt, nb_injections, molecule):
        if not n_clicks:
            return "", False, "danger", no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        # Validate input
        if not nom or not prenom or not age:
            return "Veuillez remplir tous les champs obligatoires (nom, prénom, âge).", True, "danger", no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        if ivt_recu == "Oui" and (not nb_injections or not molecule):
            return "Veuillez indiquer le nombre d'injections et la molécule.", True, "danger", no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        # Create patient data
        patient_data = {
            "nom": nom,
            "prenom": prenom,
            "sexe": sexe,
            "age": int(age),
            "ivt_recu": ivt_recu,
            "type_ivt": type_ivt if ivt_recu == "Oui" else "",
            "nb_injections": int(nb_injections) if ivt_recu == "Oui" and nb_injections else 0,
            "molecule": molecule if ivt_recu == "Oui" else "",
            "doctor": current_user.identifiant
        }
        
        # Add patient to database
        success = add_patient(patient_data)
        
        if success:
            # Create success message and clear form
            message = f"Patient {nom} {prenom} ajouté avec succès !"
            # Update the patient slider to show the new patient
            updated_slider = patients_slider()
            return message, True, "success", "", "", None, "Homme", "Non", "anti_vegf", None, "", updated_slider
        else:
            return "Erreur lors de l'ajout du patient.", True, "danger", no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    # View patient details
    @app.callback(
        Output("url", "pathname", allow_duplicate=True),
        Input({"type": "view-patient-btn", "index": ALL}, "n_clicks"),
        State({"type": "view-patient-btn", "index": ALL}, "id"),
        prevent_initial_call=True
    )
    def view_patient_details(n_clicks_list, id_list):
        # Using imported ctx from dash
        if not ctx.triggered:
            return no_update
        
        button_id = ctx.triggered_id
        if isinstance(button_id, dict) and button_id.get("type") == "view-patient-btn":
            patient_id = button_id["index"]
            return f"/patient/{patient_id}"
        
        return no_update
    
    # Back to dashboard
    @app.callback(
        Output("url", "pathname", allow_duplicate=True),
        Input("back-to-dashboard", "n_clicks"),
        prevent_initial_call=True
    )
    def go_back_to_dashboard(n_clicks):
        if n_clicks:
            return "/dashboard"
        return no_update

    # Handle navbar toggle
    @app.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")],
    )
    def toggle_navbar_collapse(n, is_open):
        if n:
            return not is_open
        return is_open
