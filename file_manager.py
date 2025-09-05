import os
import shutil
import logging
from datetime import datetime

class FileManager:
    def __init__(self, upload_dir='uploaded_files'):
        self.upload_dir = os.path.abspath(upload_dir)
        self.logs_dir = os.path.abspath('logs')
        for directory in [self.upload_dir, self.logs_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def upload_file(self, file_path, max_size_mb=50, allowed_extensions=None):
        """Télécharger un fichier."""
        if allowed_extensions is None:
            allowed_extensions = ['.html', '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico']

        if not any(file_path.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f"File type not allowed. Allowed: {', '.join(allowed_extensions)}")

        if os.path.getsize(file_path) > max_size_mb * 1024 * 1024:
            raise ValueError(f"File size exceeds {max_size_mb} MB")

        file_name = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(file_name)
        new_file_name = f"{timestamp}_{name}{ext}"
        dest_path = os.path.join(self.upload_dir, new_file_name)
        shutil.copy2(file_path, dest_path)
        logging.info(f"File uploaded: {new_file_name}")
        return new_file_name

    def list_files(self):
        """Lister les fichiers téléchargés."""
        files_info = []
        if not os.path.exists(self.upload_dir):
            return files_info

        for file in os.listdir(self.upload_dir):
            file_path = os.path.join(self.upload_dir, file)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                files_info.append({
                    'name': file,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'path': file_path
                })
        return files_info

    def delete_file(self, file_name):
        """Supprimer un fichier."""
        file_path = os.path.join(self.upload_dir, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"File deleted: {file_name}")
            return True
        return False

    def rename_file(self, old_name, new_name):
        """Renommer un fichier."""
        old_path = os.path.join(self.upload_dir, old_name)
        new_path = os.path.join(self.upload_dir, new_name)
        if os.path.exists(old_path) and not os.path.exists(new_path):
            os.rename(old_path, new_path)
            logging.info(f"File renamed from {old_name} to {new_name}")
            return True
        return False
