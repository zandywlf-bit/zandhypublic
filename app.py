import streamlit as st
import os
import pandas as pd
from config import Config
from modules.upload_handler import handle_po_upload, handle_production_upload
from modules.data_processor import compare_po_vs_production
from modules.file_manager import list_available_factories, list_available_years

# --- 1. CONFIGURATION & DIRECTORIES ---
st.set_page_config(
    page_title="Factory Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure data directories exist safely
os.makedirs(Config.DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(Config.DATA_DIR, 'distributor_po'), exist_ok=True)
os.makedirs(os.path.join(Config.DATA_DIR, 'factory_report'), exist_ok=True)
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)


# --- 2. SIDEBAR FILTERS ---
st.sidebar.title("🔍 Report Filters")

# Fetch dropdown data from your modules
factories = list_available_factories()
years = list_available_years()

selected_factory = st.sidebar.selectbox("Select Factory Name", options=factories)
selected_year = st.sidebar.selectbox("Select Year", options=years)
selected_season = st.sidebar.selectbox("Select Season", options=Config.SEASONS)


# --- 3. MAIN DASHBOARD UI ---
st.title("🏭 Factory & PO Management Dashboard")
st.markdown("Upload documents or view production comparison metrics below.")

# Split interface cleanly using top tabs
tab1, tab2 = st.tabs(["📤 Upload Data Control", "📊 View Comparison Report"])

# --- TAB 1: UPLOADS ---
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distributor PO Upload")
        po_file = st.file_uploader(
            "Choose PO File", 
            type=["xlsx", "csv"], 
            key="po_uploader"
        )
        
        if st.button("Upload & Process PO", type="primary", use_container_width=True):
            if not po_file:
                st.warning("Please choose a file to upload first.")
            else:
                with st.spinner("Processing Distributor PO..."):
                    result = handle_po_upload(
                        selected_factory, 
                        int(selected_year), 
                        selected_season, 
                        po_file
                    )
                    if result.get('status') == 'success':
                        st.success(result.get('message', 'PO Upload successful!'))
                    else:
                        st.error(result.get('message', 'Failed to process PO.'))

    with col2:
        st.subheader("Factory Production Upload")
        prod_file = st.file_uploader(
            "Choose Production File", 
            type=["xlsx", "csv"], 
            key="prod_uploader"
        )
        
        if st.button("Upload & Process Production", type="primary", use_container_width=True):
            if not prod_file:
                st.warning("Please choose a file to upload first.")
            else:
                with st.spinner("Processing Production Data..."):
                    result = handle_production_upload(
                        selected_factory, 
                        int(selected_year), 
                        selected_season, 
                        prod_file
                    )
                    if result.get('status') == 'success':
                        st.success(result.get('message', 'Production report upload successful!'))
                    else:
                        st.error(result.get('message', 'Failed to process Production data.'))


# --- TAB 2: COMPARISON REPORT ---
with tab2:
    st.subheader("PO vs Production Discrepancy Matrix")
    
    if st.button("Generate Comparison Report", use_container_width=True):
        with st.spinner("Analyzing datasets..."):
            result = compare_po_vs_production(
                selected_factory, 
                int(selected_year), 
                selected_season
            )
            
            if result.get('status') == 'success':
                st.success("Analysis complete!")
                
                # Extract data payload from your data_processor module
                report_data = result.get('data')
                
                if report_data:
                    # Dynamically convert dictionary arrays into interactive tables
                    if isinstance(report_data, list):
                        st.dataframe(pd.DataFrame(report_data), use_container_width=True)
                    elif isinstance(report_data, dict):
                        st.json(report_data)
                    else:
                        st.write(report_data)
                else:
                    st.info("Report completed but returned empty dataset metrics.")
            else:
                st.error(result.get('message', 'No active match parameters found.'))
