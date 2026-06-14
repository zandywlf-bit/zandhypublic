"""Generate sample Excel test data for the Production Dashboard"""
import pandas as pd
import os

# Create test_data directory if not exists
os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)

# ============================================================
# Sample Distributor PO Data
# ============================================================
po_data = {
    'Date of Request': [
        '2026-06-01', '2026-06-01', '2026-06-02', '2026-06-03',
        '2026-06-04', '2026-06-05', '2026-06-06', '2026-06-07',
        '2026-06-08', '2026-06-09', '2026-06-10', '2026-06-11'
    ],
    'Type of Season': [
        'Summer', 'Summer', 'Summer', 'Summer',
        'Summer', 'Summer', 'Summer', 'Summer',
        'Summer', 'Summer', 'Summer', 'Summer'
    ],
    'Product Name': [
        'T-Shirt Basic', 'Denim Jeans', 'Leather Belt', 'Tropical Shirt',
        'Cotton Socks Pack', 'Running Shoes', 'Woolen Hat', 'Leather Wallet',
        'Silk Scarf', 'Cotton T-Shirt', 'Canvas Bag', 'Denim Jacket'
    ],
    'Quantity of Product': [
        1000, 500, 300, 800,
        2000, 400, 600, 350,
        150, 1200, 450, 250
    ]
}

po_df = pd.DataFrame(po_data)
po_path = os.path.join(os.path.dirname(__file__), 'po_sample.xlsx')
po_df.to_excel(po_path, index=False)
print(f"✅ Created PO sample data: {po_path}")
print(f"   Rows: {len(po_df)}")

# ============================================================
# Sample Factory Production Data
# ============================================================
production_data = {
    'Date of Report': [
        '2026-06-05', '2026-06-06', '2026-06-07', '2026-06-08',
        '2026-06-09', '2026-06-10', '2026-06-11', '2026-06-12',
        '2026-06-13', '2026-06-14', '2026-06-15', '2026-06-16'
    ],
    'Product Name': [
        'T-Shirt Basic', 'Denim Jeans', 'Leather Belt', 'Tropical Shirt',
        'Cotton Socks Pack', 'Running Shoes', 'Woolen Hat', 'Leather Wallet',
        'Silk Scarf', 'Cotton T-Shirt', 'Canvas Bag', 'Denim Jacket'
    ],
    'Amount of Product Created': [
        750, 500, 100, 800,
        1500, 350, 600, 250,
        150, 1200, 300, 200
    ]
}

prod_df = pd.DataFrame(production_data)
prod_path = os.path.join(os.path.dirname(__file__), 'production_sample.xlsx')
prod_df.to_excel(prod_path, index=False)
print(f"✅ Created Production sample data: {prod_path}")
print(f"   Rows: {len(prod_df)}")

print("\n📊 Expected Comparison Output:")
print("-" * 80)
print(f"{'Product Name':<20} {'Requested':<10} {'Produced':<10} {'%':<8} {'Status':<10}")
print("-" * 80)

# Show the comparison
merged = pd.merge(po_df.groupby('Product Name')['Quantity of Product'].sum().reset_index(),
                  prod_df.groupby('Product Name')['Amount of Product Created'].sum().reset_index(),
                  on='Product Name', how='outer').fillna(0)
merged.columns = ['Product Name', 'Requested Qty', 'Produced Qty']
merged['Completion %'] = (merged['Produced Qty'] / merged['Requested Qty'].replace(0, 1)) * 100

for _, row in merged.iterrows():
    status = 'Complete' if row['Completion %'] >= 100 else 'Partial' if row['Completion %'] > 0 else 'Missing'
    print(f"{row['Product Name']:<20} {int(row['Requested Qty']):<10} {int(row['Produced Qty']):<10} {row['Completion %']:<7.1f}% {status:<10}")

print("-" * 80)
print("\n✅ Sample data generation complete!")