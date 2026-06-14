import streamlit as st
import io
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
    st.subheader("📊 Item-Wise PO Completion Analysis")
    st.markdown(f"**Analyzing:** {selected_factory} | Year: {selected_year} | Season: {selected_season}")
    
    if st.button("Generate Analytics & Comparison Report", use_container_width=True, type="primary"):
        with st.spinner("Processing datasets and calculating item metrics..."):
            result = compare_po_vs_production(
                selected_factory, 
                int(selected_year), 
                selected_season
            )
            
            if result.get('status') == 'success':
                report_data = result.get('data')
                
                if report_data:
                    # 1. READ RAW DATA DATASET
                   if report_data:
                    # --- FIXED DATA LOAD ENGINE ---
                    # Safely convert incoming payload to a DataFrame regardless of structure
                    if isinstance(report_data, dict):
                        # Wrap a single dictionary in a list so Pandas parses keys as columns
                        df_raw = pd.DataFrame([report_data])
                    elif isinstance(report_data, list):
                        df_raw = pd.DataFrame(report_data)
                    else:
                        df_raw = pd.DataFrame(report_data)
                    
                    # Ensure case-insensitive column matching for standard naming rules
                    df_raw.columns = [col.lower() for col in df_raw.columns]
                    
                    # Auto-detection safeguard if column naming varies
                    if not po_col or not prod_col:
                        # Fallback to search columns containing keywords
                        for col in df_raw.columns:
                            if 'po' in col: po_col = col
                            if 'prod' in col or 'production' in col: prod_col = col

                    if not po_col or not prod_col:
                        st.error("Could not find matching 'PO' or 'Production' quantity columns in the module data. Please check data schema headers.")
                        st.stop()

                    # 2. RUN COMPUTATIONAL ANALYTICS
                    # Fill blank numbers with zero to prevent breaking calculations
                    df_raw[po_col] = pd.to_numeric(df_raw[po_col]).fillna(0)
                    df_raw[prod_col] = pd.to_numeric(df_raw[prod_col]).fillna(0)
                    
                    # Group by item structure to combine duplicate rows safely
                    df_analysis = df_raw.groupby(item_col, as_index=False)[[po_col, prod_col]].sum()
                    
                    # Calculate metric variance columns
                    df_analysis['Shortage / Balance'] = df_analysis[prod_col] - df_analysis[po_col]
                    
                    # Calculate Completion Percentage safely (handle division by zero)
                    df_analysis['Completion %'] = (df_analysis[prod_col] / df_analysis[po_col] * 100).round(1)
                    df_analysis['Completion %'] = df_analysis['Completion %'].fillna(0).replace([float('inf'), float('-inf')], 100.0)

                    # Rename main columns cleanly for visualization rendering
                    df_analysis = df_analysis.rename(columns={
                        item_col: 'Item ID / Description',
                        po_col: 'Total PO Requested',
                        prod_col: 'Total Production Completed'
                    })

                    # 3. EXCEL EXPORT ENGINE (In-Memory Buffer tracking)
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_analysis.to_excel(writer, index=False, sheet_name='Item_Completion_Summary')
                    
                    st.download_button(
                        label="📥 Download Completion Excel Report",
                        data=buffer.getvalue(),
                        file_name=f"Completion_Report_{selected_factory}_{selected_year}_{selected_season}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    st.divider()

                    # 4. DATA VISUALIZATION GRAPHICS
                    st.markdown("#### 📈 Completion Percentage Matrix by Item")
                    
                    # We pass the Completion percentage column to build an easily scanable bar layout
                    st.bar_chart(
                        data=df_analysis, 
                        x='Item ID / Description', 
                        y='Completion %', 
                        use_container_width=True
                    )
                    
                    st.divider()

                    # 5. STRUCTURED DATAFRAME LAYOUT
                    st.markdown("#### 📋 Detailed Fulfillment Metrics Table")
                    
                    # Use configurations to inject clean progress bar visuals into the table
                    ui_config = {
                        "Total PO Requested": st.column_config.NumberColumn("PO Request (Units)", format="%d"),
                        "Total Production Completed": st.column_config.NumberColumn("Produced (Units)", format="%d"),
                        "Shortage / Balance": st.column_config.NumberColumn("Variance", format="%+d"),
                        "Completion %": st.column_config.ProgressColumn(
                            "Fulfillment Progress",
                            help="Percentage of production completed vs distributor request",
                            format="%.1f%%",
                            min_value=0,
                            max_value=100
                        )
                    }
                    
                    st.dataframe(
                        df_analysis,
                        column_config=ui_config,
                        hide_index=True,
                        use_container_width=True
                    )
                    
                else:
                    st.info("Report run complete, but returned an empty dataset layout structure.")
            else:
                st.error(result.get('message', 'No active matching parameters found.'))
