import streamlit as st
import numpy as np
import pandas as pd
import pickle
from tensorflow.keras.models import load_model

# ==============================
# KONFIGURASI HALAMAN
# ==============================
st.set_page_config(
    page_title="Klasifikasi Keluarga Rentan Stunting",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# CUSTOM CSS
# ==============================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        padding: 2.5rem;
        border-radius: 12px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    .risk-box {
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        text-align: center;
    }
    .high-risk {
        background: #dc3545;
        color: white;
    }
    .low-risk {
        background: #28a745;
        color: white;
    }
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2c3e50;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e0e0e0;
    }
    .stForm {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================
# HEADER APLIKASI
# ==============================
st.markdown("""
<div class="main-header">
    <h1>Klasifikasi Keluarga Rentan Stunting</h1>
    """, unsafe_allow_html=True)

# ==============================
# FUNGSI MEMUAT MODEL & SCALER
# ==============================
@st.cache_resource
def load_ml_components():
    """
    Memuat model LSTM dan scaler dari file.
    Pastikan file:
      - model_lstm_2layer_risiko_stunting.h5
      - preprocess_lstm_2layer_risiko_stunting.pkl
    berada di folder yang sama dengan app.py
    """
    try:
        model = load_model("model_lstm_2layer_risiko_stunting.h5")
        with open("preprocess_lstm_2layer_risiko_stunting.pkl", "rb") as file:
            preprocess_data = pickle.load(file)
            scaler = preprocess_data["scaler"]
        return model, scaler
    except Exception as e:
        st.error(f"Gagal memuat model atau scaler: {str(e)}")
        return None, None

model, scaler = load_ml_components()

# Hanya tampilkan form jika model berhasil dimuat
if model is not None and scaler is not None:
    
    with st.form("family_risk_assessment"):
        
        col1, col2 = st.columns(2)
        
        with col1:
            has_baduta = st.radio(
                "Apakah memiliki anak Baduta (0–24 bulan)?",
                ["Tidak", "Ya"],
                index=0,
                horizontal=True
            )
            
            has_balita = st.radio(
                "Apakah memiliki anak Balita (0–59 bulan)?",
                ["Tidak", "Ya"],
                index=0,
                horizontal=True
            )
            
            pus_status = st.radio(
                "Apakah termasuk Pasangan Usia Subur (PUS)?",
                ["Tidak", "Ya"],
                index=0,
                horizontal=True
            )
            
            pregnancy_status = st.radio(
                "Apakah ada yang sedang hamil?",
                ["Tidak", "Ya"],
                index=0,
                horizontal=True
            )
            
            age_young = st.radio(
                "Apakah ibu hamil terlalu muda (< 20 tahun)?",
                ["Tidak", "Ya"],
                index=0,
                horizontal=True
            )
            
            age_old = st.radio(
                "Apakah ibu hamil terlalu tua (> 35 tahun)?",
                ["Tidak", "Ya"],
                index=0,
                horizontal=True
            )

        with col2:
            birth_spacing = st.radio(
                "Apakah jarak kelahiran < 2 tahun?",
                ["Tidak", "Ya"],
                index=0,
                horizontal=True
            )
            
            children_count = st.radio(
                "Apakah jumlah anak > 4?",
                ["Tidak", "Ya"],
                index=0,
                horizontal=True
            )
            
            kb_participation = st.radio(
                "Apakah tidak menggunakan KB modern?",
                ["Tidak", "Ya"],
                index=0,
                horizontal=True
            )
            
            water_source = st.selectbox(
                "Sumber Air Utama Keluarga",
                [
                    "Air kemasan/isi ulang",
                    "Ledeng/PAM",
                    "Sumur bor/pompa",
                    "Sumur terlindung",
                    "Sumur tak terlindung",
                    "Mata air terlindung",
                    "Mata air tak terlindung",
                    "Air permukaan (sungai/danau/waduk/kolam/irigasi)",
                    "Air hujan",
                    "Lainnya"
                ]
            )
            
            sanitation_quality = st.radio(
                "Apakah jamban tidak memenuhi standar?",
                ["Tidak", "Ya"],
                index=0,
                horizontal=True
            )
            
            welfare_rank = st.selectbox(
                "Peringkat Kesejahteraan Keluarga",
                [
                    "Peringkat Kesejahteraan >4",
                    "Peringkat Kesejahteraan 1",
                    "Peringkat Kesejahteraan 2",
                    "Peringkat Kesejahteraan 3",
                    "Peringkat Kesejahteraan 4",
                    "Keluarga belum teridentifikasi tingkat kesejahteraannya"
                ]
            )

        # Submit Button
        st.markdown("---")
        submit_analysis = st.form_submit_button(
            "Analisis Risiko Stunting",
            use_container_width=True
        )

    # ==============================
    # PROSES PREDIKSI
    # ==============================
    if submit_analysis:
        # Mapping sumber air ke nilai numerik (1–10)
        water_source_mapping = {
            "Air kemasan/isi ulang": 1,
            "Ledeng/PAM": 2,
            "Sumur bor/pompa": 3,
            "Sumur terlindung": 4,
            "Sumur tak terlindung": 5,
            "Mata air terlindung": 6,
            "Mata air tak terlindung": 7,
            "Air permukaan (sungai/danau/waduk/kolam/irigasi)": 8,
            "Air hujan": 9,
            "Lainnya": 10
        }

        # Mapping peringkat kesejahteraan ke nilai numerik
        welfare_mapping = {
            "Peringkat Kesejahteraan >4": 0,
            "Peringkat Kesejahteraan 1": 1,
            "Peringkat Kesejahteraan 2": 2,
            "Peringkat Kesejahteraan 3": 3,
            "Peringkat Kesejahteraan 4": 4,
            "Keluarga belum teridentifikasi tingkat kesejahteraannya": 99
        }

        # Menyusun data keluarga dalam bentuk dictionary
        family_data = {
            "baduta": 1 if has_baduta == "Ya" else 0,
            "balita": 1 if has_balita == "Ya" else 0,
            "pus": 1 if pus_status == "Ya" else 0,
            "pus_hamil": 1 if pregnancy_status == "Ya" else 0,
            "sumber_air_layak_tidak": water_source_mapping[water_source],
            "jamban_layak_tidak": 1 if sanitation_quality == "Ya" else 0,
            "terlalu_muda": 1 if age_young == "Ya" else 0,
            "terlalu_tua": 1 if age_old == "Ya" else 0,
            "terlalu_dekat": 1 if birth_spacing == "Ya" else 0,
            "terlalu_banyak": 1 if children_count == "Ya" else 0,
            "bukan_peserta_kb_modern": 1 if kb_participation == "Ya" else 0,
            "kesejahteraan_prioritas": welfare_mapping[welfare_rank],
        }

        # Konversi ke DataFrame
        input_df = pd.DataFrame([family_data])

        # Scaling data
        try:
            scaled_data = scaler.transform(input_df)
        except Exception as e:
            st.error(f"Terjadi kesalahan saat scaling data: {str(e)}")
            st.stop()

        # Bentuk input untuk LSTM: (batch_size, time_steps, features)
        lstm_input = scaled_data.reshape((1, 1, input_df.shape[1]))

        with st.spinner("Sedang menganalisis risiko keluarga..."):
            prediction_result = model.predict(lstm_input)[0][0]

        st.markdown("---")
        st.markdown("## Hasil Analisis")

        # Tampilkan hasil klasifikasi
        if prediction_result >= 0.5:
            st.markdown("""
            <div class="risk-box high-risk">
                <h3>Berisiko</h3>
                <p>Keluarga teridentifikasi <strong>berisiko stunting</strong>.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="risk-box low-risk">
                <h3>Tidak Berisiko</h3>
                <p>Keluarga teridentifikasi <strong>tidak berisiko stunting</strong>.</p>
            </div>
            """, unsafe_allow_html=True)

        # Tampilkan ringkasan input
        with st.expander("Lihat Ringkasan Data yang Dimasukkan"):
            st.write(input_df)

# ==============================
# FOOTER
# ==============================
st.markdown("---")
st.markdown("""
<div style="text-align: center; background: #f8f9fa; padding: 1.5rem; border-radius: 8px; margin-top: 2rem;">
    <p><strong>Penerapan Algoritma Stacked LSTM untuk Klasifikasi Keluarga Rentan Stunting.</strong></p>
</div>
""", unsafe_allow_html=True)