import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. KONFIGURASI HALAMAN & TEMA WARNA BIRU KORPORAT COOLER CITY
st.set_page_config(
    page_title="Cooler City Executive Sales Dashboard",
    page_icon="🥤",
    layout="wide"
)

st.markdown("""
    <style>
    .main {
        background-color: #F4F8FC;
    }
    .stMetric {
        background-color: #FFFFFF;
        padding: 15px;
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
        padding: 18px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-title"><h1>COOLER CITY SALES & TRANSACTION EXECUTIVE DASHBOARD</h1></div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. LOAD DATA & SIDEBAR FILTER
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 Panel Kontrol & Filter")
uploaded_file = st.sidebar.file_uploader("Unggah Dataset POS (Excel)", type=["xlsx", "csv"])

if uploaded_file is not None:
    # Membaca sheet 'Master Data' atau sheet pertama dari file Excel
    try:
        df_raw = pd.read_excel(uploaded_file, sheet_name='Master Data')
    except:
        df_raw = pd.read_excel(uploaded_file, sheet_name=0)
        
    df = df_raw.copy()
    df.columns = df.columns.str.strip().str.lower()
    df = df.drop_duplicates()
    
    # Konversi Tanggal
    df['full_date'] = pd.to_datetime(df['full_date'], errors='coerce')
    df = df.dropna(subset=['full_date'])
    
    # Sidebar: Rentang Tanggal
    min_date = df['full_date'].min().date()
    max_date = df['full_date'].max().date()
    
    st.sidebar.subheader("Rentang Periode Tanggal")
    start_date = st.sidebar.date_input("Dari Tanggal", min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("Sampai Tanggal", max_date, min_value=min_date, max_value=max_date)
    
    df_filtered = df[(df['full_date'].dt.date >= start_date) & (df['full_date'].dt.date <= end_date)]

    # Sidebar: Filter Kategori Produk
    if 'category_name' in df_filtered.columns:
        categories = ['All'] + list(df_filtered['category_name'].dropna().unique())
        selected_cat = st.sidebar.selectbox("Category Name", categories)
        if selected_cat != 'All':
            df_filtered = df_filtered[df_filtered['category_name'] == selected_cat]

    # Sidebar: Filter Nama Produk
    if 'product_name' in df_filtered.columns:
        products = ['All'] + list(df_filtered['product_name'].dropna().unique())
        selected_prod = st.sidebar.selectbox("Product Name", products)
        if selected_prod != 'All':
            df_filtered = df_filtered[df_filtered['product_name'] == selected_prod]

    # -----------------------------------------------------------------------------
    # 3. EXECUTIVE KPI METRICS (Kotak Atas)
    # -----------------------------------------------------------------------------
    total_revenue = pd.to_numeric(df_filtered['subtotal'], errors='coerce').sum()
    total_qty_sold = pd.to_numeric(df_filtered['quantity'], errors='coerce').sum()
    total_trx = df_filtered['order_no'].nunique()
    
    avg_order_value = total_revenue / total_trx if total_trx > 0 else 0
    avg_product_per_order = total_qty_sold / total_trx if total_trx > 0 else 0

    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Total Penjualan (Revenue)", f"Rp {total_revenue:,.0f}")
    col_kpi2.metric("Avg Product Per Order", f"{avg_product_per_order:.2f} Unit")
    col_kpi3.metric("Avg Order Value (AOV)", f"Rp {avg_order_value:,.0f}")

    st.markdown("---")

    # -----------------------------------------------------------------------------
    # 4. BARIS 1: Daily Trend & Top 5 Best-Selling Products
    # -----------------------------------------------------------------------------
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Daily Trend for Total Sales")
        # Urutan hari dari Minggu ke Sabtu
        day_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        daily_trend = df_filtered.groupby('day_name')['subtotal'].sum().reindex(day_order).reset_index()
        fig_daily = px.bar(daily_trend, x='day_name', y='subtotal', labels={'day_name': 'Hari', 'subtotal': 'Total Omzet (Rp)'}, color_discrete_sequence=['#0056b3'])
        fig_daily.update_layout(margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(fig_daily, use_container_width=True)

    with c2:
        st.subheader("Top 5 Best-Selling Product")
        top_5 = df_filtered.groupby('product_name')['quantity'].sum().reset_index().sort_values(by='quantity', ascending=False).head(5)
        fig_top5 = px.bar(top_5, x='quantity', y='product_name', orientation='h', labels={'quantity': 'Total Qty', 'product_name': 'Produk'}, color_discrete_sequence=['#0b3c5d'])
        fig_top5.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(fig_top5, use_container_width=True)

    # -----------------------------------------------------------------------------
    # 5. BARIS 2: Total Sales by Month & Total Product Sold by Product (All)
    # -----------------------------------------------------------------------------
    c3, c4 = st.columns(2)

    with c3:
        st.subheader("Total Sales by Month")
        df_filtered['month_year'] = df_filtered['full_date'].dt.to_period('M').astype(str)
        monthly_rev = df_filtered.groupby('month_year')['subtotal'].sum().reset_index()
        fig_month = px.bar(monthly_rev, x='month_year', y='subtotal', labels={'month_year': 'Bulan', 'subtotal': 'Omzet (Rp)'}, color_discrete_sequence=['#1d63b8'])
        fig_month.update_layout(margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(fig_month, use_container_width=True)

    with c4:
        st.subheader("Total Product Sold by Product")
        all_prod_sold = df_filtered.groupby('product_name')['quantity'].sum().reset_index().sort_values(by='quantity', ascending=False)
        fig_all_prod = px.bar(all_prod_sold, x='quantity', y='product_name', orientation='h', labels={'quantity': 'Total Qty', 'product_name': 'Produk'}, color_discrete_sequence=['#2a75d3'])
        fig_all_prod.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(fig_all_prod, use_container_width=True)

    # -----------------------------------------------------------------------------
    # 6. BARIS 3: % of Sales by Product & % of Sales by Category (Donut Charts)
    # -----------------------------------------------------------------------------
    c5, c6 = st.columns(2)

    with c5:
        st.subheader("% of Sales by Product")
        prod_sales = df_filtered.groupby('product_name')['subtotal'].sum().reset_index()
        fig_pie_prod = px.pie(prod_sales, names='product_name', values='subtotal', hole=0.4, color_discrete_sequence=px.colors.sequential.Blues_r)
        fig_pie_prod.update_layout(margin=dict(l=0, r=0, t=10, b=10), showlegend=False)
        st.plotly_chart(fig_pie_prod, use_container_width=True)

    with c6:
        st.subheader("% of Sales by Category")
        cat_sales = df_filtered.groupby('category_name')['subtotal'].sum().reset_index()
        fig_pie_cat = px.pie(cat_sales, names='category_name', values='subtotal', hole=0.4, color_discrete_sequence=px.colors.sequential.Tealgrn)
        fig_pie_cat.update_layout(margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(fig_pie_cat, use_container_width=True)

    # -----------------------------------------------------------------------------
    # 7. BARIS 4: Analisis Korelasi & Analisis Prediktif (Regresi Linear)
    # -----------------------------------------------------------------------------
    st.markdown("---")
    c7, c8 = st.columns(2)

    with c7:
        st.subheader("Total Sales vs Total Product Correlation")
        corr_df = df_filtered.groupby('product_name').agg({'quantity': 'sum', 'subtotal': 'sum'}).reset_index()
        fig_scatter = px.scatter(corr_df, x='subtotal', y='quantity', text='product_name', labels={'subtotal': 'Total Omzet (Rp)', 'quantity': 'Total Kuantitas'}, color_discrete_sequence=['#0056b3'])
        fig_scatter.update_layout(margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(fig_scatter, use_container_width=True)

    with c8:
        st.subheader("📈 Analisis Prediktif Tren Penjualan (Regresi Linear)")
        if len(monthly_rev) >= 2:
            monthly_rev['X'] = np.arange(1, len(monthly_rev) + 1)
            X = monthly_rev['X']
            Y = monthly_rev['subtotal']
            
            b, a = np.polyfit(X, Y, 1)
            monthly_rev['Linear_Trend'] = a + b * X
            
            fig_reg = px.line(
                monthly_rev, 
                x='month_year', 
                y=['subtotal', 'Linear_Trend'],
                labels={'value': 'Nominal (Rp)', 'month_year': 'Bulan'},
                title="Aktual vs Garis Tren Regresi Linear",
                color_discrete_map={'subtotal': '#0056b3', 'Linear_Trend': '#ff7f0e'}
            )
            fig_reg.update_layout(margin=dict(l=0, r=0, t=10, b=10))
            st.plotly_chart(fig_reg, use_container_width=True)
            st.success(f"Persamaan Garis Tren: **Y = {a:,.0f} + {b:,.0f}X**")

else:
    st.info("👈 Silakan unggah file Excel `Data_CoolerCity_v3_Dirty.xlsx` melalui panel sidebar di sebelah kiri untuk menampilkan seluruh komponen dashboard.")