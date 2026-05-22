# Arquitectura: Telegram Whoop Bot

Crear un Bot de Telegram privado que funcione como interfaz única. El bot enviará automáticamente el reporte matutino de Whoop, permitirá hacer preguntas de seguimiento y actualizará automáticamente la memoria médica (`medical_baseline.md`) con base en la conversación.

## Arquitectura de Memoria
*   `context/medical_baseline.md`: Perfil médico, rutinas y objetivos. El bot lee este archivo para contextualizar y lo sobreescribe cuando hay nuevos descubrimientos en el chat.
*   `context/history_log.json`: Archivo que guarda las métricas de las últimas semanas.

## Componentes
*   `bot.py`: Controlador de Telegram (recibe y envía mensajes).
*   `whoop_client.py`: Extrae los datos diarios de Whoop.
*   `gemini_brain.py`: Construye los prompts, usa Gemini API para responder y detecta si debe actualizar la memoria.
*   `memory_manager.py`: Lógica para modificar `medical_baseline.md`.

## Credenciales Necesarias
1. Whoop API Client ID & Secret
2. Gemini API Key
3. Telegram Bot Token
