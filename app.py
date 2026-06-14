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
                    # FIX: Add the missing Flask attribute dynamically so your module doesn't break
                    po_file.filename = po_file.name 
                    
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
                    # FIX: Add the missing Flask attribute dynamically so your module doesn't break
                    prod_file.filename = prod_file.name 
                    
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
                report_data = result.get('data')
                
                if report_data:
                    # 1. CONVERT DATA TO DATAFRAME
                    # Safely handle list of dicts or nested dictionaries
                    if isinstance(report_data, list):
                        df = pd.DataFrame(report_data)
                    elif isinstance(report_data, dict):
                        # If it is nested, adjust orientation or read directly
                        df = pd.DataFrame([report_data] if 'status' not in report_data else report_data)
                    else:
                        df = pd.DataFrame(report_data)

                    # --- EXCEL DOWNLOAD RECORDING FEATURE ---
                    # Create an in-memory buffer so it doesn't write clutter files to your cloud server
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Comparison_Report')
                    
                    # Construct download action button
                    st.download_button(
                        label="📥 Download Report as Excel",
                        data=buffer.getvalue(),
                        file_name=f"Comparison_Report_{selected_factory}_{selected_year}_{selected_season}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    st.divider()

                    # --- VISUAL DATA RESULTS ---
                    col_table, col_chart = st.columns([3, 2]) # 60% table space, 40% chart space
                    
                    with col_table:
                        st.markdown("#### 📋 Structured Results Table")
                        st.dataframe(df, use_container_width=True)
                        
                    with col_chart:
                        st.markdown("#### 📊 Metric Analytics Graphic")
                        
                        # Dynamically find valid numerical columns to graph automatically
                        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                        
                        if len(numeric_cols) > 0:
                            # If you have an explicit category column like 'item', 'month', or 'date'
                            # We check for common naming strings to index the chart labels cleanly
                            text_cols = df.select_dtypes(include=['object']).columns.tolist()
                            chart_index = text_cols[0] if text_cols else None
                            
                            # Render interactive bar visual
                            st.bar_chart(data=df, x=chart_index, y=numeric_cols, use_container_width=True)
                        else:
                            st.info("No numeric fields available in report payload to generate graphs.")
                            
                else:
                    st.info("Report completed but returned empty dataset metrics.")
            else:
                st.error(result.get('message', 'No active match parameters found.'))
