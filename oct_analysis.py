# oct_analysis.py
"""
Module for OCT image analysis functionality in DeepOCT application.
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
        print("No OpenAI API key found. OCT analysis will use default values.")
        client = None
except ImportError:
    print("OpenAI package not installed. OCT analysis will use default values.")
    OpenAI = None
    client = None

def create_eye_section(side):
    """Create the eye section for OCT analysis results."""
    # Swap eye text display (Left position shows Right eye and vice versa)
    side_text = "Œil Droit" if side.lower() == "right" else "Œil Gauche"
    
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
                html.H5("Kyste intrarétinien", className="text-secondary"),
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
                html.H5("Ponts Rétiniens", className="text-secondary"),
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

def create_report_section():
    """Create the report synthesis section."""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "Synthétiser Rapport",
                    id="synthetize-report-btn",
                    color="success",
                    className="w-100 mt-3 mb-3",
                ),
                dbc.Collapse(
                    dbc.Card([
                        dbc.CardHeader("Synthèse du Rapport OCT"),
                        dbc.CardBody(
                            html.Div(id="synthesized-report", className="report-text")
                        )
                    ]),
                    id="report-collapse",
                    is_open=False,
                ),
                
                # Add new button for therapeutic plan
                dbc.Button(
                    "Proposer Plan Thérapeutique",
                    id="therapeutic-plan-btn",
                    color="info",
                    className="w-100 mt-3 mb-3",
                ),
                dbc.Collapse(
                    dbc.Card([
                        dbc.CardHeader("Plan Thérapeutique et Pronostic"),
                        dbc.CardBody(
                            html.Div(id="therapeutic-plan", className="therapeutic-text")
                        )
                    ]),
                    id="therapeutic-plan-collapse",
                    is_open=False,
                ),
            ], width=12)
        ])
    ], id="report-section")

def encode_image_contents(contents):
    """Encode image contents to base64."""
    content_type, content_string = contents.split(',')
    return content_string

def generate_default_analysis():
    """Generate default OCT analysis in case there's no GPT response."""
    default_analysis = {
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
    default_analysis["right_eye"] = copy.deepcopy(default_analysis["left_eye"])
    
    return default_analysis

def generate_therapeutic_plan(analysis_data, report_text, patient_info=None):
    """Generate a therapeutic plan and prognosis using GPT."""
    if client is None:
        print("No OpenAI client available. Cannot generate therapeutic plan.")
        return "Impossible de générer un plan thérapeutique sans clé API OpenAI."
    
    # Extract patient IVT information if available
    ivt_info = ""
    if patient_info:
        ivt_received = patient_info.get('ivt_recu', 'Non')
        ivt_info = f"Information importante: Ce patient a {'déjà' if ivt_received == 'Oui' else 'jamais'} reçu des IVT."
    
    # Create GPT prompt
    prompt = f"""
Partie 1: Synthèse du rapport OCT (déjà générée):
{report_text}

{ivt_info}

Partie 2:
Apres cette etape je voudrai que tu synthétise un plan therapeutique et des elements pronostic sur la recupération fonctionne/anatomique basé sur les biomarqueur present/absent, comme ceci:
Pour ce patient, ayant ou n'ayant pas déjà recu des IVT (information déjà remplie)
Plan thérapeutique:
- "nb d'injection", Internavale d'injection, molecule a priviligier
Pronostic:
- sur la récupération anatomique, ou visuelle en pourcentage (donner un pourcentage approximatif)
Je voudrai que tu me saisis des information correcte en te basant sur la présence/absence de certain biomarqueur qui sont determinant dans la récupération visuelle, tu peux te baser sur les derniers articles et recommandations sur le web pour me donner une réponse juste, et citer des references et des etudes pour appuyer la fiabilité de tes chiffres

Rappel important: Dans l'analyse OCT:
- OD (œil droit) correspond à ce qui était présenté dans la partie gauche de l'image
- OG (œil gauche) correspond à ce qui était présenté dans la partie droite de l'image

Données pour l'OD (œil droit):
{json.dumps(analysis_data["right_eye"], indent=2, ensure_ascii=False)}

Données pour l'OG (œil gauche):
{json.dumps(analysis_data["left_eye"], indent=2, ensure_ascii=False)}
"""

    try:
        print("\n=== Generating Therapeutic Plan with GPT ===")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un ophtalmologue expert qui élabore des plans thérapeutiques basés sur l'analyse OCT maculaire."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1000,
            temperature=0.2
        )
        
        plan_text = response.choices[0].message.content.strip()
        print("\n=== Generated Therapeutic Plan ===\n")
        print(plan_text)
        
        return plan_text
        
    except Exception as e:
        print(f"\n=== Therapeutic Plan Generation Error ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        return "Erreur lors de la génération du plan thérapeutique. Veuillez réessayer."

def generate_report(analysis_data):
    """Generate a synthetic report from analysis data using GPT."""
    if client is None:
        print("No OpenAI client available. Cannot generate report.")
        return "Impossible de générer un rapport sans clé API OpenAI."
    
    # Prepare data for GPT prompt
    left_eye = analysis_data.get("left_eye", {})
    right_eye = analysis_data.get("right_eye", {})
    
    # Create a summary of findings for each eye
    # Make sure to include briding and decollement values from the form
    report_data = {
        "left_eye": {
            "dril": left_eye.get("dril", {}).get("status", "Absente"),
            "oedeme": left_eye.get("oedeme", {}).get("status", "Absent"),
            "nb_logette": left_eye.get("oedeme", {}).get("nb_logette", ""),
            "taille_logette": left_eye.get("oedeme", {}).get("taille", ""),
            "localisation": left_eye.get("oedeme", {}).get("localisation", ""),
            "mle": left_eye.get("mle", "Continue"),
            "ze": left_eye.get("ze", "Continue"),
            "points": left_eye.get("points_hyperreflectifs", {}).get("status", "Absents"),
            "briding": left_eye.get("briding", "Absent"),  # Include briding value from form
            "decollement": left_eye.get("decollement", "Absent"),  # Include decollement value from form
            "epaisseur_retinienne": left_eye.get("epaisseur_retinienne", {}).get("central", "normal")
        },
        "right_eye": {
            "dril": right_eye.get("dril", {}).get("status", "Absente"),
            "oedeme": right_eye.get("oedeme", {}).get("status", "Absent"),
            "nb_logette": right_eye.get("oedeme", {}).get("nb_logette", ""),
            "taille_logette": right_eye.get("oedeme", {}).get("taille", ""),
            "localisation": right_eye.get("oedeme", {}).get("localisation", ""),
            "mle": right_eye.get("mle", "Continue"),
            "ze": right_eye.get("ze", "Continue"),
            "points": right_eye.get("points_hyperreflectifs", {}).get("status", "Absents"),
            "briding": right_eye.get("briding", "Absent"),  # Include briding value from form
            "decollement": right_eye.get("decollement", "Absent"),  # Include decollement value from form
            "epaisseur_retinienne": right_eye.get("epaisseur_retinienne", {}).get("central", "normal")
        }
    }
    
    # Update the prompt to explicitly mention the briding and decollement values
    prompt = f"""
Maintenant je voudrai selon les donnés des biomarqueur detecté, me donner une synthèse comme ceci:
Au total, l'oct maculaire met en évidence:
a l'OD : tu précise les elements suivant sous forme de paragraphe très bref:
- Si présence d'un oèdeme (epaisseur maculaire centrale augmentée) ou présence de logette d'oedeme
- Si effectivement il y'a un oedeme on cite les biomarqueur présent , puis les biomarqueur absent
- Si absence d'oèdeme (epaisseur normale et aucune logette detecté) on dit absence d'oèdeme. pas besoin de rajouter la presence/absence des biomarqueurs
- N'oublie pas d'inclure le statut des Ponts Rétiniens (bridging) et du Décollement Séreux Rétinien dans ton analyse
A L'OG : meme chose

Données pour l'OD:
{json.dumps(report_data["right_eye"], indent=2, ensure_ascii=False)}

Données pour l'OG:
{json.dumps(report_data["left_eye"], indent=2, ensure_ascii=False)}

Note: Kyste intrarétinien correspond à la présence de logettes d'œdème maculaire.
Note: Inclure également les informations sur les Ponts Rétiniens (bridging) et le Décollement Séreux Rétinien si présents.
"""

    try:
        print("\n=== Generating Synthesis Report with GPT ===")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un ophtalmologue expert qui rédige des rapports concis d'analyse OCT maculaire."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=500,
            temperature=0.2
        )
        
        report_text = response.choices[0].message.content.strip()
        print("\n=== Generated Report ===\n")
        print(report_text)
        
        return report_text
        
    except Exception as e:
        print(f"\n=== Report Generation Error ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        return "Erreur lors de la génération du rapport. Veuillez réessayer."

def analyze_with_gpt(image_base64):
    """Send the image to GPT-4 Vision and return the response."""
    if client is None:
        print("No OpenAI client available. Using default values.")
        return generate_default_analysis()
    
    prompt = """Je suis ophtalmologue et j'ai besoin que tu analyses cette image OCT maculaire. Fournis-moi une réponse JSON structurée uniquement, sans texte explicatif avant ou après.

TRÈS IMPORTANT - INSTRUCTIONS DE MAPPING:
- L'image OCT est divisée en DEUX PARTIES: GAUCHE et DROITE
- La partie GAUCHE de l'image (côté gauche) correspond à l'ŒIL DROIT (OD) du patient dans l'oct donné
- La partie DROITE de l'image (côté droit) correspond à l'ŒIL GAUCHE (OG) du patient dans l'oct donné
- Dans ta réponse JSON: 
  * Les données de l'ŒIL DROIT (partie GAUCHE de l'image) doivent être placées sous "right_eye"
  * Les données de l'ŒIL GAUCHE (partie DROITE de l'image) doivent être placées sous "left_eye"

Pour chaque œil (OD et OG), analyse les biomarqueurs suivants et retourne le résultat au format JSON :

1. DRIL (Désorganisation des couches rétiniennes internes)
   - Présence/absence
   - Si présent, décrire l'étendue

2. Kyste intrarétinien
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
- Tu n'as pas besoin d'évaluer le Décollement Séreux Rétinien ni les Ponts Rétiniens, ces évaluations seront faites par l'ophtalmologue

RAPPEL FINAL IMPORTANT:
- "right_eye" dans le JSON = ŒIL DROIT = partie GAUCHE de l'image 
- "left_eye" dans le JSON = ŒIL GAUCHE = partie DROITE de l'image

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
        print("Falling back to default values.")
        return generate_default_analysis()

def process_gpt_response(response):
    """Process and standardize the GPT output into a format compatible with the UI."""
    print("\n=== Processing GPT Response ===")
    
    default_structure = generate_default_analysis()

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

        # Standardize Oedeme status and details (now representing Kyste intrarétinien)
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

    # Callback for left oedeme details (now Kyste intrarétinien)
    @app.callback(
        Output('oedeme-details-left', 'style'),
        Input('oedeme-left', 'value'),
        prevent_initial_call=True
    )
    def toggle_oedeme_details_left(value):
        if value == 'Présent':
            return {'display': 'block'}
        return {'display': 'none'}
    
    # Callback for right oedeme details (now Kyste intrarétinien)
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


        # When creating results array, explicitly use the current briding and decollement values
        results = []
        
        # Process main components first (14 values total)
        for side in ['left', 'right']:
            eye_data = analysis[f'{side}_eye']
            main_values = [
                eye_data['dril']['status'],
                eye_data['oedeme']['status'],
                left_briding if side == 'left' else right_briding,  # Preserve current UI values
                eye_data['mle'],
                eye_data['ze'],
                eye_data['points_hyperreflectifs']['status'],
                left_decollement if side == 'left' else right_decollement  # Preserve current UI values
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

    # Register the report synthesis callback
    @app.callback(
        [Output("report-collapse", "is_open"),
        Output("synthesized-report", "children")],
        Input("synthetize-report-btn", "n_clicks"),
        [State("report-collapse", "is_open")] +
        [State(f'{component}-{side.lower()}', 'value') 
        for side in ['left', 'right']
        for component in ['dril', 'oedeme', 'briding', 'mle', 'ze', 'points', 'decollement']] +
        [State(f'nb-logette-input-{side.lower()}', 'value') for side in ['left', 'right']] +
        [State(f'taille-logette-input-{side.lower()}', 'value') for side in ['left', 'right']] +
        [State(f'localisation-input-{side.lower()}', 'value') for side in ['left', 'right']] +
        [State(f'edtrs-input-{side.lower()}', 'value') for side in ['left', 'right']],
        prevent_initial_call=True
    )
    def toggle_report_synthesis(n_clicks, is_open, 
                            dril_left, oedeme_left, briding_left, mle_left, ze_left, points_left, decollement_left,
                            dril_right, oedeme_right, briding_right, mle_right, ze_right, points_right, decollement_right,
                            nb_logette_left, nb_logette_right,
                            taille_left, taille_right,
                            localisation_left, localisation_right,
                            edtrs_left, edtrs_right):
        
        if not n_clicks:
            return is_open, ""
        
        # Build analysis data structure from form values
        # This ensures we use ALL current form values including briding and decollement
        analysis_data = {
            "left_eye": {
                "dril": {"status": dril_left if dril_left else "Absente", "extent": ""},
                "oedeme": {
                    "status": oedeme_left if oedeme_left else "Absent",
                    "nb_logette": nb_logette_left if nb_logette_left else "",
                    "taille": taille_left if taille_left else "",
                    "localisation": localisation_left if localisation_left else ""
                },
                "mle": mle_left if mle_left else "Continue",
                "ze": ze_left if ze_left else "Continue",
                "points_hyperreflectifs": {
                    "status": points_left if points_left else "Absents",
                    "nombre": "",
                    "localisation": ""
                },
                "briding": briding_left if briding_left else "Absent",  # Use current UI value
                "decollement": decollement_left if decollement_left else "Absent",  # Use current UI value
                "epaisseur_retinienne": {
                    "central": edtrs_left.split(",")[0].split(":")[1].strip() if edtrs_left and ":" in edtrs_left else ""
                }
            },
            "right_eye": {
                "dril": {"status": dril_right if dril_right else "Absente", "extent": ""},
                "oedeme": {
                    "status": oedeme_right if oedeme_right else "Absent",
                    "nb_logette": nb_logette_right if nb_logette_right else "",
                    "taille": taille_right if taille_right else "",
                    "localisation": localisation_right if localisation_right else ""
                },
                "mle": mle_right if mle_right else "Continue",
                "ze": ze_right if ze_right else "Continue",
                "points_hyperreflectifs": {
                    "status": points_right if points_right else "Absents",
                    "nombre": "",
                    "localisation": ""
                },
                "briding": briding_right if briding_right else "Absent",  # Use current UI value
                "decollement": decollement_right if decollement_right else "Absent",  # Use current UI value
                "epaisseur_retinienne": {
                    "central": edtrs_right.split(",")[0].split(":")[1].strip() if edtrs_right and ":" in edtrs_right else ""
                }
            }
        }
        
        # Generate report using the analysis data constructed from current form values
        report_text = generate_report(analysis_data)
        
        # Format report with paragraphs
        formatted_report = []
        for line in report_text.split('\n'):
            if line.strip():
                formatted_report.append(html.P(line))
        
        return not is_open, formatted_report
    
    # Register the therapeutic plan callback
    @app.callback(
        [Output("therapeutic-plan-collapse", "is_open"),
        Output("therapeutic-plan", "children")],
        Input("therapeutic-plan-btn", "n_clicks"),
        [State("therapeutic-plan-collapse", "is_open"),
        State("synthesized-report", "children")] +
        [State(f'{component}-{side.lower()}', 'value') 
        for side in ['left', 'right']
        for component in ['dril', 'oedeme', 'briding', 'mle', 'ze', 'points', 'decollement']] +
        [State(f'nb-logette-input-{side.lower()}', 'value') for side in ['left', 'right']] +
        [State(f'taille-logette-input-{side.lower()}', 'value') for side in ['left', 'right']] +
        [State(f'localisation-input-{side.lower()}', 'value') for side in ['left', 'right']] +
        [State(f'edtrs-input-{side.lower()}', 'value') for side in ['left', 'right']],
        prevent_initial_call=True
    )
    def toggle_therapeutic_plan(n_clicks, is_open, report_children,
                            dril_left, oedeme_left, briding_left, mle_left, ze_left, points_left, decollement_left,
                            dril_right, oedeme_right, briding_right, mle_right, ze_right, points_right, decollement_right,
                            nb_logette_left, nb_logette_right,
                            taille_left, taille_right,
                            localisation_left, localisation_right,
                            edtrs_left, edtrs_right):
        
        if not n_clicks:
            return is_open, ""
        
        # Extract report text from children
        report_text = ""
        if isinstance(report_children, list):
            for child in report_children:
                if isinstance(child, dict) and child.get('props', {}).get('children'):
                    report_text += child['props']['children'] + "\n"
        
        # Build analysis data structure from current form values
        # Including ALL fields (briding and decollement) from the UI
        analysis_data = {
            "left_eye": {
                "dril": {"status": dril_left if dril_left else "Absente", "extent": ""},
                "oedeme": {
                    "status": oedeme_left if oedeme_left else "Absent",
                    "nb_logette": nb_logette_left if nb_logette_left else "",
                    "taille": taille_left if taille_left else "",
                    "localisation": localisation_left if localisation_left else ""
                },
                "mle": mle_left if mle_left else "Continue",
                "ze": ze_left if ze_left else "Continue",
                "points_hyperreflectifs": {
                    "status": points_left if points_left else "Absents",
                    "nombre": "",
                    "localisation": ""
                },
                "briding": briding_left if briding_left else "Absent",  # Explicitly use UI value
                "decollement": decollement_left if decollement_left else "Absent",  # Explicitly use UI value
                "epaisseur_retinienne": {
                    "central": edtrs_left.split(",")[0].split(":")[1].strip() if edtrs_left and ":" in edtrs_left else ""
                }
            },
            "right_eye": {
                "dril": {"status": dril_right if dril_right else "Absente", "extent": ""},
                "oedeme": {
                    "status": oedeme_right if oedeme_right else "Absent",
                    "nb_logette": nb_logette_right if nb_logette_right else "",
                    "taille": taille_right if taille_right else "",
                    "localisation": localisation_right if localisation_right else ""
                },
                "mle": mle_right if mle_right else "Continue",
                "ze": ze_right if ze_right else "Continue",
                "points_hyperreflectifs": {
                    "status": points_right if points_right else "Absents",
                    "nombre": "",
                    "localisation": ""
                },
                "briding": briding_right if briding_right else "Absent",  # Explicitly use UI value
                "decollement": decollement_right if decollement_right else "Absent",  # Explicitly use UI value
                "epaisseur_retinienne": {
                    "central": edtrs_right.split(",")[0].split(":")[1].strip() if edtrs_right and ":" in edtrs_right else ""
                }
            }
        }
        
        # Generate therapeutic plan using current form values and the most recent report
        plan_text = generate_therapeutic_plan(analysis_data, report_text)
        
        # Format plan with paragraphs
        formatted_plan = []
        for line in plan_text.split('\n'):
            if line.strip():
                formatted_plan.append(html.P(line))
        
        return not is_open, formatted_plan

