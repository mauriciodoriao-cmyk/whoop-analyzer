import markdown
import os
from datetime import datetime

import json

def generate_and_save_html_report(json_string, base_dir):
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        # Fallback if Gemini failed to generate valid JSON
        print(f"Error parsing JSON: {e}")
        data = {"clinical_analysis": "<p>Error de formato. Datos crudos:</p><pre>" + json_string + "</pre>"}

    dash = data.get("dashboard", {})
    inbody = data.get("inbody_history", {})
    analysis = data.get("clinical_analysis", "")
    plan = data.get("action_plan", [])

    # Construir lista de acciones HTML
    plan_html = "<ul>"
    for item in plan:
        plan_html += f"<li>{item}</li>"
    plan_html += "</ul>"

    inbody_html = ""
    if inbody.get("has_data"):
        inbody_html = f"""
        <div class="inbody-dashboard">
            <h3>Último InBody</h3>
            <div class="inbody-grid">
                <div class="kpi-mini">
                    <span class="val">{inbody.get("latest_weight", "-")}</span>
                    <span class="lbl">Peso</span>
                    <span class="trend">{inbody.get("weight_trend", "")}</span>
                </div>
                <div class="kpi-mini">
                    <span class="val">{inbody.get("latest_muscle", "-")}</span>
                    <span class="lbl">Músculo</span>
                    <span class="trend">{inbody.get("muscle_trend", "")}</span>
                </div>
                <div class="kpi-mini">
                    <span class="val">{inbody.get("latest_fat_kg", "-")}</span>
                    <span class="lbl">Grasa (kg)</span>
                    <span class="trend">{inbody.get("fat_kg_trend", "")}</span>
                </div>
                <div class="kpi-mini">
                    <span class="val">{inbody.get("latest_fat_percent", "-")}</span>
                    <span class="lbl">% Grasa</span>
                    <span class="trend">{inbody.get("fat_percent_trend", inbody.get("fat_trend", ""))}</span>
                </div>
                <div class="kpi-mini">
                    <span class="val">{inbody.get("latest_water", "-")}</span>
                    <span class="lbl">Agua (L)</span>
                    <span class="trend">{inbody.get("water_trend", "")}</span>
                </div>
            </div>
        </div>
        """

    css = """
    :root {
        --mc-blue: #002D62;
        --mc-olive: #556B2F;
        --mc-brick: #C41E3A;
        --mc-gray: #4A4A4A;
        --mc-light-gray: #F4F6F8;
    }
    body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #E9ECEF; color: #333; line-height: 1.6; margin: 0; padding: 40px 20px; }
    .container { max-width: 900px; margin: 0 auto; background: #fff; padding: 40px 50px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border-top: 8px solid var(--mc-blue); }
    h1 { color: var(--mc-blue); font-size: 2.2em; border-bottom: 2px solid var(--mc-brick); padding-bottom: 10px; margin-top: 0; text-transform: uppercase; letter-spacing: 1px; }
    h2 { color: var(--mc-olive); font-size: 1.5em; margin-top: 40px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
    p, li { font-size: 0.95em; color: #444; font-style: normal !important; }
    strong { color: var(--mc-blue); }
    
    /* DASHBOARD GRID */
    .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px; }
    .kpi-card { background: var(--mc-light-gray); border-left: 4px solid var(--mc-olive); padding: 20px; border-radius: 6px; }
    .kpi-card.red { border-left-color: var(--mc-brick); }
    .kpi-card.blue { border-left-color: var(--mc-blue); }
    .kpi-value { font-size: 2.5em; font-weight: bold; color: var(--mc-blue); line-height: 1; margin-bottom: 5px; }
    .kpi-label { font-size: 0.8em; text-transform: uppercase; color: #777; letter-spacing: 1px; margin-bottom: 10px; font-weight: bold; }
    .kpi-insight { font-size: 0.85em; color: #555; font-style: normal; }
    
    /* INBODY DASHBOARD */
    .inbody-dashboard { margin-top: 30px; background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; }
    .inbody-grid { display: flex; justify-content: space-around; flex-wrap: wrap; gap: 15px; }
    .kpi-mini { text-align: center; }
    .kpi-mini .val { display: block; font-size: 1.5em; font-weight: bold; color: var(--mc-gray); }
    .kpi-mini .lbl { display: block; font-size: 0.7em; text-transform: uppercase; color: #888; }
    .kpi-mini .trend { display: block; font-size: 0.75em; color: var(--mc-olive); font-weight: bold; margin-top: 5px; }
    
    .footer { text-align: center; color: #888; margin-top: 50px; font-size: 0.8em; border-top: 1px solid #eee; padding-top: 20px; }
    """

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reporte Ejecutivo Whoop</title>
        <style>{css}</style>
    </head>
    <body>
        <div class="container">
            <h1>Reporte Ejecutivo</h1>
            
            <div class="dashboard-grid">
                <div class="kpi-card">
                    <div class="kpi-value">{dash.get('recovery_score', '-')}</div>
                    <div class="kpi-label">Recuperación</div>
                    <div class="kpi-insight">{dash.get('recovery_insight', '-')}</div>
                </div>
                <div class="kpi-card blue">
                    <div class="kpi-value">{dash.get('sleep_score', '-')}</div>
                    <div class="kpi-label">Rendimiento de Sueño</div>
                    <div class="kpi-insight">{dash.get('sleep_insight', '-')}</div>
                </div>
                <div class="kpi-card red">
                    <div class="kpi-value">{dash.get('strain_score', '-')}</div>
                    <div class="kpi-label">Esfuerzo Ayer</div>
                    <div class="kpi-insight">{dash.get('strain_insight', '-')}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">{dash.get('basal_calories', '-')}</div>
                    <div class="kpi-label">Calorías Basales (Netas)</div>
                    <div class="kpi-insight">Totales: {dash.get('total_calories', '-')} | Ejercicio: {dash.get('workout_calories', '-')}</div>
                </div>
            </div>

            {inbody_html}

            <h2>Análisis Clínico</h2>
            <div>{analysis}</div>

            <h2>Plan de Acción</h2>
            {plan_html}

            <div class="footer">
                Generado por Whoop AI Assistant &bull; {datetime.now().strftime('%d de %B, %Y')}
            </div>
        </div>
    </body>
    </html>
    """

    filename = f"reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    reports_dir = os.path.join(base_dir, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    filepath = os.path.join(reports_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
        
    # Subir a Google Drive
    from src.drive_client import DriveClient
    drive = DriveClient()
    if drive.service:
        drive.upload_file(filepath, filename, "Reportes Diarios")
        
    return filepath
