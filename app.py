import streamlit as st
import io
import os
import pandas as pd
from config import Config
from modules.upload_handler import handle_po_upload, handle_production_upload
from modules.data_processor import compare_po_vs_production
from modules.file_manager import list_available_factories, list_available_years

# --- 1. INITIAL APP CONFIGURATION ---
st.set_page_config(
    page_title="Factory & PO Management Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure data directories exist safely on the server backend
os.makedirs(Config.DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(Config.DATA_DIR, 'distributor_po'), exist_ok=True)
os.makedirs(os.path.join(Config.DATA_DIR, 'factory_report'), exist_ok=True)
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)


# --- 2. SIDEBAR NAVIGATION FILTERS ---
st.sidebar.title("🔍 Report Filters")

# Fetch operational filtering options from your modules
factories = list_available_factories()
years = list_available_years()

selected_factory = st.sidebar.selectbox("Select Factory Name", options=factories)
selected_year = st.sidebar.selectbox("Select Year", options=years)
selected_season = st.sidebar.selectbox("Select Season", options=Config.SEASONS)


# --- 3. MAIN DASHBOARD INTERFACE UI ---
st.title("🏭 Factory & PO Management Dashboard")
st.markdown("Upload structural data sets or generate immediate fulfillment comparison metrics below.")

# Split interface control flow using visual top layout tabs
tab1, tab2 = st.tabs(["📤 Upload Data Control", "📊 View Comparison Report"])


# --- TAB 1: FILE UPLOADS CONTROL ---
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distributor PO Upload")
        po_file = st.file_uploader(
            "Choose PO File", 
            type=["xlsx", "csv"], 
            key="po_uploader"
        )
        
        if st.button("Upload & Process PO", type="primary", width='stretch'):
            if not po_file:
                st.warning("Please choose a file to upload first.")
            else:
                with st.spinner("Processing Distributor PO..."):
                    # Patch Flask filename dependency dynamically
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
        
        if st.button("Upload & Process Production", type="primary", width='stretch'):
            if not prod_file:
                st.warning("Please choose a file to upload first.")
            else:
                with st.spinner("Processing Production Data..."):
                    # Patch Flask filename dependency dynamically
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


# --- TAB 2: ANALYTICS & COMPARISON REPORT ---
with tab2:
    st.subheader("📊 Item-Wise PO Completion Analysis")
    st.markdown(f"**Analyzing:** {selected_factory} | Year: {selected_year} | Season: {selected_season}")
    
    if st.button("Generate Analytics & Comparison Report", width='stretch', type="primary"):
        with st.spinner("Processing datasets and calculating item metrics..."):
            result = compare_po_vs_production(
                selected_factory, 
                int(selected_year), 
                selected_season
            )
            
            if result.get('status') == 'success':
                report_data = result.get('data')
                
                if report_data:
                    # 1. DATA LOAD ENGINE (Flattens nested/unhashable structures)
                    if isinstance(report_data, dict):
                        df_raw = pd.DataFrame([report_data])
                    elif isinstance(report_data, list):
                        if len(report_data) == 1 and isinstance(report_data, dict):
                            df_raw = pd.DataFrame(list(report_data.items()), columns=['Key', 'Value'])
                        else:
                            df_raw = pd.DataFrame(report_data)
                    elif isinstance(report_data, pd.DataFrame):
                        df_raw = report_data.copy()
                    else:
                        df_raw = pd.DataFrame(report_data)
                    
                    # Flatten MultiIndex column Tuples if they exist
                    clean_columns = []
                    for col in df_raw.columns:
                        if isinstance(col, tuple):
                            col_str = "_".join([str(c).strip() for c in col if str(c).strip() and "unnamed" not in str(c).lower()])
                        else:
                            col_str = str(col).strip()
                        clean_columns.append(col_str.lower())
                    df_raw.columns = clean_columns
                    
                    # 2. COLUMN DETECTION ENGINE (Guaranteed String Output)
                    item_col = None
                    po_col = None
                    prod_col = None

                    # Attempt clean keyword tracing
                    for col in df_raw.columns:
                        col_str = str(col)
                        if any(keyword in col_str for keyword in ['item', 'product', 'desc', 'code', 'name', 'article', 'key']):
                            item_col = col_str
                        elif any(keyword in col_str for keyword in ['po', 'request', 'order', 'qty', 'target', 'demand']):
                            if 'prod' not in col_str and 'actual' not in col_str and 'complete' not in col_str:
                                po_col = col_str
                        elif any(keyword in col_str for keyword in ['prod', 'complete', 'actual', 'manufacture', 'made', 'done']):
                            prod_col = col_str

                    # Strict single-string positional fallbacks to eliminate data types error
                    available_cols = [str(c) for c in df_raw.columns]
                    if len(available_cols) > 0:
                        if not item_col:
                            item_col = available_cols[0]
                        if not po_col:
                            po_col = available_cols[1] if len(available_cols) > 1 else available_cols[0]
                        if not prod_col:
                            if len(available_cols) > 2:
                                prod_col = available_cols[2]
                            elif len(available_cols) > 1:
                                prod_col = available_cols[1]
                            else:
                                prod_col = available_cols[0]

                    # Terminal protection checkpoint
                    if not po_col or not prod_col or not item_col:
                        st.error(f"Could not determine layout tracking columns. Available headers: {available_cols}")
                        st.stop()

                    # Convert unhashable items explicitly to standard text strings
                    df_raw[item_col] = df_raw[item_col].astype(str)

                    # 3. COMPUTATIONAL ANALYTICS
                    # Clean values and parse strings to numbers safely
                    df_raw[po_col] = pd.to_numeric(df_raw[po_col], errors='coerce').fillna(0)
                    df_raw[prod_col] = pd.to_numeric(df_raw[prod_col], errors='coerce').fillna(0)
                    
                    # Consolidate repeating lines safely
                    df_analysis = df_raw.groupby(item_col, as_index=False)[[po_col, prod_col]].sum()
                    
                    # Calculate tracking balance and variance rows
                    df_analysis['Shortage / Balance'] = df_analysis[prod_col] - df_analysis[po_col]
                    
                    # Safe completion percentage engine framework
                    df_analysis['Completion %'] = (df_analysis[prod_col] / df_analysis[po_col] * 100).round(1)
                    df_analysis['Completion %'] = df_analysis['Completion %'].fillna(0).replace([float('inf'), float('-inf')], 100.0)

                    # Standardize visual headers cleanly for presentation layer layout
                    df_analysis = df_analysis.rename(columns={
                        item_col: 'Item ID / Description',
                        po_col: 'Total PO Requested',
                        prod_col: 'Total Production Completed'
                    })

                    # 4. EXCEL EXPORT ENGINE (In-Memory Binary Stream Buffer)
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_analysis.to_excel(writer, index=False, sheet_name='Item_Fulfillment_Summary')
                    
                    st.download_button(
                        label="📥 Download Completion Excel Report",
                        data=buffer.getvalue(),
                        file_name=f"Fulfillment_Report_{selected_factory}_{selected_year}_{selected_season}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    st.divider()

                    # 5. VISUAL METRIC GRAPHICS PANEL
                    st.markdown("#### 📈 Completion Percentage Matrix by Item")
                    st.bar_chart(
                        data=df_analysis, 
                        x='Item ID / Description', 
                        y='Completion %', 
                        use_container_width=True
                    )
                    
                    st.divider()

					 # 6. ENHANCED DATAFRAME PROGRESS VISUALIZATION TABLE
                    st.markdown("#### 📋 Detailed Fulfillment Metrics Table")
                    
                    # Configuration schema to map column presentation rules dynamically
                    ui_config = {
                        "Item ID / Description": st.column_config.TextColumn(
                            label="🆔 Item Details",
                            help="Product unique identification name or barcode string",
                            width="large",
                            required=True
                        ),
                        "Total PO Requested": st.column_config.NumberColumn(
                            label="📦 PO Request (Units)",
                            help="Total inventory volume requested by the distributor",
                            format="%d",
                            width="medium"
                        ),
                        "Total Production Completed": st.column_config.NumberColumn(
                            label="🏭 Produced (Units)",
                            help="Total actual manufacturing volume produced by the factory",
                            format="%d",
                            width="medium"
                        ),
                        "Shortage / Balance": st.column_config.NumberColumn(
                            label="⚖️ Variance",
                            help="Production discrepancy balance: positive indicates surplus, negative indicates shortage",
                            format="%+d",
                            width="medium"
                        ),
                        "Completion %": st.column_config.ProgressColumn(
                            label="🏁 Fulfillment Progress",
                            help="Visual breakdown percentage of production completed vs distributor request",
                            format="%.1f%%",
                            min_value=0,
                            max_value=100,
                            width="large"
                        )
                    }
                    
                    # Render the interactive clean dashboard dataset matrix table
                    st.dataframe(
                        data=df_analysis,
                        column_config=ui_config,
                        hide_index=True,           # Removes the raw 0,1,2 left side row index numbering
                        use_container_width=True   # Forces the table to expand seamlessly to full grid width
                    )
