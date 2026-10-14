import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. KONFIGURASI HALAMAN & TEMA WARNA BIRU COOLER CITY
st.set_page_config(
    page_title="Cooler City BI & Analytics System",
    page_icon="🥤",
    layout="wide"
)

# Styling CSS Custom Tema Biru Cooler City
st.markdown("""
    <style>
    .main {
        background-color: #F4F8FC;
    }
    .stMetric {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #0056b3;
    }
    h1, h2, h3 {
        color: #0b3c5d;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🥤 Cooler City Business Intelligence Dashboard")
st.markdown("Sistem Integrasi ETL, Pemodelan Star Schema, dan Analisis Prediktif (Regresi Linear).")

# -----------------------------------------------------------------------------
# LANGKAH 1: EXTRACT (UPLOAD DATASET POS MENTAH)
# -----------------------------------------------------------------------------
st.sidebar.header("📁 1. Extract Data")
uploaded_file = st.sidebar.file_uploader("Unggah dataset POS (Excel / CSV)", type=["xlsx", "csv"])

if uploaded_file is not None:
    if uploaded_file.name.endswith('.xlsx'):
        df_raw = pd.read_excel(uploaded_file, sheet_name=0)
    else:
        df_raw = pd.read_csv(uploaded_file)
        
    st.sidebar.success("Data berhasil diekstrak!")

    # -----------------------------------------------------------------------------
    # LANGKAH 2: TRANSFORM (ETL & DATA CLEANSING OTOMATIS)
    # -----------------------------------------------------------------------------
    with st.spinner("Menjalankan proses ETL (Cleaning & Transformation)..."):
        df = df_raw.copy()
        
        # A. Deduplication (Hapus baris duplikat)
        df = df.drop_duplicates()
        
        # B. Missing Value Imputation
        if 'customer_name' in df.columns:
            df['customer_name'] = df['customer_name'].fillna('Guest/Unregistered')
        if 'payment_method' in df.columns:
            df['payment_method'] = df['payment_method'].fillna('Unknown Payment')
            
        # C. Standardisasi Tanggal & Waktu
        if 'full_date' in df.columns:
            df['full_date'] = pd.to_datetime(df['full_date'])
            df['year'] = df['full_date'].dt.year
            df['month_name'] = df['full_date'].dt.month_name()

    st.info(f"Proses ETL Selesai! Baris data bersih tersisa: **{len(df):,} baris**.")

    # -----------------------------------------------------------------------------
    # LANGKAH 3: LOAD & STAR SCHEMA MODELING
    # -----------------------------------------------------------------------------
    fact_transaction = df[['order_no', 'date_key', 'product_id', 'customer_key', 'payment_id', 'quantity', 'subtotal']].copy()
    dim_product = df[['product_id', 'product_name', 'category_name', 'unit_price']].drop_duplicates()
    dim_customer = df[['customer_key', 'customer_name', 'customer_type']].drop_duplicates()
    dim_payment = df[['payment_id', 'payment_method']].drop_duplicates()
    dim_date = df[['date_key', 'full_date', 'year', 'month_name']].drop_duplicates()

    # -----------------------------------------------------------------------------
    # LANGKAH 4: DASHBOARD & KPI METRICS
    # -----------------------------------------------------------------------------
    st.markdown("---")
    st.header("📊 Executive Summary & KPI Operasional")
    
    total_revenue = fact_transaction['subtotal'].sum()
    total_qty = fact_transaction['quantity'].sum()
    total_transactions = fact_transaction['order_no'].nunique()
    aov = total_revenue / total_transactions if total_transactions > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sales Revenue", f"Rp {total_revenue:,.0f}")
    c2.metric("Total Quantity Sold", f"{total_qty:,} Unit")
    c3.metric("Average Basket Size (AOV)", f"Rp {aov:,.0f}")
    c4.metric("Total Transactions", f"{total_transactions:,} Struk")

    st.markdown("---")

    col_1, col_2 = st.columns(2)
    
    with col_1:
        st.subheader("Kontribusi Pendapatan per Kategori")
        if 'category_name' in dim_product.columns:
            merged_cat = fact_transaction.merge(dim_product, on='product_id', how='left')
            cat_share = merged_cat.groupby('category_name')['subtotal'].sum().reset_index()
            fig_cat = px.bar(cat_share, x='category_name', y['subtotal'] if 'subtotal' in cat_share.columns else 'subtotal', 
                             title="Omzet Berdasarkan Kategori Produk",
                             color_discrete_sequence=['#0056b3'])
            st.plotly_chart(fig_cat, use_container_width=True)

    with col_2:
        st.subheader("Distribusi Metode Pembayaran")
        if 'payment_method' in dim_payment.columns:
            merged_pay = fact_transaction.merge(dim_payment, on='payment_id', how='left')
            pay_dist = merged_pay.groupby('payment_method')['order_no'].count().reset_index()
            fig_pay = px.pie(pay_dist, names='payment_method', values='order_no', 
                             title="Proporsi Kanal Pembayaran Konsumen",
                             color_discrete_sequence=px.colors.sequential.Blues_r)
            st.plotly_chart(fig_pay, use_container_width=True)

    # -----------------------------------------------------------------------------
    # LANGKAH 5: ANALISIS PREDIKTIF (REGRESI LINEAR)
    # -----------------------------------------------------------------------------
    st.markdown("---")
    st.header("📈 Analisis Prediktif: Regresi Linear (Linear Trend Analysis)")
    
    df['month_period'] = df['full_date'].dt.to_period('M').astype(str)
    monthly_sales = df.groupby('month_period')['subtotal'].sum().reset_index()
    
    if len(monthly_sales) >= 2:
        monthly_sales['X'] = np.arange(1, len(monthly_sales) + 1)
        X = monthly_sales['X']
        Y = monthly_sales['subtotal']
        
        # Hitung Regresi Linear (Y = a + bX)
        b, a = np.polyfit(X, Y, 1)
        monthly_sales['Linear_Trend'] = a + b * X
        
        fig_reg = px.line(monthly_sales, x='month_period', y=['subtotal', 'Linear_Trend'],
                           labels={'value': 'Nominal (Rp)', 'month_period': 'Bulan'},
                           title="Kurva Tren Penjualan Aktual vs Regresi Linear",
                           color_discrete_map={'subtotal': '#0056b3', 'Linear_Trend': '#ff7f0e'})
        st.plotly_chart(fig_reg, use_container_width=True)
        
        st.success(f"Persamaan Garis Tren: **Y = {a:,.0f} + {b:,.0f}X** (Rata-rata pertumbuhan omzet Rp {b:,.0f} per bulan).")
    else:
        st.warning("Data bulanan tidak mencukupi untuk menjalankan analisis regresi.")

else:
    st.info("👈 Silakan unggah file Excel/CSV data POS Cooler City melalui panel sidebar di sebelah kiri untuk memulai sistem.")