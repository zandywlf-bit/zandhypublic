import os

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'xlsx'}
    
    # Default factory list (can be extended)
    FACTORIES = [
        'Factory A', 'Factory B', 'Factory C', 'Factory D', 'Factory E'
    ]
    
    SEASONS = ['Summer', 'Winter', 'Fall', 'Spring']
    YEARS = [2024, 2025, 2026]