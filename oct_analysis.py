# oct_analysis.py
"""
Module for OCT image analysis functionality in OCT Master application.
"""
from dash import html, dcc, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import base64
import json
import os
import copy
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client if API key exists
try:
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)
        print("OpenAI client initialized successfully.")
    else:
        print("No OpenAI API key found. OCT analysis will be simulated.")
        client = None
except ImportError:
    print("OpenAI package not installed. OCT analysis will be simulated.")
    OpenAI = None
    client = None
    
def create_eye_section(side):
    """Create the eye section for OCT analysis results."""
    side_text = "Œil Gauche" if side.lower() == "left" else "Œil Droit"
    return dbc.Card([
        dbc.CardHeader(html.H3(side_text, className="text-primary")),
        dbc.CardBody([
            html.Div([
                html.H5("DRIL", className="text-secondary"),
                dcc.RadioItems(
                    options=['Présente', 'Absente'],
                    id=f'dril-{side.lower()}',
                    inline=True,
                    className="radio-group"
                )
            ], className="parameter-group"),

            html.Div([
                html.H5("Œdème maculaire cystoïde", className="text-secondary"),
                dcc.RadioItems(
                    options=['Présent', 'Absent'],
                    id=f'oedeme-{side.lower()}',
                    inline=True,
                    className="radio-group"
                ),
                html.Div([
                    dbc.Label("Nb de logette"),
                    dbc.Input(
                        type="text",
                        id=f'nb-logette-input-{side.lower()}',
                        placeholder="Entrer le nombre de logettes",
                        className="mb-2"
                    ),
                    dbc.Label("Taille"),
                    dbc.Input(
                        type="text",
                        id=f'taille-logette-input-{side.lower()}',
                        placeholder="Entrer la taille",
                        className="mb-2"
                    ),
                    dbc.Label("Localisation"),
                    dbc.Input(
                        type="text",
                        id=f'localisation-input-{side.lower()}',
                        placeholder="Entrer la localisation",
                        className="mb-2"
                    ),
                ], id=f'oedeme-details-{side.lower()}', style={"display": "none"})
            ], className="parameter-group"),

            html.Div([
                html.H5("Processus Rétiniens de Pontage", className="text-secondary"),
                dcc.RadioItems(
                    options=['Présent', 'Absent'],
                    id=f'briding-{side.lower()}',
                    inline=True,
                    className="radio-group"
                )
            ], className="parameter-group"),

            html.Div([
                html.H5("Intégrité de la MLE/ZE", className="text-secondary"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("MLE"),
                        dbc.Select(
                            id=f'mle-{side.lower()}',
                            options=[
                                {"label": "Continue", "value": "Continue"},
                                {"label": "Partiellement interrompue", "value": "Partiellement interrompue"},
                                {"label": "Complètement interrompue", "value": "Complètement interrompue"}
                            ]
                        )
                    ]),
                    dbc.Col([
                        dbc.Label("ZE"),
                        dbc.Select(
                            id=f'ze-{side.lower()}',
                            options=[
                                {"label": "Continue", "value": "Continue"},
                                {"label": "Partiellement interrompue", "value": "Partiellement interrompue"},
                                {"label": "Complètement interrompue", "value": "Complètement interrompue"}
                            ]
                        )
                    ])
                ])
            ], className="parameter-group"),

            html.Div([
                html.H5("Points Hyperréflectifs", className="text-secondary"),
                dcc.RadioItems(
                    options=['Présents', 'Absents'],
                    id=f'points-{side.lower()}',
                    inline=True,
                    className="radio-group"
                )
            ], className="parameter-group"),

            html.Div([
                html.H5("Décollement Séreux Rétinien", className="text-secondary"),
                dcc.RadioItems(
                    options=['Présent', 'Absent'],
                    id=f'decollement-{side.lower()}',
                    inline=True,
                    className="radio-group"
                )
            ], className="parameter-group"),

            html.Div([
                html.H5("Épaisseur Rétinienne (EDTRS)", className="text-secondary"),
                dbc.Input(
                    type="text",
                    id=f'edtrs-input-{side.lower()}',
                    placeholder="Entrer la valeur EDTRS",
                    className="mt-2"
                )
            ], className="parameter-group")
        ])
    ], className="h-100")

def encode_image_contents(contents):
    """Encode image contents to base64."""
    content_type, content_string = contents.split(',')
    return content_string

def simulate_oct_analysis():
    """Simulate an OCT analysis response for development purposes."""
    # Simulated OCT analysis for development/testing
    import random
    
    statuses = ["Présente", "Absente"]
    oedeme_statuses = ["Présent", "Absent"]
    tailles = ["petite", "grande", "volumineuse"]
    localisations = ["fovéolaire", "parafovéolaire"]
    membrane_statuses = ["Continue", "Partiellement interrompue", "Complètement interrompue"]
    points_statuses = ["Présents", "Absents"]
    points_localisations = ["intrarétinien", "choroïdien"]
    
    # Create a random analysis for demonstration
    analysis = {
        "left_eye": {
            "dril": {
                "status": random.choice(statuses),
                "extent": "Légère désorganisation des couches rétiniennes internes" if random.choice([True, False]) else ""
            },
            "oedeme": {
                "status": random.choice(oedeme_statuses),
                "nb_logette": str(random.randint(1, 5)) if random.choice([True, False]) else "",
                "taille": random.choice(tailles) if random.choice([True, False]) else "",
                "localisation": random.choice(localisations) if random.choice([True, False]) else ""
            },
            "mle": random.choice(membrane_statuses),
            "ze": random.choice(membrane_statuses),
            "points_hyperreflectifs": {
                "status": random.choice(points_statuses),
                "nombre": str(random.randint(2, 10)) if random.choice([True, False]) else "",
                "localisation": random.choice(points_localisations) if random.choice([True, False]) else ""
            },
            "epaisseur_retinienne": {
                "central": str(random.randint(200, 350)),
                "superieur": str(random.randint(200, 350)),
                "inferieur": str(random.randint(200, 350)),
                "nasal": str(random.randint(200, 350)),
                "temporal": str(random.randint(200, 350))
            }
        },
        "right_eye": {
            "dril": {
                "status": random.choice(statuses),
                "extent": "Désorganisation modérée des couches rétiniennes internes" if random.choice([True, False]) else ""
            },
            "oedeme": {
                "status": random.choice(oedeme_statuses),
                "nb_logette": str(random.randint(1, 5)) if random.choice([True, False]) else "",
                "taille": random.choice(tailles) if random.choice([True, False]) else "",
                "localisation": random.choice(localisations) if random.choice([True, False]) else ""
            },
            "mle": random.choice(membrane_statuses),
            "ze": random.choice(membrane_statuses),
            "points_hyperreflectifs": {
                "status": random.choice(points_statuses),
                "nombre": str(random.randint(2, 10)) if random.choice([True, False]) else "",
                "localisation": random.choice(points_localisations) if random.choice([True, False]) else ""
            },
            "epaisseur_retinienne": {
                "central": str(random.randint(200, 350)),
                "superieur": str(random.randint(200, 350)),
                "inferieur": str(random.randint(200, 350)),
                "nasal": str(random.randint(200, 350)),
                "temporal": str(random.randint(200, 350))
            }
        }
    }
    
    return analysis

def analyze_with_gpt(image_base64):
    """Send the image to GPT-4 Vision and return the response."""
    if client is None:
        print("No OpenAI client available. Using simulation instead.")
        return simulate_oct_analysis()
    
    prompt = """Je suis ophtalmologue et j'ai besoin que tu analyses cette image OCT maculaire. Fournis-moi une réponse JSON structurée uniquement, sans texte explicatif avant ou après.

Pour chaque œil (OD et OG), analyse les biomarqueurs suivants et retourne le résultat au format JSON :

1. DRIL (Désorganisation des couches rétiniennes internes)
   - Présence/absence
   - Si présent, décrire l'étendue

2. Œdème maculaire Cystoïde
   - Nombre de logettes
   - Taille de la plus grande logette:
     * Petite: <100μm
     * Grande: 100-200μm
     * Volumineuse: >200μm
   - Localisation: fovéolaire ou parafovéolaire

3. Intégrité des membranes
   Membrane limitante externe (MLE):
   - Continue
   - Partiellement interrompue
   - Complètement interrompue

   Zone ellipsoïde (ZE):
   - Continue
   - Partiellement interrompue
   - Complètement interrompue

4. Points hyperréflectifs
   - Présence/absence
   - Si présent:
     * Nombre approximatif
     * Localisation (intrarétinien/choroïdien)

5. Épaisseur rétinienne
   - Analyser la carte ETDRS
   - Donner les chiffres importants dans chaque secteur EXACTEMENT dans ce format: 
     "epaisseur_retinienne": {
         "central": "valeur en μm",
         "superieur": "valeur en μm",
         "inferieur": "valeur en μm",
         "nasal": "valeur en μm",
         "temporal": "valeur en μm"
     }

POINTS IMPORTANTS:
- Ne mentionner que ce qui est clairement visible
- Éviter les surinterprétations
- Pour les kystes, ne les mentionner que s'ils sont clairement identifiables
- Rester objectif et précis dans les mesures
- Tu n'as pas besoin d'évaluer le Décollement Séreux Rétinien ni les Processus Rétiniens de Pontage, ces évaluations seront faites par l'ophtalmologue

RETOURNER UNIQUEMENT UN OBJET JSON VALIDE AVEC LA STRUCTURE SUIVANTE:

{
    "left_eye": {
        "dril": {
            "status": "Présente/Absente",
            "extent": "description si présent"
        },
        "oedeme": {
            "status": "Présent/Absent",
            "nb_logette": "nombre",
            "taille": "petite/grande/volumineuse",
            "localisation": "fovéolaire/parafovéolaire"
        },
        "mle": "Continue/Partiellement interrompue/Complètement interrompue",
        "ze": "Continue/Partiellement interrompue/Complètement interrompue",
        "points_hyperreflectifs": {
            "status": "Présents/Absents",
            "nombre": "nombre approximatif",
            "localisation": "intrarétinien/choroïdien"
        },
        "epaisseur_retinienne": {
            "central": "valeur",
            "superieur": "valeur",
            "inferieur": "valeur",
            "nasal": "valeur",
            "temporal": "valeur"
        }
    },
    "right_eye": {
        "dril": {
            "status": "Présente/Absente",
            "extent": "description si présent"
        },
        "oedeme": {
            "status": "Présent/Absent",
            "nb_logette": "nombre",
            "taille": "petite/grande/volumineuse",
            "localisation": "fovéolaire/parafovéolaire"
        },
        "mle": "Continue/Partiellement interrompue/Complètement interrompue",
        "ze": "Continue/Partiellement interrompue/Complètement interrompue",
        "points_hyperreflectifs": {
            "status": "Présents/Absents",
            "nombre": "nombre approximatif",
            "localisation": "intrarétinien/choroïdien"
        },
        "epaisseur_retinienne": {
            "central": "valeur",
            "superieur": "valeur",
            "inferieur": "valeur",
            "nasal": "valeur",
            "temporal": "valeur"
        }
    }
}"""

    try:
        print("\n=== Sending request to GPT-4 ===")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un ophtalmologue expert en analyse d'OCT maculaire. Tu retournes uniquement des réponses au format JSON valide, sans texte explicatif."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500,
            temperature=0.1
        )
        
        print("\n=== Raw GPT Response ===")
        
        response_text = response.choices[0].message.content.strip()
        print(response_text)
        
        # Extract JSON from response if wrapped in code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
            print("\n=== Extracted JSON from code block ===")
            print(response_text)
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            print("\n=== Extracted content from code block ===")
            print(response_text)
            
        try:
            parsed_response = json.loads(response_text)
            print("\n=== Successfully parsed JSON ===")
            print(json.dumps(parsed_response, indent=2))
            return parsed_response
        except json.JSONDecodeError as e:
            print(f"\n=== JSON Parsing Error ===")
            print(f"Failed to parse: {response_text}")
            print(f"Error: {str(e)}")
            return {"error": str(e)}
            
    except Exception as e:
        print(f"\n=== API Error ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("Falling back to simulation.")
        return simulate_oct_analysis()

def process_gpt_response(response):
    """Process and standardize the GPT output into a format compatible with the UI."""
    print("\n=== Processing GPT Response ===")
    
    default_structure = {
        "left_eye": {
            "dril": {"status": "Absente", "extent": ""},
            "oedeme": {
                "status": "Absent",
                "nb_logette": "",
                "taille": "",
                "localisation": ""
            },
            "mle": "Continue",
            "ze": "Continue",
            "points_hyperreflectifs": {
                "status": "Absents",
                "nombre": "",
                "localisation": ""
            },
            "epaisseur_retinienne": {
                "central": "",
                "superieur": "",
                "inferieur": "",
                "nasal": "",
                "temporal": ""
            },
            "briding": "Absent",
            "decollement": "Absent"
        },
        "right_eye": {}
    }
    
    # Copy left_eye structure to right_eye
    default_structure["right_eye"] = copy.deepcopy(default_structure["left_eye"])

    if "error" in response:
        print(f"\n=== Error in response ===")
        print(f"Error: {response['error']}")
        return default_structure

    # Size standardization mapping
    taille_mapping = {
        "small": "petite",
        "medium": "grande",
        "large": "volumineuse",
        "petit": "petite",
        "grand": "grande",
        "<100": "petite",
        "100-200": "grande",
        ">200": "volumineuse"
    }

    # Process each eye
    for eye in ["left_eye", "right_eye"]:
        if eye not in response:
            response[eye] = default_structure[eye]
            continue

        eye_data = response[eye]
        
        # Standardize DRIL status
        if "dril" in eye_data:
            if isinstance(eye_data["dril"], dict):
                eye_data["dril"]["status"] = eye_data["dril"]["status"].capitalize()
                if eye_data["dril"]["status"] not in ["Présente", "Absente"]:
                    eye_data["dril"]["status"] = "Présente" if "present" in eye_data["dril"]["status"].lower() else "Absente"

        # Standardize Oedeme status and details
        if "oedeme" in eye_data:
            if isinstance(eye_data["oedeme"], dict):
                eye_data["oedeme"]["status"] = eye_data["oedeme"]["status"].capitalize()
                if eye_data["oedeme"]["status"] not in ["Présent", "Absent"]:
                    eye_data["oedeme"]["status"] = "Présent" if "present" in eye_data["oedeme"]["status"].lower() else "Absent"
                
                # Standardize taille
                if "taille" in eye_data["oedeme"]:
                    taille = eye_data["oedeme"]["taille"].lower()
                    eye_data["oedeme"]["taille"] = taille_mapping.get(taille, taille)

        # Standardize MLE/ZE values
        for field in ["mle", "ze"]:
            if field in eye_data:
                value = eye_data[field]
                if "continu" in value.lower():
                    eye_data[field] = "Continue"
                elif "partiel" in value.lower():
                    eye_data[field] = "Partiellement interrompue"
                elif "complet" in value.lower():
                    eye_data[field] = "Complètement interrompue"

        # Standardize points hyperreflectifs
        if "points_hyperreflectifs" in eye_data:
            points = eye_data["points_hyperreflectifs"]
            if isinstance(points, dict):
                points["status"] = points["status"].capitalize()
                if points["status"] not in ["Présents", "Absents"]:
                    points["status"] = "Présents" if "present" in points["status"].lower() else "Absents"

        # Format retinal thickness values
        if "epaisseur_retinienne" in eye_data:
            if isinstance(eye_data["epaisseur_retinienne"], str):
                # If it's a string, convert to structured format
                eye_data["epaisseur_retinienne"] = {
                    "central": eye_data["epaisseur_retinienne"],
                    "superieur": "",
                    "inferieur": "",
                    "nasal": "",
                    "temporal": ""
                }

        # Add missing fields with default values
        for key, default_value in default_structure[eye].items():
            if key not in eye_data:
                eye_data[key] = default_value
                print(f"Added missing key '{key}' with default value for {eye}")

    print("\n=== Processed Response ===")
    return response

def register_oct_analysis_callbacks(app):
    """Register callbacks related to OCT analysis."""
    
    # Enable Analyze button when image is uploaded
    @app.callback(
        Output("analyze-button", "disabled"),
        Input("output-image-upload", "children")
    )
    def toggle_analyze_button(children):
        if children:
            return False
        return True
    
    # Display uploaded image
    @app.callback(
        Output("output-image-upload", "children"),
        Input("upload-image", "contents"),
        State("upload-image", "filename"),
        prevent_initial_call=True
    )
    def display_uploaded_image(contents, filename):
        if contents:
            return html.Div([
                html.Img(src=contents, style={"max-width": "100%", "height": "auto"}),
                html.P(filename, className="mt-2 text-muted")
            ])
        return None
        
    # Show/hide the biomarkers section after analysis button click
    @app.callback(
        [Output('biomarkers-section', 'style'),
         Output('analysis-loading', 'children')],
        Input('analyze-button', 'n_clicks'),
        State('upload-image', 'contents'),
        prevent_initial_call=True
    )
    def toggle_biomarkers_section(n_clicks, contents):
        if not n_clicks or not contents:
            return {"display": "none"}, ""
        return {"display": "block"}, ""

    # Callback for left oedeme details
    @app.callback(
        Output('oedeme-details-left', 'style'),
        Input('oedeme-left', 'value'),
        prevent_initial_call=True
    )
    def toggle_oedeme_details_left(value):
        if value == 'Présent':
            return {'display': 'block'}
        return {'display': 'none'}
    
    # Callback for right oedeme details
    @app.callback(
        Output('oedeme-details-right', 'style'),
        Input('oedeme-right', 'value'),
        prevent_initial_call=True
    )
    def toggle_oedeme_details_right(value):
        if value == 'Présent':
            return {'display': 'block'}
        return {'display': 'none'}
        
    # Analyze the OCT image and update form values
    @app.callback(
        [Output(f'{component}-{side.lower()}', 'value') 
         for side in ['left', 'right']
         for component in ['dril', 'oedeme', 'briding', 'mle', 'ze', 'points', 'decollement']] +
        [Output(f'nb-logette-input-{side.lower()}', 'value') for side in ['left', 'right']] +
        [Output(f'taille-logette-input-{side.lower()}', 'value') for side in ['left', 'right']] +
        [Output(f'localisation-input-{side.lower()}', 'value') for side in ['left', 'right']] +
        [Output(f'edtrs-input-{side.lower()}', 'value') for side in ['left', 'right']],
        Input('analyze-button', 'n_clicks'),
        [State('upload-image', 'contents')] + 
        [State(f'{component}-{side.lower()}', 'value') 
         for side in ['left', 'right']
         for component in ['briding', 'decollement']],
        prevent_initial_call=True
    )
    def analyze_image(n_clicks, contents, left_briding, left_decollement, right_briding, right_decollement):
        if not n_clicks or not contents:
            return [None] * 22

        image_base64 = encode_image_contents(contents)
        raw_response = analyze_with_gpt(image_base64)
        analysis = process_gpt_response(raw_response)
        
        # Don't take GPT's results for briding and decollement - use existing values
        results = []
        
        # Process main components first (14 values total)
        for side in ['left', 'right']:
            eye_data = analysis[f'{side}_eye']
            main_values = [
                eye_data['dril']['status'],
                eye_data['oedeme']['status'],
                left_briding if side == 'left' else right_briding,  # Use the State values directly
                eye_data['mle'],
                eye_data['ze'],
                eye_data['points_hyperreflectifs']['status'],
                left_decollement if side == 'left' else right_decollement  # Use the State values directly
            ]
            results.extend(main_values)

        # Handle nb_logette values (positions 14-15)
        for side in ['left', 'right']:
            eye_data = analysis[f'{side}_eye']
            oedeme_data = eye_data['oedeme']
            results.append(oedeme_data['nb_logette'] if oedeme_data['status'] == 'Présent' else '')

        # Handle taille values (positions 16-17)
        for side in ['left', 'right']:
            eye_data = analysis[f'{side}_eye']
            oedeme_data = eye_data['oedeme']
            results.append(oedeme_data['taille'].lower() if oedeme_data['status'] == 'Présent' else '')

        # Handle localisation values (positions 18-19)
        for side in ['left', 'right']:
            eye_data = analysis[f'{side}_eye']
            oedeme_data = eye_data['oedeme']
            results.append(oedeme_data['localisation'] if oedeme_data['status'] == 'Présent' else '')

        # Handle EDTRS values (positions 20-21)
        for side in ['left', 'right']:
            eye_data = analysis[f'{side}_eye']
            retinal_thickness = eye_data['epaisseur_retinienne']
            
            if isinstance(retinal_thickness, dict):
                sections = {
                    'central': 'Central',
                    'superieur': 'Supérieur',
                    'inferieur': 'Inférieur',
                    'nasal': 'Nasal',
                    'temporal': 'Temporal'
                }
                edtrs_parts = []
                for key, label in sections.items():
                    value = retinal_thickness.get(key, '')
                    if value:
                        edtrs_parts.append(f"{label}: {value}μm")
                results.append(", ".join(edtrs_parts) if edtrs_parts else '')
            else:
                results.append('')

        # Print verification
        print("\n=== Value Mapping Verification ===")
        
        # Main components verification (0-13)
        components = ['dril', 'oedeme', 'briding', 'mle', 'ze', 'points', 'decollement']
        for side in ['left', 'right']:
            base_idx = 0 if side == 'left' else 7
            print(f"\n{side.upper()} EYE MAIN VALUES:")
            for i, comp in enumerate(components):
                print(f"{comp}: {results[base_idx + i]}")

        # Details verification (14-21)
        print("\nDETAILS VALUES:")
        details = ['nb_logette', 'taille', 'localisation', 'edtrs']
        for side in ['left', 'right']:
            print(f"\n{side.upper()} EYE DETAILS:")
            for i, field in enumerate(details):
                idx = 14 + (i * 2) + (0 if side == 'left' else 1)
                print(f"{field} [{idx}]: {results[idx]}")

        return results