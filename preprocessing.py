import pandas as pd

def process_drop_columns_with_year(df):
    """
    Preprocessing dataset dengan menghapus semua kolom
    kecuali:
    - latitude
    - longitude
    - nama_kelurahan
    - nama_kecamatan
    - tahun
    """

    # ===============================
    # 1. Normalisasi nama kolom
    # ===============================
    df.columns = (
        df.columns
        .str.lower()
        .str.strip()
        .str.replace(" ", "_")
    )

    # ===============================
    # 2. Mapping nama kolom alternatif
    # ===============================
    column_mapping = {
        # koordinat
        "latitude": "lat",
        "lat": "lat",
        "longitude": "lon",
        "lng": "lon",
        "long": "lon",

        # administratif
        "nama_kelurahan": "namakelurahan",
        "kelurahan": "namakelurahan",
        "nama_desa": "namakelurahan",

        "nama_kecamatan": "namakecamatan",
        "kecamatan": "namakecamatan",
        "resiko_stunting": "risiko_stunting",
        
        # temporal
        "tahun": "tahun",
        "year": "tahun"
    }

    df = df.rename(columns=column_mapping)

    # ===============================
    # 3. Kolom wajib final
    # ===============================
    required_columns = [
        "lat",
        "lon",
        "namakelurahan",
        "namakecamatan",
        "tahun",
        "risiko_stunting"
    ]

    # ===============================
    # 4. Validasi kolom wajib
    # ===============================
    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Kolom wajib tidak ditemukan: {', '.join(missing_columns)}"
        )

    # ===============================
    # 5. Drop kolom selain yang dibutuhkan
    # ===============================
    df = df[required_columns]

    # ===============================
    # 6. Optional: cleaning dasar
    # ===============================
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["tahun"] = pd.to_numeric(df["tahun"], errors="coerce")

    df = df.dropna(subset=["lat", "lon", "tahun"])

    return df


def export_to_excel(df, output_path):
    """
    Menyimpan DataFrame hasil preprocessing
    ke file Excel (.xlsx)
    """
    df.to_excel(output_path, index=False)


df = pd.read_excel("KRS - 3201 Bogor Th. 2024.xlsx")

df_processed = process_drop_columns_with_year(df)

export_to_excel(
    df_processed,
    "dataset_stunting_preprocessed.xlsx"
)
