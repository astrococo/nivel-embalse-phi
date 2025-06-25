
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from io import BytesIO
from datetime import datetime
import base64
import os
import io
import zipfile

st.set_page_config(page_title="Análisis Nivel Embalse", layout="wide")
st.title("📊 Análisis del Nivel del Embalse")
st.markdown("Sube un archivo `.xls` o `.xlsx` desde tu computador para comenzar.")

uploaded_file = st.file_uploader("Sube el archivo de Excel:", type=["xls", "xlsx"])

if uploaded_file is not None:
    try:
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        file_bytes = uploaded_file.read()
        file_buffer = io.BytesIO(file_bytes)

        if file_ext == ".xls":
            df = pd.read_excel(file_buffer, sheet_name="Hoja1", engine="xlrd")
        elif file_ext == ".xlsx":
            if not zipfile.is_zipfile(file_buffer):
                raise ValueError("El archivo .xlsx no es válido o está corrupto.")
            file_buffer.seek(0)
            df = pd.read_excel(file_buffer, sheet_name="Hoja1", engine="openpyxl")
        else:
            raise ValueError("Formato no soportado. Solo .xls y .xlsx")

        df.columns = df.columns.str.strip()
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df.set_index('Fecha', inplace=True)

        tabs = st.tabs(["📥 Carga y estructura", "🔍 Nulos", "📊 Análisis Exploratorio", "🕒 Resampleo", "📤 Exportar"])

        with tabs[0]:
            st.success("✅ Archivo cargado exitosamente.")
            st.write("Vista previa de los datos:")
            st.write(df.head())
            st.write("📌 Estadísticas básicas:")
            st.dataframe(df.describe())

        with tabs[1]:
            st.subheader("🔍 Valores nulos")
            st.dataframe(df.isnull().sum())
            fig, ax = plt.subplots(figsize=(12, 1))
            sns.heatmap(df[['NivelEmbalse']].isnull().T, cbar=False, cmap='viridis')
            ax.set_title("Mapa de calor de valores nulos")
            ax.set_yticks([])
            st.pyplot(fig)

        with tabs[2]:
            st.subheader("📊 Análisis Exploratorio")
            st.plotly_chart(
                px.histogram(df, x='NivelEmbalse', nbins=50, title='Distribución del Nivel del Embalse'),
                use_container_width=True
            )
            st.plotly_chart(
                px.line(df.reset_index(), x='Fecha', y='NivelEmbalse', title='Nivel del Embalse (Original)'),
                use_container_width=True
            )

        with tabs[3]:
            df_clean = df[df['NivelEmbalse'].notnull().cummax()]
            df_clean['NivelEmbalse'] = df_clean['NivelEmbalse'].interpolate(method='linear')

            freq_options = {
                '15 minutos': '15T',
                '30 minutos': '30T',
                '1 hora': 'H',
                '1 día': 'D'
            }

            freq_label = st.selectbox("📅 Frecuencia para resampleo:", list(freq_options.keys()))
            freq_code = freq_options[freq_label]

            df_resampled = df_clean['NivelEmbalse'].resample(freq_code).mean()
            st.plotly_chart(
                px.line(df_resampled.reset_index(), x='Fecha', y='NivelEmbalse', title=f'Resampleado cada {freq_label}'),
                use_container_width=True
            )
            st.write("Vista previa del resampleo:")
            st.dataframe(df_resampled.head())

        with tabs[4]:
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
        st.exception(e)
        st.stop()
else:
    st.warning("⚠️ Por favor, sube un archivo `.xls` o `.xlsx` con las columnas `Fecha` y `NivelEmbalse`.")

