import os
import re
from config import Config


def sanitize_name(name: str) -> str:
    """Replace spaces with underscores, remove special chars"""
    return re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')


def ensure_dir(path: str) -> str:
    """Create directory if not exists, return path"""
    os.makedirs(path, exist_ok=True)
    return path


def get_po_path(factory: str, year: int, season: str) -> str:
    """Construct full path for PO data file"""
    return os.path.join(
        Config.DATA_DIR, 'distributor_po',
        sanitize_name(factory), str(year), season.lower(), 'po_data.xlsx'
    )


def get_production_path(factory: str, year: int, season: str) -> str:
    """Construct full path for Production data file"""
    return os.path.join(
        Config.DATA_DIR, 'factory_report',
        str(year), season.lower(), f'{sanitize_name(factory)}_production.xlsx'
    )


def list_available_factories() -> list:
    """Scan filesystem for factory directories"""
    po_dir = os.path.join(Config.DATA_DIR, 'distributor_po')
    if not os.path.exists(po_dir):
        return Config.FACTORIES  # fallback to config
    factories = [d for d in os.listdir(po_dir)
                 if os.path.isdir(os.path.join(po_dir, d))]
    return sorted(factories) if factories else Config.FACTORIES


def list_available_years() -> list:
    """Scan filesystem for year directories across both PO and production"""
    years = set()
    for base in ['distributor_po', 'factory_report']:
        path = os.path.join(Config.DATA_DIR, base)
        if os.path.exists(path):
            for d in os.listdir(path):
                dir_path = os.path.join(path, d)
                if os.path.isdir(dir_path) and d.isdigit():
                    years.add(int(d))
    return sorted(years, reverse=True) or Config.YEARS