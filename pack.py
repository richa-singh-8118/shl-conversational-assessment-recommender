import os
import zipfile

def create_submission_zip():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_filename = os.path.join(os.path.dirname(base_dir), "SHL_Recommender_Submission.zip")
    
    exclude_dirs = {".pytest_cache", "__pycache__", ".git", "venv", "env"}
    exclude_files = {".env", "pack.py", "SHL_Recommender_Submission.zip"}
    
    print(f"Creating zip file at: {zip_filename}")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(base_dir):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file in exclude_files:
                    print(f"Excluding file: {file}")
                    continue
                    
                file_path = os.path.join(root, file)
                if file_path.endswith('.pyc') or file_path.endswith('.pyo'):
                    continue
                    
                arcname = os.path.relpath(file_path, base_dir)
                zipf.write(file_path, arcname)
                
    print(f"Successfully created {zip_filename}!")

if __name__ == "__main__":
    create_submission_zip()
