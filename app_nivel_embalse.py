import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from datetime import datetime
import base64
import os
import io
import zipfile

# ─── CONFIGURACIÓN GENERAL ──────────────────────────────────────────────
st.set_page_config(page_title="Análisis Nivel Embalse", layout="wide")
st.title("📊 Análisis del Nivel del Embalse")
st.markdown("Sube un archivo `.xls` o `.xlsx` desde tu computador para comenzar.")

# ─── SUBIDA DE ARCHIVO ──────────────────────────────────────────────────
uploaded_file = st.file_uploader("Sube el archivo de Excel:", type=["xls", "xlsx"])

if uploaded_file is not None:
    try:
        # ─── DETECCIÓN Y LECTURA SEGURA DEL ARCHIVO ─────────────────────
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()

        if file_ext == ".xls":
            df = pd.read_excel(uploaded_file, sheet_name="Hoja1", engine="xlrd")

        elif file_ext == ".xlsx":
            file_bytes = uploaded_file.read()

            if not zipfile.is_zipfile(io.BytesIO(file_bytes)):
                raise ValueError("El archivo .xlsx no es válido o está corrupto.")

            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name="Hoja1", engine="openpyxl")

        else:
            raise ValueError("Formato de archivo no soportado. Solo se aceptan .xls o .xlsx")

        # ─── LIMPIEZA BÁSICA ──────────────────────────────────────────────
        df.columns = df.columns.str.strip()
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df.set_index('Fecha', inplace=True)

        st.success("✅ Archivo cargado exitosamente.")
        st.write("Vista previa de los datos:")
        st.write(df.head())

        # ─── ANÁLISIS DE VALORES NULOS ────────────────────────────────────
        st.subheader("🔍 Análisis de valores nulos")
        st.write(df.isnull().sum())

        fig, ax = plt.subplots(figsize=(12, 1))
        sns.heatmap(df[['NivelEmbalse']].isnull().T, cbar=False, cmap='viridis')
        ax.set_title("Mapa de calor de valores nulos")
        ax.set_yticks([])
        st.pyplot(fig)

        # ─── LIMPIEZA E INTERPOLACIÓN ─────────────────────────────────────
        df_clean = df[df['NivelEmbalse'].notnull().cummax()]
        df_clean['NivelEmbalse'] = df_clean['NivelEmbalse'].interpolate(method='linear')

        st.subheader("🧼 Datos limpios e interpolados")
        st.write(df_clean.head())
        st.write("Valores nulos después de interpolar:")
        st.write(df_clean.isnull().sum())

        # ─── RESAMPLEO ─────────────────────────────────────────────────────
        freq_options = {
            '15 minutos': '15T',
            '30 minutos': '30T',
            '1 hora': 'H',
            '1 día': 'D'
        }

        freq_label = st.selectbox("📅 Frecuencia para resampleo:", list(freq_options.keys()))
        freq_code = freq_options[freq_label]

        df_resampled = df_clean['NivelEmbalse'].resample(freq_code).mean()

        # ─── GRÁFICO INTERACTIVO ──────────────────────────────────────────
        st.subheader(f"📈 Nivel del Embalse - Resampleado cada {freq_label}")
        fig, ax = plt.subplots(figsize=(14, 5))
        df_resampled.plot(ax=ax)
        ax.set_title(f"Nivel del Embalse ({freq_label})")
        ax.set_ylabel("Nivel (m)")
        ax.set_xlabel("Fecha")
        ax.grid(True)
        st.pyplot(fig)

        # ─── EXPORTACIÓN ─────────────────────────────────────────────────
        def to_excel_download_link(df_export):
            output = BytesIO()
            df_export.to_excel(output, index=True, sheet_name='Resampleado')
            processed_data = output.getvalue()
            b64 = base64.b64encode(processed_data).decode()
            now = datetime.now().strftime("%Y%m%d_%H%M")
            return f'<a href="data:application/octet-stream;base64,{b64}" download="nivel_embalse_{now}.xlsx">📥 Descargar Excel</a>'

        st.markdown("### 💾 Exportar resultados:")
        st.markdown(to_excel_download_link(df_resampled.to_frame()), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error procesando el archivo: {e}")
        st.stop()
else:
    st.warning("⚠️ Por favor, sube un archivo `.xls` o `.xlsx` con las columnas `Fecha` y `NivelEmbalse`.")
