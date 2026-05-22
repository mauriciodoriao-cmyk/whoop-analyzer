import os
from src.drive_client import DriveClient

class MemoryManager:
    @staticmethod
    def get_baseline():
        """Lee el medical_baseline.md desde Google Drive o local fallback."""
        drive = DriveClient()
        # Fallback local
        local_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'context', 'medical_baseline.md')
        
        # Descargar de Drive si existe
        if drive.service:
            temp_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp_baseline.md')
            if drive.download_file_by_name("medical_baseline.md", temp_path):
                with open(temp_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                os.remove(temp_path)
                return content
                
        # Si falla Drive o no está configurado, intentar local
        if os.path.exists(local_path):
            with open(local_path, 'r', encoding='utf-8') as f:
                return f.read()
        return "No baseline found."

    @staticmethod
    def update_baseline(new_content):
        """Actualiza el medical_baseline.md en Google Drive y localmente."""
        local_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'context', 'medical_baseline.md')
        
        # Update localmente por redundancia
        if os.path.exists(local_path):
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
        # Subir a Google Drive
        drive = DriveClient()
        if drive.service:
            drive.upload_content(new_content, "medical_baseline.md")
