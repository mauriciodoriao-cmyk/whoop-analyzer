import os
import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from src.memory_manager import MemoryManager

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Usamos el modelo Flash que es ultra rápido y extremadamente barato
MODEL_NAME = 'gemini-flash-latest'

class GeminiBrain:
    def __init__(self):
        self.model = genai.GenerativeModel(MODEL_NAME)
        
    def generate_daily_report(self, cycle_data, recovery_data, sleep_data, workouts_data, user_notes=""):
        baseline = MemoryManager.get_baseline()
        
        # Matemáticas de Calorías
        # 1 kilojoule = 0.239006 kilocalories
        KJ_TO_KCAL = 0.239006
        
        total_kj = cycle_data.get('score', {}).get('kilojoule', 0) if cycle_data else 0
        total_kcal = int(total_kj * KJ_TO_KCAL)
        
        workout_kcal = 0
        workout_details = []
        for w in workouts_data:
            wk_kj = w.get('score', {}).get('kilojoule', 0)
            wk_kcal = int(wk_kj * KJ_TO_KCAL)
            workout_kcal += wk_kcal
            sport = w.get('sport_name', 'Actividad')
            workout_details.append(f"{sport}: {wk_kcal} kcal")
            
        basal_net_kcal = total_kcal - workout_kcal
        
        cal_math_context = f"""
CÁLCULO EXACTO DE CALORÍAS DEL DÍA:
- Calorías Totales: {total_kcal} kcal
- Calorías de Entrenamientos: {workout_kcal} kcal ({', '.join(workout_details) if workout_details else 'Ninguno'})
- Calorías Basales Netas (Totales - Ejercicio): {basal_net_kcal} kcal
"""

        prompt = f"""
Eres un analista médico experto (estilo consultor McKinsey). Genera un REPORTE EJECUTIVO para Mauricio.

DATOS DE WHOOP:
Ciclo (Ayer): {cycle_data}
Sueño (Noche pasada): {sleep_data}
Recuperación (Hoy): {recovery_data}
{cal_math_context}

HISTORIAL MÉDICO E INBODY (Baseline):
{baseline}

NOTAS ADICIONALES DEL USUARIO DE HOY (MUY IMPORTANTE):
{user_notes if user_notes else 'Ninguna.'}

INSTRUCCIONES CRÍTICAS:
1. DEVUELVE ÚNICAMENTE UN JSON VÁLIDO. No agregues texto fuera del JSON.
2. NO USES EMOJIS BAJO NINGUNA CIRCUNSTANCIA. Si quieres indicar una tendencia, usa flechas estéticas tipo ASCII (▲ o ▼).
3. Tu tono debe ser directo, ejecutivo y basado en datos clínicos.
4. El JSON debe tener esta estructura exacta:
{{
  "dashboard": {{
    "recovery_score": "70%",
    "recovery_insight": "Breve análisis de 2 líneas sobre HRV y RHR.",
    "sleep_score": "85%",
    "sleep_insight": "Breve análisis sobre la deuda de sueño y fases.",
    "total_calories": "{total_kcal} kcal",
    "basal_calories": "{basal_net_kcal} kcal",
    "workout_calories": "{workout_kcal} kcal",
    "strain_score": "12.5",
    "strain_insight": "Análisis del esfuerzo vs capacidad."
  }},
  "clinical_analysis": "Un texto largo en HTML (usando <p>, <ul>, <strong>) con un análisis profundo, cruzando la información de hoy con su perfil médico, disfunción HPA, tiroides y metas. Sin itálicas, todo formal y profesional.",
  "inbody_history": {{
    "has_data": true_o_false,
    "latest_weight": "XX kg",
    "weight_trend": "▲ +0.5 kg (opcional)",
    "latest_muscle": "XX kg",
    "muscle_trend": "",
    "latest_fat_percent": "XX%",
    "fat_percent_trend": "",
    "latest_fat_kg": "XX kg",
    "fat_kg_trend": "",
    "latest_water": "XX L",
    "water_trend": ""
  }},
  "action_plan": [
    "Acción 1 clara y directa",
    "Acción 2..."
  ]
}}
"""
        # Configuramos el modelo para que obligatoriamente devuelva JSON
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        return response.text

    def chat_and_update_memory(self, user_message, chat_history, whoop_data=None):
        baseline = MemoryManager.get_baseline()
        
        whoop_context = ""
        if whoop_data:
            whoop_context = f"""
DATOS DE WHOOP DE HOY (EN VIVO):
- Recuperación: {whoop_data.get('recovery', 'No disponible')}
- Sueño: {whoop_data.get('sleep', 'No disponible')}
- Ciclo/Esfuerzo Ayer: {whoop_data.get('cycle', 'No disponible')}
"""

        system_instruction = f"""
Eres el bot personal de salud de Mauricio.
Tu memoria/contexto actual es:
---
{baseline}
---
{whoop_context}

Si Mauricio dice "anota que..." o "guarda en memoria que..." o te pide actualizar su perfil, DEBES responder con EXACTAMENTE dos bloques de texto separados por una línea que diga "---UPDATE_MEMORY---".
El primer bloque será tu respuesta normal en chat. ¡ATENCIÓN AL FORMATO DEL CHAT!: Escríbela como texto plano muy limpio y profesional. NO USES ASTERISCOS (**) para negritas, NO USES SÍMBOLOS MATEMÁTICOS NI LATEX. Haz que parezca un mensaje premium de WhatsApp.
El segundo bloque será EL NUEVO CONTENIDO COMPLETO Y REESCRITO DEL ARCHIVO medical_baseline.md (incluyendo la nueva información integrada de manera formal). 
Si NO necesitas actualizar la memoria, solo responde de manera normal usando este mismo formato limpio.
"""
        
        # En una app real, guardaríamos el chat_history en una base de datos.
        # Aquí lo simplificamos a una llamada directa con contexto.
        full_prompt = f"{system_instruction}\n\nMensaje del usuario: {user_message}"
        response = self.model.generate_content(full_prompt)
        
        text = response.text
        if "---UPDATE_MEMORY---" in text:
            parts = text.split("---UPDATE_MEMORY---")
            reply = parts[0].strip()
            new_baseline = parts[1].strip()
            MemoryManager.update_baseline(new_baseline)
            return reply + "\n\n*(Memoria actualizada correctamente)*"
        else:
            return text

    def analyze_image_and_update_memory(self, image_path, user_message=""):
        import PIL.Image
        img = PIL.Image.open(image_path)
        baseline = MemoryManager.get_baseline()
        
        prompt = f"""
Eres un analista médico experto analizando un reporte InBody o documento médico.
El usuario dice: "{user_message}"

Tu tarea es:
1. Extraer la Fecha (del ticket), Peso, Masa Muscular, Grasa, % Grasa, Grasa Visceral y Agua.
2. Actualizar el archivo medical_baseline.md añadiendo una sección de "Historial InBody" (o actualizando la existente) con esta nueva entrada estructurada.
3. Responder al usuario resumiendo los datos leídos y comparándolos con su registro anterior si existe.

DEBES responder con EXACTAMENTE dos bloques de texto separados por una línea que diga "---UPDATE_MEMORY---".
El primer bloque será tu respuesta normal en chat. ¡ATENCIÓN AL FORMATO DEL CHAT!: Escríbela como texto plano muy limpio y profesional. NO USES ASTERISCOS (**) para negritas, NO USES SÍMBOLOS MATEMÁTICOS NI LATEX (como $\rightarrow$). Si necesitas hacer listas, usa guiones normales (-). Si necesitas resaltar, usa MAYÚSCULAS o emojis sutiles. Haz que parezca un reporte premium enviado por WhatsApp.
El segundo bloque será EL NUEVO CONTENIDO COMPLETO Y REESCRITO DEL ARCHIVO medical_baseline.md (este sí puede llevar Markdown).

Memoria actual:
{baseline}
"""
        response = self.model.generate_content([prompt, img])
        
        text = response.text
        if "---UPDATE_MEMORY---" in text:
            parts = text.split("---UPDATE_MEMORY---")
            reply = parts[0].strip()
            new_baseline = parts[1].strip()
            MemoryManager.update_baseline(new_baseline)
            return reply + "\n\n*(InBody guardado en tu expediente)*"
        else:
            return text


    def save_report_to_drive(self, report_text):
        """Guarda el reporte en la carpeta reports que se sincroniza con Google Drive."""
        reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        date_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(reports_dir, f"Reporte_Whoop_{date_str}.md")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_text)
        return filename
