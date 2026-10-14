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
        
        # Normalisasi nama kolom (menghilangkan spasi dan mengubah ke huruf kecil agar aman)
        df.columns = df.columns.str.strip().str.lower()
        
        # A. Deduplication (Hapus baris duplikat)
        df = df.drop_duplicates()
        
        # B. Missing Value Imputation
        if 'customer_name' in df.columns:
            df['customer_name'] = df['customer_name'].fillna('Guest/Unregistered')
        if 'payment_method' in df.columns:
            df['payment_method'] = df['payment_method'].fillna('Unknown Payment')
            
        # C. Standardisasi Tanggal & Waktu
        date_col = 'full_date' if 'full_date' in df.columns else ('date' if 'date' in df.columns else df.columns[1])
        df['full_date'] = pd.to_datetime(df[date_col], errors='coerce')
        df['year'] = df['full_date'].dt.year
        df['month_name'] = df['full_date'].dt.month_name()

    st.info(f"Proses ETL Selesai! Baris data bersih tersisa: **{len(df):,} baris**.")

    # Deteksi nama kolom finansial secara otomatis
    col_subtotal = next((c for c in df.columns if 'subtotal' in c or 'total' in c or 'price' in c), df.columns[-1])
    col_qty = next((c for c in df.columns if 'qty' in c or 'quantity' in c or 'jumlah' in c), 'quantity' if 'quantity' in df.columns else df.columns[-2])
    col_order = next((c for c in df.columns if 'order' in c or 'nota' in c or 'trx' in c), df.columns[0])
    col_cat = next((c for c in df.columns if 'cat' in c or 'kategori' in c or 'product_name' in c), None)
    col_pay = next((c for c in df.columns if 'pay' in c or 'metode' in c), None)

    # -----------------------------------------------------------------------------
    # LANGKAH 3: LOAD & STAR SCHEMA MODELING
    # -----------------------------------------------------------------------------
    fact_transaction = pd.DataFrame({
        'order_no': df[col_order],
        'quantity': pd.to_numeric(df[col_qty], errors='coerce').fillna(1),
        'subtotal': pd.to_numeric(df[col_subtotal], errors='coerce').fillna(0)
    })
    
    if col_cat and col_cat in df.columns:
        fact_transaction['category_name'] = df[col_cat]
    else:
        fact_transaction['category_name'] = 'General Product'
        
    if col_pay and col_pay in df.columns:
        fact_transaction['payment_method'] = df[col_pay]
    else:
        fact_transaction['payment_method'] = 'CASH'

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
    c2.metric("Total Quantity Sold", f"{total_qty:,.0f} Unit")
    c3.metric("Average Basket Size (AOV)", f"Rp {aov:,.0f}")
    c4.metric("Total Transactions", f"{total_transactions:,} Struk")

    st.markdown("---")

    col_1, col_2 = st.columns(2)
    
    with col_1:
        st.subheader("Kontribusi Pendapatan per Kategori")
        cat_share = fact_transaction.groupby('category_name')['subtotal'].sum().reset_index()
        fig_cat = px.bar(
            cat_share, 
            x='category_name', 
            y='subtotal', 
            title="Omzet Berdasarkan Kategori Produk",
            color_discrete_sequence=['#0056b3']
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_2:
        st.subheader("Distribusi Metode Pembayaran")
        pay_dist = fact_transaction.groupby('payment_method')['order_no'].count().reset_index()
        fig_pay = px.pie(
            pay_dist, 
            names='payment_method', 
            values='order_no', 
            title="Proporsi Kanal Pembayaran Konsumen",
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        st.plotly_chart(fig_pay, use_container_width=True)

    # -----------------------------------------------------------------------------
    # LANGKAH 5: ANALISIS PREDIKTIF (REGRESI LINEAR)
    # -----------------------------------------------------------------------------
    st.markdown("---")
    st.header("📈 Analisis Prediktif: Regresi Linear (Linear Trend Analysis)")
    
    df['month_period'] = df['full_date'].dt.to_period('M').astype(str)
    monthly_sales = df.groupby('month_period')[col_subtotal].sum().reset_index()
    monthly_sales.columns = ['month_period', 'subtotal']
    
    if len(monthly_sales.dropna()) >= 2:
        monthly_sales = monthly_sales.dropna()
        monthly_sales['X'] = np.arange(1, len(monthly_sales) + 1)
        X = monthly_sales['X']
        Y = monthly_sales['subtotal']
        
        # Hitung Regresi Linear (Y = a + bX)
        b, a = np.polyfit(X, Y, 1)
        monthly_sales['Linear_Trend'] = a + b * X
        
        fig_reg = px.line(
            monthly_sales, 
            x='month_period', 
            y=['subtotal', 'Linear_Trend'],
            labels={'value': 'Nominal (Rp)', 'month_period': 'Bulan'},
            title="Kurva Tren Penjualan Aktual vs Regresi Linear",
            color_discrete_map={'subtotal': '#0056b3', 'Linear_Trend': '#ff7f0e'}
        )
        st.plotly_chart(fig_reg, use_container_width=True)
        
        st.success(f"Persamaan Garis Tren: **Y = {a:,.0f} + {b:,.0f}X** (Rata-rata pertumbuhan omzet Rp {b:,.0f} per bulan).")
    else:
        st.warning("Data bulanan tidak mencukupi untuk menjalankan analisis regresi.")

else:
    st.info("👈 Silakan unggah file Excel/CSV data POS Cooler City melalui panel sidebar di sebelah kiri untuk memulai sistem.")