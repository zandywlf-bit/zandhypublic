import os
import pandas as pd
from modules.file_manager import get_po_path, get_production_path, ensure_dir
from modules.file_validator import (
    validate_file_extension,
    validate_po_columns,
    validate_production_columns,
    validate_quantity_column,
    validate_season_column,
    validate_date_column
)
from config import Config


def handle_po_upload(factory: str, year: int, season: str, uploaded_file) -> dict:
    """Process PO upload: validate, merge, save"""
    # Validate file extension
    if not validate_file_extension(uploaded_file.filename):
        return {'status': 'error', 'message': 'Only .xlsx files are supported'}

    # Read Excel file
    try:
        df = pd.read_excel(uploaded_file)
    except Exception as e:
        return {'status': 'error', 'message': f'Could not read Excel file: {str(e)}'}

    # Validate columns
    is_valid, errors = validate_po_columns(df)
    if not is_valid:
        return {
            'status': 'error',
            'message': 'Missing required columns',
            'errors': [f"Missing column: {col}" for col in errors]
        }

    # Validate data quality
    data_errors = []
    is_valid_qty, qty_errors = validate_quantity_column(df['Quantity of Product'])
    if not is_valid_qty:
        data_errors.extend(qty_errors)

    is_valid_season, season_errors = validate_season_column(df['Type of Season'])
    if not is_valid_season:
        data_errors.extend(season_errors)

    is_valid_date, date_errors = validate_date_column(df['Date of Request'])
    if not is_valid_date:
        data_errors.extend(date_errors)

    if data_errors:
        return {
            'status': 'error',
            'message': 'Data validation errors',
            'errors': data_errors
        }

    # Normalize season to title case
    df['Type of Season'] = df['Type of Season'].str.strip().str.title()

    # Ensure Date column is proper datetime
    df['Date of Request'] = pd.to_datetime(df['Date of Request'], errors='coerce')

    # Merge with existing data
    target_path = get_po_path(factory, year, season)
    ensure_dir(os.path.dirname(target_path))

    existing_rows = 0
    if os.path.exists(target_path):
        try:
            existing_df = pd.read_excel(target_path)
            existing_rows = len(existing_df)
            df = pd.concat([existing_df, df], ignore_index=True)
            df = df.drop_duplicates()
            df = df.sort_values('Date of Request')
        except Exception as e:
            return {'status': 'error', 'message': f'Error merging with existing data: {str(e)}'}

    # Write to Excel
    try:
        df.to_excel(target_path, index=False)
    except Exception as e:
        return {'status': 'error', 'message': f'Error saving file: {str(e)}'}

    return {
        'status': 'success',
        'message': 'PO data uploaded successfully',
        'data': {
            'factory_name': factory,
            'year': year,
            'season': season,
            'file_path': target_path,
            'rows_added': len(df) - existing_rows,
            'total_rows': len(df)
        }
    }


def handle_production_upload(factory: str, year: int, season: str, uploaded_file) -> dict:
    """Process Production upload: validate, merge, save"""
    # Validate file extension
    if not validate_file_extension(uploaded_file.filename):
        return {'status': 'error', 'message': 'Only .xlsx files are supported'}

    # Read Excel file
    try:
        df = pd.read_excel(uploaded_file)
    except Exception as e:
        return {'status': 'error', 'message': f'Could not read Excel file: {str(e)}'}

    # Validate columns
    is_valid, errors = validate_production_columns(df)
    if not is_valid:
        return {
            'status': 'error',
            'message': 'Missing required columns',
            'errors': [f"Missing column: {col}" for col in errors]
        }

    # Validate data quality
    data_errors = []
    is_valid_qty, qty_errors = validate_quantity_column(df['Amount of Product Created'])
    if not is_valid_qty:
        data_errors.extend(qty_errors)

    is_valid_date, date_errors = validate_date_column(df['Date of Report'])
    if not is_valid_date:
        data_errors.extend(date_errors)

    if data_errors:
        return {
            'status': 'error',
            'message': 'Data validation errors',
            'errors': data_errors
        }

    # Ensure Date column is proper datetime
    df['Date of Report'] = pd.to_datetime(df['Date of Report'], errors='coerce')

    # Merge with existing data
    target_path = get_production_path(factory, year, season)
    ensure_dir(os.path.dirname(target_path))

    existing_rows = 0
    if os.path.exists(target_path):
        try:
            existing_df = pd.read_excel(target_path)
            existing_rows = len(existing_df)
            df = pd.concat([existing_df, df], ignore_index=True)
            df = df.drop_duplicates()
            df = df.sort_values('Date of Report')
        except Exception as e:
            return {'status': 'error', 'message': f'Error merging with existing data: {str(e)}'}

    # Write to Excel
    try:
        df.to_excel(target_path, index=False)
    except Exception as e:
        return {'status': 'error', 'message': f'Error saving file: {str(e)}'}

    return {
        'status': 'success',
        'message': 'Production report uploaded successfully',
        'data': {
            'factory_name': factory,
            'year': year,
            'season': season,
            'file_path': target_path,
            'rows_added': len(df) - existing_rows,
            'total_rows': len(df)
        }
    }