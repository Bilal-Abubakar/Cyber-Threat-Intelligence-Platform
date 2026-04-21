import shutil
import datetime
import os

DATABASE_FILE = "assets.db"
BACKUP_FOLDER = "backups"

def backup_db():
    if not os.path.exists(DATABASE_FILE):
        print(f"Error: {DATABASE_FILE} does not exist.")
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"assets_backup_{timestamp}.db"

    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)

    backup_path = os.path.join(BACKUP_FOLDER, backup_filename)
    shutil.copy(DATABASE_FILE, backup_path)

    print(f"Backup successful! The backup is saved as {backup_path}")

if __name__ == '__main__':
    backup_db()