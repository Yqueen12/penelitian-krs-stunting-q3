import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.features import CustomIcon
import base64
from pathlib import Path

# ========== Konfigurasi Awal ========== #
st.set_page_config(page_title="Visualisasi Risiko Stunting", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
        
        .main > div {
            font-family: 'Poppins', sans-serif;
        }
        
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin: 10px 0;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }
        
        .metric-number {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .metric-label {
            font-size: 1rem;
            opacity: 0.9;
        }
        
        .section-header {
            color: #667eea;
            font-size: 1.8rem;
            font-weight: 600;
            margin: 30px 0 20px 0;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .info-box {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 15px;
            border-radius: 10px;
            color: white;
            margin: 10px 0;
        }
        
        .upload-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin: 20px 0;
        }
        
        .sidebar .stSelectbox > label {
            font-weight: 600;
            color: #667eea;
        }
        
        .legend-container {
            border: 1px solid #667eea;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
        }
    </style>
""", unsafe_allow_html=True)

# ================= HELPER FUNCTIONS ================= #

def get_icon_path(status):
    """Get path untuk custom marker icon"""
    if status == 'Aman':
        return 'assets/marker_green.png'
    else:
        return 'assets/marker_red.png'

# ================= CACHED FUNCTIONS ================= #

@st.cache_data
def load_data_from_upload(uploaded_file):
    """Load data dari file yang diupload dengan caching"""
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Format file tidak didukung! Gunakan file .csv, .xlsx, atau .xls")
            return pd.DataFrame()
        
        df.columns = df.columns.str.lower()
        
        required_columns = ['namakecamatan', 'risiko_stunting', 'lat', 'lon']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"⚠️ Kolom yang diperlukan tidak ditemukan: {', '.join(missing_columns)}")
            return pd.DataFrame()
        
        df['risiko_stunting'] = df['risiko_stunting'].astype(str).str.strip().str.title()
        df['risiko_stunting'] = df['risiko_stunting'].replace({
            '1': 'Berisiko', '0': 'Tidak Berisiko',
            'True': 'Berisiko', 'False': 'Tidak Berisiko',
            'Yes': 'Berisiko', 'No': 'Tidak Berisiko'
        })
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error saat membaca file: {str(e)}")
        return pd.DataFrame()

def calculate_kecamatan_status(df):
    """Calculate status untuk kecamatan berdasarkan dataframe yang diberikan (TIDAK LAGI CACHED)"""
    kecamatan_stats = {}
    
    for kecamatan in df['namakecamatan'].unique():
        df_kec = df[df['namakecamatan'] == kecamatan]
        total = len(df_kec)
        
        if total == 0:
            kecamatan_stats[kecamatan] = {
                'status': 'Aman',
                'persentase': 0.0,
                'berisiko': 0,
                'tidak_berisiko': 0,
                'total': 0
            }
        else:
            berisiko = len(df_kec[df_kec['risiko_stunting'] == 'Berisiko'])
            tidak_berisiko = len(df_kec[df_kec['risiko_stunting'] == 'Tidak Berisiko'])
            persentase = (berisiko / total) * 100
            status = 'Rentan Stunting' if persentase > 20 else 'Aman'
            
            kecamatan_stats[kecamatan] = {
                'status': status,
                'persentase': persentase,
                'berisiko': berisiko,
                'tidak_berisiko': tidak_berisiko,
                'total': total
            }
    
    return kecamatan_stats

def generate_map(df, kecamatan_stats):
    """Generate map dengan custom marker icons (TIDAK LAGI CACHED)"""
    if df.empty:
        return None
        
    df = df.dropna(subset=['lat', 'lon'])
    
    if df.empty:
        return None

    # Group data untuk efisiensi
    map_data = df.groupby('namakecamatan').agg({
        'lat': 'mean',
        'lon': 'mean'
    }).reset_index()

    m = folium.Map(
        location=[df['lat'].mean(), df['lon'].mean()], 
        zoom_start=12,
        prefer_canvas=True
    )

    for _, row in map_data.iterrows():
        kec_name = row['namakecamatan']
        stats = kecamatan_stats[kec_name]
        
        is_aman = stats['status'] == 'Aman'
        status_emoji = "✅" if is_aman else "⚠️"
        status_color = "#51cf66" if is_aman else "#ff6b6b"

        popup_html = f"""
        <div style="font-size: 14px; font-family: 'Poppins', sans-serif; min-width: 250px;">
            <b style="color: #667eea;">📍 Kecamatan:</b> {kec_name}<br>
            <b style="color: {status_color};">{status_emoji} Status:</b> <b>{stats['status']}</b><br>
            <b style="color: #ff6b6b;">📊 Persentase Berisiko:</b> <b>{stats['persentase']:.1f}%</b><br><br>
            <b style="color: #667eea;">📈 Distribusi Data:</b><br>
            ✅ Tidak Berisiko: <b>{stats['tidak_berisiko']}</b> ({stats['tidak_berisiko']/stats['total']*100:.1f}%)<br>
            ⚠️ Berisiko: <b>{stats['berisiko']}</b> ({stats['berisiko']/stats['total']*100:.1f}%)<br>
            <b style="color: #764ba2;">📊 Total Data: {stats['total']}</b><br><br>
            <i style="color: #999; font-size: 11px;">
            * Standar WHO: >20% Berisiko = Rentan Stunting<br>
            * ≤20% Berisiko = Aman
            </i>
        </div>
        """

        # Gunakan custom icon
        icon_path = get_icon_path(stats['status'])
        
        # Cek apakah file icon ada
        if Path(icon_path).exists():
            custom_icon = CustomIcon(
                icon_path,
                icon_size=(40, 40),
                icon_anchor=(20, 40),
                popup_anchor=(0, -40)
            )
            
            folium.Marker(
                location=[row['lat'], row['lon']],
                icon=custom_icon,
                popup=folium.Popup(popup_html, max_width=400)
            ).add_to(m)
        else:
            # Fallback ke icon default jika file tidak ditemukan
            color = 'green' if is_aman else 'red'
            folium.Marker(
                location=[row['lat'], row['lon']],
                icon=folium.Icon(color=color, icon='info-sign'),
                popup=folium.Popup(popup_html, max_width=400)
            ).add_to(m)

    return m

# ========== Main App ========== #
def main():
    # Header
    st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="background: linear-gradient(90deg, #667eea, #764ba2); 
                       background-clip: text; -webkit-background-clip: text; 
                       -webkit-text-fill-color: transparent; 
                       font-size: 3rem; font-weight: 700; margin: 0;">
                Peta Keluarga Rentan Stunting Kota Bogor
            </h1>
            <p style="color: #666; margin-top: 10px; font-size: 1.1rem;">
                Klasifikasi Berdasarkan Standar WHO (Threshold >20% Kasus Berisiko)
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Upload File Section
    st.markdown("""
        <div class="upload-box">
            <h2 style="margin-top: 0; color: white;">📂 Upload File Data Stunting</h2>
            <p style="margin-bottom: 0; opacity: 0.9;">
                Upload file Excel (.xlsx, .xls) atau CSV (.csv) yang berisi data keluarga rentan stunting
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Pilih file data",
        type=['csv', 'xlsx', 'xls'],
        help="File harus memiliki kolom: namakecamatan, risiko_stunting, lat, lon",
        label_visibility="collapsed"
    )
    
    # Info tentang format file
    with st.expander("ℹ️ Informasi Format File yang Dibutuhkan"):
        st.markdown("""
        **Kolom Wajib:**
        - `namakecamatan`: Nama kecamatan
        - `risiko_stunting`: Status risiko (Berisiko/Tidak Berisiko atau 1/0)
        - `lat`: Koordinat latitude
        - `lon`: Koordinat longitude
        
        **Kolom Opsional:**
        - `tahun`: Tahun data (jika ada, akan muncul filter tahun)
        
        **Format Nilai risiko_stunting yang didukung:**
        - Berisiko / Tidak Berisiko
        - 1 / 0
        - True / False
        - Yes / No
        """)
    
    # Jika belum upload file
    if uploaded_file is None:
        st.info("👆 Silakan upload file data terlebih dahulu untuk memulai visualisasi")
        
        st.markdown("### 📋 Contoh Struktur Data")
        sample_data = pd.DataFrame({
            'namakecamatan': ['Kecamatan X', 'Kecamatan X', 'Kecamatan Y'],
            'risiko_stunting': ['Berisiko', 'Tidak Berisiko', 'Berisiko'],
            'lat': [-6.5971, -6.5975, -6.6021],
            'lon': [106.8060, 106.8065, 106.8100],
            'tahun': [2024, 2024, 2024]
        })
        st.dataframe(sample_data, use_container_width=True)
        return
    
    # Load data dengan caching
    with st.spinner('Loading data...'):
        df = load_data_from_upload(uploaded_file)
    
    if df.empty:
        return
    
    st.success(f"✅ File berhasil dimuat! Total data: {len(df):,} baris")
    
    # Preview data
    with st.expander("👁️ Preview Data yang Diupload"):
        st.dataframe(df.head(10), use_container_width=True)

    # Sidebar Filter
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 20px 0;">
                <h2 style="color: #667eea; font-weight: 700;">🔍 Filter Data</h2>
            </div>
        """, unsafe_allow_html=True)
        
        kec = ['Semua'] + sorted(df['namakecamatan'].unique())
        
        kecamatan = st.selectbox("📍 Pilih Kecamatan", kec)
        
        if 'tahun' in df.columns:
            tahun = ['Semua'] + sorted(df['tahun'].unique(), reverse=True)
            tahun_select = st.selectbox("📅 Pilih Tahun", tahun)
        else:
            tahun_select = 'Semua'

        st.markdown("""
            <div class="info-box">
                <h4>ℹ️ Standar WHO</h4>
                <p style="font-size: 13px; line-height: 1.6;">
                <b>"Suatu wilayah dikatakan memiliki masalah stunting bila kasusnya mencapai angka di atas 20%"</b>
                </p>
                <hr style="border-color: rgba(255,255,255,0.3); margin: 10px 0;">
                <p><b>✅ Kecamatan Aman (Hijau):</b><br>
                Persentase Berisiko ≤ 20%</p>
                <p><b>⚠️ Kecamatan Rentan (Merah):</b><br>
                Persentase Berisiko > 20%</p>
                <hr style="border-color: rgba(255,255,255,0.3); margin: 10px 0;">
                <p style="font-size: 12px; opacity: 0.9;">
                Klik marker pada peta untuk melihat detail lengkap setiap kecamatan
                </p>
            </div>
        """, unsafe_allow_html=True)

    # Filter DataFrame
    df_filtered = df.copy()
    if kecamatan != 'Semua':
        df_filtered = df_filtered[df_filtered['namakecamatan'] == kecamatan]
    if tahun_select != 'Semua' and 'tahun' in df.columns:
        df_filtered = df_filtered[df_filtered['tahun'] == tahun_select]

    if df_filtered.empty:
        st.warning("❗ Tidak ada data untuk filter yang dipilih.")
        return

    # PERBAIKAN UTAMA: Hitung statistik berdasarkan data yang SUDAH DIFILTER
    with st.spinner('Calculating statistics...'):
        kecamatan_stats = calculate_kecamatan_status(df_filtered)

    # Calculate metrics
    jumlah_aman = sum(1 for s in kecamatan_stats.values() if s['status'] == 'Aman')
    jumlah_rentan = sum(1 for s in kecamatan_stats.values() if s['status'] == 'Rentan Stunting')

    # Metrics Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number">{len(df_filtered):,}</div>
                <div class="metric-label">📊 Total Data Keluarga</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <div class="metric-number">{df_filtered['namakecamatan'].nunique()}</div>
                <div class="metric-label">📍 Total Kecamatan</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                <div class="metric-number">{jumlah_aman}</div>
                <div class="metric-label">✅ Kecamatan Aman</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
                <div class="metric-number">{jumlah_rentan}</div>
                <div class="metric-label">⚠️ Kecamatan Rentan</div>
            </div>
        """, unsafe_allow_html=True)

    # Peta
    st.markdown('<h2 class="section-header">🗺️ Peta Keluarga Rentan Stunting</h2>', unsafe_allow_html=True)
        
    st.markdown("""
        <div class="legend-container">
            <h4 style="margin-top: 0; color: #667eea;">📍 Legenda Peta (Berdasarkan Standar WHO)</h4>
            <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
                <div style="display: flex; align-items: center; margin: 5px;">
                    <div style="width: 20px; height: 20px; background-color: #51cf66; border-radius: 50%; margin-right: 10px;"></div>
                    <span><b>Kecamatan Aman</b> (≤20% Berisiko)</span>
                </div>
                <div style="display: flex; align-items: center; margin: 5px;">
                    <div style="width: 20px; height: 20px; background-color: #ff6b6b; border-radius: 50%; margin-right: 10px;"></div>
                    <span><b>Kecamatan Rentan Stunting</b> (>20% Berisiko)</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    with st.spinner('Generating map...'):
        map_obj = generate_map(df_filtered, kecamatan_stats)
        if map_obj:
            st_folium(map_obj, height=600, width=None, returned_objects=[])
        else:
            st.error("Tidak dapat menampilkan peta. Pastikan data koordinat tersedia.")

    # Footer
    st.markdown("""
        <div style="text-align: center; padding: 30px 0 10px 0; color: #666;">
            <hr style="border: 1px solid #eee;">
            <p><b>Penerapan Algoritma Stacked LSTM untuk Klasifikasi dan Visualisasi Keluarga Rentan Stunting</b></p>
            <p style="font-size: 13px; margin-top: 5px; color: #888;">
                Klasifikasi berdasarkan Standar WHO:<br>
                <i>"Suatu wilayah dikatakan memiliki masalah stunting bila kasusnya mencapai angka di atas 20%"</i>
            </p>
            <p style="font-size: 12px; margin-top: 5px;">
                Kecamatan dengan >20% kasus berisiko = <span style="color: #ff6b6b; font-weight: 600;">Rentan Stunting</span> | 
                ≤20% = <span style="color: #51cf66; font-weight: 600;">Aman</span>
            </p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()