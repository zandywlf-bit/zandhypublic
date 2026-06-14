import streamlit
from flask import Flask, render_template, request, jsonify
import os
from config import Config
from modules.upload_handler import handle_po_upload, handle_production_upload
from modules.data_processor import compare_po_vs_production
from modules.file_manager import list_available_factories, list_available_years
app = Flask(__name__)
app.config.from_object(Config)

# Ensure data directories exist
os.makedirs(app.config['DATA_DIR'], exist_ok=True)
os.makedirs(os.path.join(app.config['DATA_DIR'], 'distributor_po'), exist_ok=True)
os.makedirs(os.path.join(app.config['DATA_DIR'], 'factory_report'), exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    """Serve main dashboard page"""
    factories = list_available_factories()
    years = list_available_years()
    return render_template('index.html',
                           factories=factories,
                           years=years,
                           seasons=Config.SEASONS)


@app.route('/api/upload/po', methods=['POST'])
def upload_po():
    """API endpoint for Distributor PO upload"""
    factory = request.form.get('factory_name')
    year = request.form.get('year')
    season = request.form.get('season')
    file = request.files.get('file')

    if not all([factory, year, season, file]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

    result = handle_po_upload(factory, int(year), season, file)
    status_code = 200 if result['status'] == 'success' else 400
    return jsonify(result), status_code


@app.route('/api/upload/production', methods=['POST'])
def upload_production():
    """API endpoint for Factory Production upload"""
    factory = request.form.get('factory_name')
    year = request.form.get('year')
    season = request.form.get('season')
    file = request.files.get('file')

    if not all([factory, year, season, file]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

    result = handle_production_upload(factory, int(year), season, file)
    status_code = 200 if result['status'] == 'success' else 400
    return jsonify(result), status_code


@app.route('/api/report/compare')
def get_comparison():
    """API endpoint to get comparison report"""
    factory = request.args.get('factory_name')
    year = request.args.get('year')
    season = request.args.get('season')

    if not all([factory, year, season]):
        return jsonify({'status': 'error', 'message': 'Missing filter parameters'}), 400

    result = compare_po_vs_production(factory, int(year), season)
    status_code = 200 if result['status'] == 'success' else 404
    return jsonify(result), status_code


@app.route('/api/factories')
def get_factories():
    """API endpoint to list available factories"""
    factories = list_available_factories()
    return jsonify({'status': 'success', 'data': {'factories': factories}})


@app.route('/api/filters')
def get_filters():
    """API endpoint to get all available filter options"""
    factories = list_available_factories()
    years = list_available_years()
    return jsonify({
        'status': 'success',
        'data': {
            'factories': factories,
            'years': years,
            'seasons': Config.SEASONS
        }
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5016, debug=False, use_reloader=False)
