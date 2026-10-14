import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. KONFIGURASI HALAMAN & TEMA WARNA BIRU COOLER CITY
st.set_page_config(
    page_title="Cooler City Executive Sales Dashboard",
    page_icon="🥤",
    layout="wide"
)

# Styling CSS Custom agar menyerupai Dashboard Eksekutif Profesional
st.markdown("""
    <style>
    .main {
        background-color: #F4F8FC;
    }
    .stMetric {
        background-color: #FFFFFF;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #0056b3;
    }
    h1, h2, h3 {
        color: #0b3c5d;
    }
    .header-title {
        background-color: #0b3c5d;
        color: white;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# Judul Utama Dashboard
st.markdown('<div class="header-title"><h1>COOLER CITY SALES & TRANSACTION EXECUTIVE DASHBOARD</h1></div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1. EXTRACT & SIDEBAR FILTER
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 Panel Kontrol & Filter")
uploaded_file = st.sidebar.file_uploader("Unggah Dataset POS (Excel / CSV)", type=["xlsx", "csv"])

if uploaded_file is not None:
    if uploaded_file.name.endswith('.xlsx'):
        df_raw = pd.read_excel(uploaded_file, sheet_name=0)
    else:
        df_raw = pd.read_csv(uploaded_file)
        
    df = df_raw.copy()
    df.columns = df.columns.str.strip().str.lower()
    df = df.drop_duplicates()
    
    # Standarisasi Kolom Tanggal
    date_col = next((c for c in df.columns if 'date' in c or 'tanggal' in c), df.columns[1])
    df['full_date'] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=['full_date'])
    
    # Filter Sidebar Berdasarkan Tanggal
    min_date = df['full_date'].min().date()
    max_date = df['full_date'].max().date()
    
    st.sidebar.subheader("Rentang Periode")
    start_date = st.sidebar.date_input("Dari Tanggal", min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("Sampai Tanggal", max_date, min_value=min_date, max_value=max_date)
    
    df_filtered = df[(df['full_date'].dt.date >= start_date) & (df['full_date'].dt.date <= end_date)]

    # Pemetaan Nama Kolom Dinamis
    col_subtotal = next((c for c in df.columns if 'subtotal' in c or 'total' in c or 'price' in c), df.columns[-1])
    col_qty = next((c for c in df.columns if 'qty' in c or 'quantity' in c or 'jumlah' in c), 'quantity')
    col_order = next((c for c in df.columns if 'order' in c or 'nota' in c or 'trx' in c), df.columns[0])
    col_cat = next((c for c in df.columns if 'cat' in c or 'kategori' in c), None)
    col_prod = next((c for c in df.columns if 'product_name' in c or 'menu' in c or 'product' in c), None)

    # Filter Kategori di Sidebar
    if col_cat and col_cat in df_filtered.columns:
        categories = ['All'] + list(df_filtered[col_cat].dropna().unique())
        selected_cat = st.sidebar.selectbox("Category Name", categories)
        if selected_cat != 'All':
            df_filtered = df_filtered[df_filtered[col_cat] == selected_cat]

    # Filter Produk di Sidebar
    if col_prod and col_prod in df_filtered.columns:
        products = ['All'] + list(df_filtered[col_prod].dropna().unique())
        selected_prod = st.sidebar.selectbox("Product Name", products)
        if selected_prod != 'All':
            df_filtered = df_filtered[df_filtered[col_prod] == selected_prod]

    # -----------------------------------------------------------------------------
    # 2. EXECUTIVE METRICS (KPI CARDS)
    # -----------------------------------------------------------------------------
    total_revenue = pd.to_numeric(df_filtered[col_subtotal], errors='coerce').sum()
    total_qty_sold = pd.to_numeric(df_filtered[col_qty], errors='coerce').sum()
    total_trx = df_filtered[col_order].nunique()
    
    avg_order_value = total_revenue / total_trx if total_trx > 0 else 0
    avg_product_per_order = total_qty_sold / total_trx if total_trx > 0 else 0

    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Total Penjualan (Revenue)", f"Rp {total_revenue:,.0f}")
    col_kpi2.metric("Avg Product Per Order", f"{avg_product_per_order:.2f} Unit")
    col_kpi3.metric("Avg Order Value (AOV)", f"Rp {avg_order_value:,.0f}")

    st.markdown("---")

    # -----------------------------------------------------------------------------
    # 3. BARIS GRAFIK: Daily Trend & Top 5 Best-Selling Products
    # -----------------------------------------------------------------------------
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Daily Trend for Total Sales")
        df_filtered['day_name'] = df_filtered['full_date'].dt.day_name()
        daily_trend = df_filtered.groupby('day_name')[col_subtotal].sum().reset_index()
        fig_daily = px.bar(daily_trend, x='day_name', y=col_subtotal, color_discrete_sequence=['#0056b3'])
        fig_daily.update_layout(margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(fig_daily, use_container_width=True)

    with c2:
        st.subheader("Top 5 Best-Selling Product")
        if col_prod and col_prod in df_filtered.columns:
            top_5 = df_filtered.groupby(col_prod)[col_qty].sum().reset_index().sort_values(by=col_qty, ascending=False).head(5)
            fig_top5 = px.bar(top_5, x=col_qty, y=col_prod, orientation='h', color_discrete_sequence=['#0b3c5d'])
            fig_top5.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=10, b=10))
            st.plotly_chart(fig_top5, use_container_width=True)

    # -----------------------------------------------------------------------------
    # 4. BARIS GRAFIK: Total Sales by Month & Total Product Sold by Product
    # -----------------------------------------------------------------------------
    c3, c4 = st.columns(2)

    with c3:
        st.subheader("Total Sales by Month")
        df_filtered['month_year'] = df_filtered['full_date'].dt.to_period('M').astype(str)
        monthly_rev = df_filtered.groupby('month_year')[col_subtotal].sum().reset_index()
        fig_month = px.bar(monthly_rev, x='month_year', y=col_subtotal, color_discrete_sequence=['#1d63b8'])
        fig_month.update_layout(margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(fig_month, use_container_width=True)

    with c4:
        st.subheader("Total Product Sold by Product")
        if col_prod and col_prod in df_filtered.columns:
            all_prod_sold = df_filtered.groupby(col_prod)[col_qty].sum().reset_index().sort_values(by=col_qty, ascending=False)
            fig_all_prod = px.bar(all_prod_sold, x=col_qty, y=col_prod, orientation='h', color_discrete_sequence=['#2a75d3'])
            fig_all_prod.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=10, b=10))
            st.plotly_chart(fig_all_prod, use_container_width=True)

    # -----------------------------------------------------------------------------
    # 5. BARIS GRAFIK: % of Sales by Product & % of Sales by Category (Donut Charts)
    # -----------------------------------------------------------------------------
    c5, c6 = st.columns(2)

    with c5:
        st.subheader("% of Sales by Product")
        if col_prod and col_prod in df_filtered.columns:
            prod_sales = df_filtered.groupby(col_prod)[col_subtotal].sum().reset_index()
            fig_pie_prod = px.pie(prod_sales, names=col_prod, values=col_subtotal, hole=0.4, color_discrete_sequence=px.colors.sequential.Blues_r)
            fig_pie_prod.update_layout(margin=dict(l=0, r=0, t=10, b=10))
            st.plotly_chart(fig_pie_prod, use_container_width=True)

    with c6:
        st.subheader("% of Sales by Category")
        if col_cat and col_cat in df_filtered.columns:
            cat_sales = df_filtered.groupby(col_cat)[col_subtotal].sum().reset_index()
            fig_pie_cat = px.pie(cat_sales, names=col_cat, values=col_subtotal, hole=0.4, color_discrete_sequence=px.colors.sequential.Tealgrn)
            fig_pie_cat.update_layout(margin=dict(l=0, r=0, t=10, b=10))
            st.plotly_chart(fig_pie_cat, use_container_width=True)

    # -----------------------------------------------------------------------------
    # 6. ANALISIS LANJUTAN: Scatter Plot (Qty vs Sales) & Regresi Linear
    # -----------------------------------------------------------------------------
    st.markdown("---")
    c7, c8 = st.columns(2)

    with c7:
        st.subheader("Total Sales and Total Product Correlation")
        if col_prod and col_prod in df_filtered.columns:
            corr_df = df_filtered.groupby(col_prod).agg({col_qty: 'sum', col_subtotal: 'sum'}).reset_index()
            fig_scatter = px.scatter(corr_df, x=col_subtotal, y=col_qty, text=col_prod, title="Korelasi Omzet vs Kuantitas Produk", color_discrete_sequence=['#0056b3'])
            st.plotly_chart(fig_scatter, use_container_width=True)

    with c8:
        st.subheader("📈 Analisis Prediktif Tren Penjualan (Regresi Linear)")
        if len(monthly_rev) >= 2:
            monthly_rev['X'] = np.arange(1, len(monthly_rev) + 1)
            X = monthly_rev['X']
            Y = monthly_rev[col_subtotal]
            
            b, a = np.polyfit(X, Y, 1)
            monthly_rev['Linear_Trend'] = a + b * X
            
            fig_reg = px.line(
                monthly_rev, 
                x='month_year', 
                y=[col_subtotal, 'Linear_Trend'],
                labels={'value': 'Nominal (Rp)', 'month_year': 'Bulan'},
                title="Aktual vs Garis Tren Regresi Linear",
                color_discrete_map={col_subtotal: '#0056b3', 'Linear_Trend': '#ff7f0e'}
            )
            st.plotly_chart(fig_reg, use_container_width=True)
            st.success(f"Persamaan Tren: **Y = {a:,.0f} + {b:,.0f}X**")

else:
    st.info("👈 Silakan unggah file Excel/CSV data POS Cooler City melalui panel sidebar di sebelah kiri untuk memuat seluruh komponen dashboard.")
    