import streamlit as st
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
import matplotlib.pyplot as plt
import seaborn as sns

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Cooler City Market Basket Analysis",
    page_icon="🧋",
    layout="wide"
)

st.title("🧋 Cooler City Market Basket Analysis Dashboard")
st.markdown("Dashboard interaktif untuk menganalisis pola pembelian konsumen menggunakan algoritma **Apriori**.")

# 1. Load Data
@st.cache_data
def load_data():
    file_path = "Data_CoolerCity_Apriori_Ready_v2.xlsx"
    df = pd.read_excel(file_path, sheet_name="Master Data")
    return df

df = load_data()

# Sidebar / Filter
st.sidebar.header("⚙️ Pengaturan Filter & Apriori")

# Filter Bulan
months = ["All"] + list(df['month_name'].dropna().unique())
selected_month = st.sidebar.selectbox("Pilih Bulan", months)

if selected_month != "All":
    df_filtered = df[df['month_name'] == selected_month]
else:
    df_filtered = df.copy()

# Parameter Apriori
st.sidebar.subheader("Parameter Algoritma Apriori")
min_supp = st.sidebar.slider("Minimum Support", min_value=0.01, max_value=0.50, value=0.05, step=0.01)
min_conf = st.sidebar.slider("Minimum Confidence", min_value=0.10, max_value=0.90, value=0.30, step=0.05)

# Tampilkan Metrik Utama
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Transaksi", f"{df_filtered['order_no'].nunique():,}")
col2.metric("Total Produk Terjual", f"{df_filtered['quantity'].sum():,}")
col3.metric("Total Pendapatan", f"Rp {df_filtered['subtotal'].sum():,}")
col4.metric("Jumlah Kategori", f"{df_filtered['category_name'].nunique()}")
st.markdown("---")

# Proses Apriori
@st.cache_data
def run_apriori(data, min_support, min_confidence):
    # Buat One-Hot Encoding berdasarkan order_no dan product_name (Menggunakan .map untuk pandas terbaru)
    basket = data.groupby(['order_no', 'product_name'])['quantity'].count().unstack().fillna(0)
    basket_encoded = basket.map(lambda x: 1 if x > 0 else 0)
    
    # Jalankan Apriori
    frequent_itemsets = apriori(basket_encoded, min_support=min_support, use_colnames=True)
    
    if frequent_itemsets.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
    return frequent_itemsets, rules

frequent_itemsets, rules = run_apriori(df_filtered, min_supp, min_conf)

# Layout Tabs
tab1, tab2, tab3 = st.tabs(["📈 Frequent Itemsets", "🔗 Association Rules", "📊 Visualisasi & Insights"])

with tab1:
    st.subheader("Daftar Kombinasi Produk Sering Dibeli (Frequent Itemsets)")
    if not frequent_itemsets.empty:
        fi_sorted = frequent_itemsets.sort_values(by='support', ascending=False)
        fi_sorted['itemsets'] = fi_sorted['itemsets'].apply(lambda x: ', '.join(list(x)))
        st.dataframe(fi_sorted.reset_index(drop=True), use_container_width=True)
    else:
        st.warning("Tidak ada itemset yang memenuhi minimum support tersebut. Coba turunkan nilai Minimum Support di sidebar.")

with tab2:
    st.subheader("Aturan Asosiasi (Association Rules)")
    if not rules.empty:
        rules_display = rules.copy()
        rules_display['antecedents'] = rules_display['antecedents'].apply(lambda x: ', '.join(list(x)))
        rules_display['consequents'] = rules_display['consequents'].apply(lambda x: ', '.join(list(x)))
        rules_sorted = rules_display.sort_values(by='lift', ascending=False)
        st.dataframe(rules_sorted[['antecedents', 'consequents', 'support', 'confidence', 'lift']].reset_index(drop=True), use_container_width=True)
    else:
        st.warning("Tidak ada aturan asosiasi yang ditemukan dengan parameter saat ini.")

with tab3:
    st.subheader("Visualisasi Pola Pembelian")
    if not rules.empty:
        col_v1, col_v2 = st.columns(2)
        
        with col_v1:
            st.markdown("##### Top 10 Rules Berdasarkan Lift")
            fig, ax = plt.subplots(figsize=(8, 5))
            top_rules = rules.sort_values(by='lift', ascending=False).head(10)
            top_rules['rule_str'] = top_rules['antecedents'].apply(lambda x: ' & '.join(list(x))) + " -> " + top_rules['consequents'].apply(lambda x: ' & '.join(list(x)))
            sns.barplot(x='lift', y='rule_str', data=top_rules, palette='viridis', ax=ax)
            ax.set_xlabel("Lift Ratio")
            ax.set_ylabel("Association Rules")
            st.pyplot(fig)
            
        with col_v2:
            st.markdown("##### Scatter Plot: Support vs Confidence")
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            sns.scatterplot(x='support', y='confidence', size='lift', hue='lift', data=rules, palette='coolwarm', ax=ax2, sizes=(50, 200))
            ax2.set_xlabel("Support")
            ax2.set_ylabel("Confidence")
            st.pyplot(fig2)
    else:
        st.info("Visualisasi akan muncul setelah aturan asosiasi berhasil dihasilkan.")

st.markdown("---")
st.markdown("<p style='text-align: center;'>Cooler City Business Intelligence Dashboard | Powered by Streamlit & Apriori</p>", unsafe_allow_html=True)
