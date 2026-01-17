import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard KRS-Kota Bogor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cache data dengan TTL untuk optimasi performa
@st.cache_data(ttl=600, show_spinner=False)
def load_dataset():
    """Memuat dan memproses data penelitian KRS"""
    try:
        data = pd.read_excel("penelitian_bersih_coba2.xlsx")
        
        # Normalisasi kolom
        data.columns = [col.lower().replace(' ', '_') for col in data.columns]
        
        # Preprocessing risiko stunting
        if 'risiko_stunting' in data.columns:
            data['risiko_stunting'] = data['risiko_stunting'].fillna('Tidak Diketahui')
            data['risiko_stunting'] = data['risiko_stunting'].astype(str).str.strip()
            
            # Mapping berbagai format ke standar
            risk_mapping = {
                '1': 'Berisiko', '0': 'Tidak Berisiko',
                'true': 'Berisiko', 'false': 'Tidak Berisiko',
                'ya': 'Berisiko', 'tidak': 'Tidak Berisiko',
                'yes': 'Berisiko', 'no': 'Tidak Berisiko',
                'tinggi': 'Berisiko', 'rendah': 'Tidak Berisiko'
            }
            
            data['risiko_stunting'] = data['risiko_stunting'].str.lower().map(risk_mapping).fillna(data['risiko_stunting'])
            data['risiko_stunting'] = data['risiko_stunting'].str.title()
        
        return data
    
    except FileNotFoundError:
        st.error("File data tidak ditemukan. Pastikan file 'penelitian_bersih.xlsx' tersedia.")
        st.stop()
    except Exception as error:
        st.error(f"Kesalahan saat memuat data: {str(error)}")
        st.stop()

def calculate_statistics(dataframe):
    """Menghitung statistik dasar dari dataset"""
    total_records = len(dataframe)
    
    if 'risiko_stunting' in dataframe.columns:
        risk_counts = dataframe['risiko_stunting'].value_counts()
        high_risk = risk_counts.get('Berisiko', 0)
        low_risk = risk_counts.get('Tidak Berisiko', 0)
    else:
        high_risk = low_risk = 0
    
    return {
        'total': total_records,
        'high_risk': high_risk,
        'low_risk': low_risk
    }

def display_header():
    """Menampilkan header aplikasi"""
    st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 12px; margin-bottom: 2rem;'>
            <h1 style='color: white; text-align: center; margin-bottom: 0.5rem; 
                       font-weight: 700; letter-spacing: -0.5px;'>
                Dashboard Keluarga Rentan Stunting - Kota Bogor
            </h1>
            <p style='color: rgba(255,255,255,0.9); text-align: center; 
                      font-size: 1.1rem; margin: 0; line-height: 1.5;'>
                        </div>
    """, unsafe_allow_html=True)

def display_metrics(stats):
    """Menampilkan metrik utama dalam card format - versi sederhana"""
    st.markdown("### Indikator Utama")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div style='background: #f8f9fa; padding: 2rem; border-radius: 10px; border-left: 5px solid #007bff; text-align: center;'>
                <h2 style='margin: 0; color: #007bff; font-size: 2.5rem; font-weight: bold;'>{stats['total']:,}</h2>
                <p style='margin: 0.5rem 0 0 0; color: #6c757d; font-weight: 600; font-size: 1.1rem;'>Total Keluarga</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        safe_percentage = (stats['low_risk'] / stats['total'] * 100) if stats['total'] > 0 else 0
        st.markdown(f"""
            <div style='background: #f8f9fa; padding: 2rem; border-radius: 10px; border-left: 5px solid #28a745; text-align: center;'>
                <h2 style='margin: 0; color: #28a745; font-size: 2.5rem; font-weight: bold;'>{stats['low_risk']:,}</h2>
                <p style='margin: 0.5rem 0 0 0; color: #6c757d; font-weight: 600; font-size: 1.1rem;'>Tidak Berisiko</p>
                <small style='color: #28a745; font-weight: 600; font-size: 0.9rem;'>{safe_percentage:.1f}%</small>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        risk_percentage = (stats['high_risk'] / stats['total'] * 100) if stats['total'] > 0 else 0
        st.markdown(f"""
            <div style='background: #f8f9fa; padding: 2rem; border-radius: 10px; border-left: 5px solid #dc3545; text-align: center;'>
                <h2 style='margin: 0; color: #dc3545; font-size: 2.5rem; font-weight: bold;'>{stats['high_risk']:,}</h2>
                <p style='margin: 0.5rem 0 0 0; color: #6c757d; font-weight: 600; font-size: 1.1rem;'>Berisiko</p>
                <small style='color: #dc3545; font-weight: 600; font-size: 0.9rem;'>{risk_percentage:.1f}%</small>
            </div>
        """, unsafe_allow_html=True)

def display_bar_chart(stats):
    """Menampilkan diagram batang distribusi risiko stunting"""
    st.markdown("### Distribusi Risiko Stunting")
    
    # Hitung persentase yang benar
    total = stats['total']
    if total > 0:
        persen_tidak_berisiko = (stats['low_risk'] / total) * 100
        persen_berisiko = (stats['high_risk'] / total) * 100
    else:
        persen_tidak_berisiko = 0
        persen_berisiko = 0
    
    # Persiapkan data untuk chart
    chart_data = pd.DataFrame({
        'Kategori': ['Tidak Berisiko', 'Berisiko'],
        'Jumlah': [stats['low_risk'], stats['high_risk']],
        'Persentase': [persen_tidak_berisiko, persen_berisiko]
    })
    
    # Buat bar chart dengan Plotly
    fig = px.bar(
        chart_data, 
        x='Kategori', 
        y='Jumlah',
        color='Kategori',
        color_discrete_map={
            'Tidak Berisiko': '#28a745',
            'Berisiko': '#dc3545'
        },
        title='',
        custom_data=['Persentase']
    )
    
    # Kustomisasi chart dengan format persentase yang lebih jelas
    fig.update_traces(
        texttemplate='%{y:,}<br>(%{customdata[0]:.1f}%)',
        textposition='outside',
        textfont=dict(size=14, color='black')
    )
    
    fig.update_layout(
        showlegend=False,
        xaxis_title="Kategori Risiko",
        yaxis_title="Jumlah Keluarga",
        font=dict(size=12),
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    
    st.plotly_chart(fig, use_container_width=True)

# Eksekusi aplikasi utama
def main():
    display_header()
    
    # Load dan proses data
    with st.spinner('Memuat dataset...'):
        dataset = load_dataset()
    
    # Hitung statistik
    statistics = calculate_statistics(dataset)
    
    # Tampilkan metrik
    display_metrics(statistics)
    
    # Tampilkan diagram batang
    display_bar_chart(statistics)

if __name__ == "__main__":
    main()