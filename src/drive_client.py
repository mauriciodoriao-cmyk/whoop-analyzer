import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']

class DriveClient:
    def __init__(self):
        self.creds = None
        
        base_dir = os.path.dirname(os.path.dirname(__file__))
        token_path = os.path.join(base_dir, 'token.json')
        creds_path = os.path.join(base_dir, 'credentials.json')
        
        # 1. Intentar cargar OAuth Token de usuario (Opción B)
        if os.path.exists(token_path):
            from google.oauth2.credentials import Credentials
            self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        # 2. Fallback a Service Account (Opción A)
        elif os.path.exists(creds_path):
            self.creds = service_account.Credentials.from_service_account_file(
                creds_path, scopes=SCOPES)
        else:
            print("ERROR: Ni token.json ni credentials.json encontrados.")
            
        self.service = build('drive', 'v3', credentials=self.creds) if self.creds else None
        self.folder_id = self._get_or_create_root_folder("Whoop Analyzer")

    def _get_or_create_root_folder(self, folder_name):
        if not self.service:
            return None
            
        # Buscar carpeta
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
        results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])
        
        if items:
            return items[0]['id']
        else:
            # En teoría el usuario la compartió, si no la encuentra podría no tener permisos.
            print(f"ADVERTENCIA: No se encontró la carpeta '{folder_name}'. ¿Está compartida con el bot?")
            return None

    def upload_file(self, file_path, file_name=None, subfolder_name=None):
        if not self.service or not self.folder_id:
            return None
            
        if not file_name:
            file_name = os.path.basename(file_path)
            
        parent_id = self.folder_id
        if subfolder_name:
            # Buscar o crear subcarpeta
            query = f"mimeType='application/vnd.google-apps.folder' and name='{subfolder_name}' and '{self.folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id)').execute()
            items = results.get('files', [])
            if items:
                parent_id = items[0]['id']
            else:
                folder_metadata = {
                    'name': subfolder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [self.folder_id]
                }
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                parent_id = folder.get('id')

        # Subir archivo
        try:
            file_metadata = {'name': file_name, 'parents': [parent_id]}
            media = MediaFileUpload(file_path, resumable=True)
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            return file.get('id')
        except Exception as e:
            print(f"Error subiendo archivo a Drive: {e}")
            return None

    def download_file_by_name(self, file_name, dest_path):
        """Descarga un archivo desde la carpeta raíz si existe."""
        if not self.service or not self.folder_id:
            return False
            
        query = f"name='{file_name}' and '{self.folder_id}' in parents and trashed=false"
        results = self.service.files().list(q=query, spaces='drive', fields='files(id)').execute()
        items = results.get('files', [])
        
        if not items:
            return False
            
        file_id = items[0]['id']
        request = self.service.files().get_media(fileId=file_id)
        
        with io.FileIO(dest_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
        return True

    def upload_content(self, content, file_name):
        """Sube texto directo como archivo (sin usar archivos locales intermedios)"""
        from googleapiclient.http import MediaIoBaseUpload
        import io
        
        if not self.service or not self.folder_id:
            return None
            
        # Buscar si ya existe para actualizarlo o crearlo nuevo
        query = f"name='{file_name}' and '{self.folder_id}' in parents and trashed=false"
        results = self.service.files().list(q=query, spaces='drive', fields='files(id)').execute()
        items = results.get('files', [])
        
        file_metadata = {'name': file_name}
        
        # Crear archivo en memoria
        fh = io.BytesIO(content.encode('utf-8'))
        media = MediaIoBaseUpload(fh, mimetype='text/plain', resumable=True)
        
        try:
            if items:
                # Update
                file_id = items[0]['id']
                file = self.service.files().update(fileId=file_id, media_body=media).execute()
            else:
                # Create
                file_metadata['parents'] = [self.folder_id]
                file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            return file.get('id')
        except Exception as e:
            print(f"Error subiendo contenido a Drive: {e}")
            return None
