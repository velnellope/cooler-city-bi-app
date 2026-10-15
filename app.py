import streamlit as st
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
import matplotlib.pyplot as plt
import seaborn as sns

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Cooler City BI & Power BI Dashboard",
    page_icon="🧊",
    layout="wide"
)

# Styling Warna Biru Khas Cooler City
st.markdown("""
    <style>
        .main-header {
            font-size: 32px;
            font-weight: 800;
            color: #1e3a8a;
        }
        .sub-header {
            font-size: 18px;
            color: #475569;
        }
        .card-box {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# 1. Load Data
@st.cache_data
def load_data():
    file_path = "Data_CoolerCity_Apriori_Ready_v2.xlsx"
    df = pd.read_excel(file_path, sheet_name="Master Data")
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Gagal memuat file Excel: {e}. Pastikan file 'Data_CoolerCity_Apriori_Ready_v2.xlsx' sudah di-upload ke repository GitHub.")
    st.stop()

# Header Utama Aplikasi
st.markdown("<p class='main-header'>🧊 Cooler City Business Intelligence & Power BI Dashboard</p>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Analisis Penjualan Multi-Tahun & Rekomendasi Product Bundling berbasis Algoritma Apriori</p>", unsafe_allow_html=True)
st.markdown("---")

# Global Sidebar Slicer
st.sidebar.header("⚙️ Global Slicer & Filter")

# Slicer Tahun & Bulan
years = ["All"] + sorted([str(y) for y in df['year'].dropna().unique()]) if 'year' in df.columns else ["All"]
selected_year = st.sidebar.selectbox("Pilih Tahun", years)

months = ["All"] + list(df['month_name'].dropna().unique()) if 'month_name' in df.columns else ["All"]
selected_month = st.sidebar.selectbox("Pilih Bulan", months)

categories = ["All"] + list(df['category_name'].dropna().unique()) if 'category_name' in df.columns else ["All"]
selected_category = st.sidebar.selectbox("Pilih Kategori Produk", categories)

# Terapkan Filter Global
df_filtered = df.copy()
if selected_year != "All":
    df_filtered = df_filtered[df_filtered['year'].astype(str) == selected_year]
if selected_month != "All":
    df_filtered = df_filtered[df_filtered['month_name'] == selected_month]
if selected_category != "All":
    df_filtered = df_filtered[df_filtered['category_name'] == selected_category]

# Navigasi 3 Halaman Utama (Power BI Style Tabs)
page1, page2, page3 = st.tabs([
    "📊 Halaman 1 — Sales Overview", 
    "🔗 Halaman 2 — Apriori Association", 
    "💡 Halaman 3 — Product Bundling Insights"
])

# ==========================================
# HALAMAN 1: SALES OVERVIEW
# ==========================================
with page1:
    st.subheader("Halaman 1 — Sales Overview & Performa Makro")
    st.markdown("Memahami kondisi performa penjualan sebelum menganalisis pola asosiasi produk.")
    
    # KPI Cards ala Power BI
    col1, col2, col3, col4 = st.columns(4)
    
    total_revenue = df_filtered['subtotal'].sum() if 'subtotal' in df_filtered.columns else 0
    total_transactions = df_filtered['order_no'].nunique() if 'order_no' in df_filtered.columns else 0
    total_products_sold = df_filtered['quantity'].sum() if 'quantity' in df_filtered.columns else 0
    total_categories = df_filtered['category_name'].nunique() if 'category_name' in df_filtered.columns else 0
    
    col1.metric("Total Revenue", f"Rp {total_revenue:,.0f}")
    col2.metric("Total Transaksi", f"{total_transactions:,}")
    col3.metric("Total Produk Terjual", f"{total_products_sold:,}")
    col4.metric("Jumlah Kategori", f"{total_categories}")
    
    st.markdown("---")
    
    # Visualisasi Halaman 1
    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        st.markdown("##### 📈 Line Chart: Tren Penjualan Bulanan")
        if 'month_name' in df_filtered.columns and 'subtotal' in df_filtered.columns:
            trend_data = df_filtered.groupby('month_name')['subtotal'].sum().reset_index()
            fig, ax = plt.subplots(figsize=(8, 4))
            sns.lineplot(x='month_name', y='subtotal', data=trend_data, marker='o', color='#2563eb', linewidth=2.5, ax=ax)
            ax.set_title("Pendapatan per Bulan", fontsize=12, fontweight='bold')
            ax.set_xlabel("Bulan")
            ax.set_ylabel("Total Pendapatan (Rp)")
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.info("Kolom bulan atau subtotal tidak ditemukan.")
            
    with col_v2:
        st.markdown("##### 📊 Bar Chart: Produk Terlaris (Top 10)")
        if 'product_name' in df_filtered.columns and 'quantity' in df_filtered.columns:
            top_prod = df_filtered.groupby('product_name')['quantity'].sum().reset_index().sort_values(by='quantity', ascending=False).head(10)
            fig, ax = plt.subplots(figsize=(8, 4))
            sns.barplot(x='quantity', y='product_name', data=top_prod, palette='Blues_r', ax=ax)
            ax.set_title("Kuantitas Penjualan Tertinggi", fontsize=12, fontweight='bold')
            ax.set_xlabel("Total Kuantitas")
            ax.set_ylabel("Nama Produk")
            st.pyplot(fig)
        else:
            st.info("Kolom produk atau quantity tidak ditemukan.")

# ==========================================
# HALAMAN 2: APRIORI ASSOCIATION ANALYSIS
# ==========================================
with page2:
    st.subheader("Halaman 2 — Apriori Association Analysis")
    st.markdown("Eksplorasi pola kedekatan produk yang sering dibeli secara bersamaan.")
    
    # Threshold Slicer di Halaman 2
    st.sidebar.markdown("---")
    st.sidebar.subheader("Threshold Apriori")
    min_supp = st.sidebar.slider("Minimum Support", min_value=0.005, max_value=0.30, value=0.02, step=0.005)
    min_conf = st.sidebar.slider("Minimum Confidence", min_value=0.10, max_value=0.90, value=0.20, step=0.05)
    
    # Fungsi Proses Apriori
    @st.cache_data
    def run_apriori(data, support, confidence):
        try:
            basket = data.groupby(['order_no', 'product_name'])['quantity'].count().unstack().fillna(0)
            basket_encoded = basket.map(lambda x: 1 if x > 0 else 0)
            frequent_itemsets = apriori(basket_encoded, min_support=support, use_colnames=True)
            if frequent_itemsets.empty:
                return pd.DataFrame(), pd.DataFrame()
            rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=confidence)
            return frequent_itemsets, rules
        except Exception:
            return pd.DataFrame(), pd.DataFrame()

    frequent_itemsets, rules = run_apriori(df_filtered, min_supp, min_conf)
    
    # Ringkasan Metric Apriori
    col_a1, col_a2, col_a3 = st.columns(3)
    col_a1.metric("Frequent Itemsets", f"{len(frequent_itemsets):,}")
    col_a2.metric("Association Rules", f"{len(rules):,}")
    col_a3.metric("Min. Support Setting", f"{min_supp}")
    
    st.markdown("---")
    
    if not rules.empty:
        # Tabel Aturan Asosiasi
        st.markdown("##### 📋 Tabel Aturan Asosiasi (A → B)")
        rules_display = rules.copy()
        rules_display['antecedents'] = rules_display['antecedents'].apply(lambda x: ', '.join(list(x)))
        rules_display['consequents'] = rules_display['consequents'].apply(lambda x: ', '.join(list(x)))
        rules_sorted = rules_display.sort_values(by='lift', ascending=False)
        st.dataframe(rules_sorted[['antecedents', 'consequents', 'support', 'confidence', 'lift']].reset_index(drop=True), use_container_width=True)
        
        # Visualisasi Aturan (Scatter & Bar)
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("##### 📉 Scatter Chart: Confidence vs Lift")
            fig, ax = plt.subplots(figsize=(8, 4))
            sns.scatterplot(x='support', y='confidence', size='lift', hue='lift', data=rules, palette='Blues', ax=ax, sizes=(40, 200))
            ax.set_title("Sebaran Rule (Support vs Confidence)")
            st.pyplot(fig)
            
        with col_r2:
            st.markdown("##### 📊 Bar Chart: Kombinasi Support Tertinggi")
            fig, ax = plt.subplots(figsize=(8, 4))
            top_sup = rules.sort_values(by='support', ascending=False).head(10)
            top_sup['rule_str'] = top_sup['antecedents'].apply(lambda x: ' & '.join(list(x))) + " → " + top_sup['consequents'].apply(lambda x: ', '.join(list(x)))
            sns.barplot(x='support', y='rule_str', data=top_sup, palette='crest', ax=ax)
            ax.set_title("Top 10 Rules by Support")
            st.pyplot(fig)
    else:
        st.warning("Tidak ada aturan asosiasi yang ditemukan dengan parameter threshold saat ini. Coba turunkan Minimum Support atau Confidence di sidebar.")

# ==========================================
# HALAMAN 3: PRODUCT BUNDLING INSIGHTS
# ==========================================
with page3:
    st.subheader("Halaman 3 — Product Bundling Insights & Rekomendasi Bisnis")
    st.markdown("Mengubah pola asosiasi menjadi strategi rekomendasi paket promosi di gerai Cooler City.")
    
    if not rules.empty:
        st.markdown("##### 🏆 Peringkat Kombinasi Produk Terbaik (Prioritas Lift & Confidence)")
        best_bundles = rules.sort_values(by=['lift', 'confidence'], ascending=False).head(5).copy()
        best_bundles['Paket Bundling'] = best_bundles['antecedents'].apply(lambda x: ' + '.join(list(x))) + "  ➔  " + best_bundles['consequents'].apply(lambda x: ' + '.join(list(x)))
        
        for idx, row in best_bundles.reset_index(drop=True).iterrows():
            with st.container():
                st.markdown(f"""
                <div style="background:#ffffff; border-left: 5px solid #2563eb; padding: 15px; border-radius: 8px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <h4 style="margin: 0; color: #1e3a8a;">Paket #{idx+1}: {row['Paket Bundling']}</h4>
                    <p style="margin: 5px 0 0 0; color: #475569; font-size: 14px;">
                        <b>Support:</b> {row['support']:.4f} | <b>Confidence:</b> {row['confidence']:.4f} | <b>Lift Ratio:</b> {row['lift']:.4f}
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("##### 💡 Panduan Interpretasi & Saran Promosi Cooler City")
        st.info("""
        **Catatan Strategis:**  
        - Jika aturan **A → B** memiliki *confidence* tinggi dan *lift* di atas **1**, pembelian produk A berkaitan erat dengan peningkatan kemungkinan pembelian produk B dibandingkan rata-rata umum.  
        - Hasil analisis ini merupakan **dasar pertimbangan dan panduan promosi (bundling)**, bukan jaminan mutlak bahwa bundling pasti meningkatkan penjualan tanpa strategi eksekusi pemasaran yang tepat.
        """)
    else:
        st.info("Silakan jalankan analisis Apriori di Halaman 2 terlebih dahulu agar rekomendasi bundling dapat ditampilkan.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #94a3b8;'>Cooler City Business Intelligence Dashboard | Powered by Streamlit & Power BI Structure</p>", unsafe_allow_html=True)
