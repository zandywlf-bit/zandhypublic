import pandas as pd
from config import Config


def validate_file_extension(filename: str) -> bool:
    """Check if file has .xlsx extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def validate_po_columns(df: pd.DataFrame) -> tuple:
    """Check PO Excel has required columns. Returns (is_valid, errors)"""
    required = ['Date of Request', 'Type of Season', 'Product Name', 'Quantity of Product']
    missing = [col for col in required if col not in df.columns]
    return (len(missing) == 0, missing)


def validate_production_columns(df: pd.DataFrame) -> tuple:
    """Check Production Excel has required columns. Returns (is_valid, errors)"""
    required = ['Date of Report', 'Product Name', 'Amount of Product Created']
    missing = [col for col in required if col not in df.columns]
    return (len(missing) == 0, missing)


def validate_quantity_column(series: pd.Series) -> tuple:
    """Validate quantity values are positive integers"""
    errors = []
    if series.dtype not in ['int64', 'float64']:
        errors.append(f"Column must contain numbers, got {series.dtype}")
    if (series <= 0).any():
        errors.append("All values must be positive numbers")
    return (len(errors) == 0, errors)


def validate_season_column(series: pd.Series) -> tuple:
    """Validate season values against allowed list"""
    valid_seasons = ['Summer', 'Winter', 'Fall', 'Spring']
    invalid = series[~series.isin(valid_seasons)].unique()
    if len(invalid) > 0:
        return (False, [f"Invalid season values: {list(invalid)}"])
    return (True, [])


def validate_date_column(series: pd.Series) -> tuple:
    """Validate date column can be parsed as datetime"""
    errors = []
    try:
        parsed = pd.to_datetime(series, errors='coerce')
        if parsed.isna().any():
            errors.append("Some values could not be parsed as dates")
    except Exception as e:
        errors.append(f"Date parsing error: {str(e)}")
    return (len(errors) == 0, errors)