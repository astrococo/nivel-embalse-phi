import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from datetime import datetime
import base64
import os

st.set_page_config(page_title="Análisis Nivel Embalse", layout="wide")
st.title("📊 Análisis del Nivel del Embalse")
st.markdown("Sube un archivo `.xls` o `.xlsx` desde tu computador para comenzar.")

uploaded_file = st.file_uploader("Sube el archivo de Excel:", type=["xls", "xlsx"])

if uploaded_file is not None:
    try:
        # Detectar extensión y usar engine adecuado
        ext = os.path.splitext(uploaded_file.name)[1]
        if ext == ".xls":
            df = pd.read_excel(uploaded_file, sheet_name="Hoja1", engine="xlrd")
        elif ext == ".xlsx":
            df = pd.read_excel(uploaded_file, sheet_name="Hoja1", engine="openpyxl")
        else:
            raise ValueError("Formato de archivo no soportado")

        df.columns = df.columns.str.strip()
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df.set_index('Fecha', inplace=True)

        st.success("✅ Datos cargados exitosamente.")
        st.write("Vista previa de los datos:", df.head())

        st.subheader("🔍 Análisis de valores nulos")
        st.write(df.isnull().sum())

        fig, ax = plt.subplots(figsize=(12, 1))
        sns.heatmap(df[['NivelEmbalse']].isnull().T, cbar=False, cmap='viridis')
        ax.set_title("Mapa de calor de valores nulos")
        ax.set_yticks([])
        st.pyplot(fig)

        df_clean = df[df['NivelEmbalse'].notnull().cummax()]
        df_clean['NivelEmbalse'] = df_clean['NivelEmbalse'].interpolate(method='linear')

        st.subheader("🧼 Datos limpios e interpolados")
        st.write(df_clean.head())
        st.write("Valores nulos después de limpiar:", df_clean.isnull().sum())

        freq_options = {
            '15 minutos': '15T',
            '30 minutos': '30T',
            '1 hora': 'H',
            '1 día': 'D'
        }

        freq_label = st.selectbox("📅 Frecuencia para resampleo:", list(freq_options.keys()))
        freq_code = freq_options[freq_label]

        df_resampled = df_clean['NivelEmbalse'].resample(freq_code).mean()

        st.subheader(f"📈 Nivel del Embalse - Resampleado cada {freq_label}")
        fig, ax = plt.subplots(figsize=(14, 5))
        df_resampled.plot(ax=ax)
        ax.set_title(f"Nivel del Embalse ({freq_label})")
        ax.set_ylabel("Nivel (m)")
        ax.set_xlabel("Fecha")
        ax.grid(True)
        st.pyplot(fig)

        def to_excel_download_link(df_export):
            output = BytesIO()
            df_export.to_excel(output, index=True, sheet_name='DatosResampleados')
            processed_data = output.getvalue()
            b64 = base64.b64encode(processed_data).decode()
            now = datetime.now().strftime("%Y%m%d_%H%M")
            return f'<a href="data:application/octet-stream;base64,{b64}" download="nivel_embalse_resampleado_{now}.xlsx">📥 Descargar archivo Excel</a>'

        st.markdown("### 💾 Exportar resultados")
        st.markdown(to_excel_download_link(df_resampled.to_frame()), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error procesando el archivo: {e}")
else:
    st.warning("⚠️ Por favor, sube un archivo `.xls` o `.xlsx` con las columnas `Fecha` y `NivelEmbalse`.")
