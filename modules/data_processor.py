import os
import pandas as pd
from modules.file_manager import get_po_path, get_production_path


def compare_po_vs_production(factory: str, year: int, season: str) -> dict:
    """Main comparison engine: compare distributor PO vs factory production"""
    po_path = get_po_path(factory, year, season)
    prod_path = get_production_path(factory, year, season)

    # Check if files exist
    if not os.path.exists(po_path):
        return {
            'status': 'error',
            'message': f'No PO data found for {factory}, {year}, {season}. Please upload distributor PO data first.'
        }
    if not os.path.exists(prod_path):
        return {
            'status': 'error',
            'message': f'No Production data found for {factory}, {year}, {season}. Please upload factory production report first.'
        }

    # Load data
    try:
        po_df = pd.read_excel(po_path)
        prod_df = pd.read_excel(prod_path)
    except Exception as e:
        return {'status': 'error', 'message': f'Error reading data files: {str(e)}'}

    # Validate data has required columns
    if 'Product Name' not in po_df.columns or 'Quantity of Product' not in po_df.columns:
        return {'status': 'error', 'message': 'PO data is missing required columns'}
    if 'Product Name' not in prod_df.columns or 'Amount of Product Created' not in prod_df.columns:
        return {'status': 'error', 'message': 'Production data is missing required columns'}

    # Aggregate by product
    po_agg = po_df.groupby('Product Name')['Quantity of Product'].sum().reset_index()
    prod_agg = prod_df.groupby('Product Name')['Amount of Product Created'].sum().reset_index()

    # Merge (outer join to catch products in one but not the other)
    merged = pd.merge(po_agg, prod_agg, on='Product Name', how='outer').fillna(0)

    # Rename for clarity
    merged.columns = ['product_name', 'requested_qty', 'produced_qty']
    merged['requested_qty'] = merged['requested_qty'].astype(int)
    merged['produced_qty'] = merged['produced_qty'].astype(int)

    # Calculate completion percentage
    merged['completion_pct'] = round(
        (merged['produced_qty'] / merged['requested_qty'].replace(0, 1)) * 100, 1
    )
    merged['completion_pct'] = merged['completion_pct'].clip(upper=100)

    # Assign status
    def assign_status(row):
        if row['completion_pct'] >= 100:
            return 'Complete'
        elif row['completion_pct'] > 0:
            return 'Partial'
        else:
            return 'Missing'

    merged['status'] = merged.apply(assign_status, axis=1)

    # Calculate summary
    total = len(merged)
    complete = len(merged[merged['status'] == 'Complete'])
    partial = len(merged[merged['status'] == 'Partial'])
    missing = len(merged[merged['status'] == 'Missing'])

    total_requested = merged['requested_qty'].sum()
    total_produced = merged['produced_qty'].sum()
    overall_pct = round(
        (total_produced / total_requested) * 100, 2
    ) if total_requested > 0 else 0

    comparison_list = merged.to_dict('records')

    return {
        'status': 'success',
        'data': {
            'filters': {
                'factory_name': factory,
                'year': year,
                'season': season
            },
            'comparison': comparison_list,
            'summary': {
                'total_products': total,
                'complete': int(complete),
                'partial': int(partial),
                'missing': int(missing),
                'total_requested': int(total_requested),
                'total_produced': int(total_produced),
                'overall_completion_pct': overall_pct
            }
        }
    }