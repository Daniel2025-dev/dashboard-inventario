import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración
st.set_page_config(page_title="Dashboard de Inventario", layout="wide")
st.title("📦 Dashboard de Inventario - Warehousing")

# Ruta del archivo Excel
RUTA_ARCHIVO = r"Dashboard_Lista de tareas 2025.xlsx"


@st.cache_data
def cargar_datos(ruta):
    df = pd.read_excel(ruta)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df

try:
    df = cargar_datos(RUTA_ARCHIVO)
except FileNotFoundError:
    st.error(f"No se encontró el archivo en la ruta: {RUTA_ARCHIVO}")
    st.stop()

# Validar columnas
# Normalizar nombres de columnas
df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("á", "a")
    .str.replace("é", "e")
    .str.replace("í", "i")
    .str.replace("ó", "o")
    .str.replace("ú", "u")
    .str.replace("ñ", "n")
)

# Reemplazo personalizado de columnas comunes mal escritas
reemplazo_columnas = {
    "codigo_inventario": "codigo_inventario",
    "codigo__inventario": "codigo_inventario",
    "codigo": "codigo_inventario",
    "accion": "accion",
    "acción": "accion",
    "accion_ejecutada": "accion"
}
df.rename(columns=reemplazo_columnas, inplace=True)

# Verificación de columnas necesarias
columnas_requeridas = [
    'fecha_de_inicio', 'fecha_de_termino', 'total_horas', 'cliente', 'coordinador',
    'contenedores_asignados', 'contenedores_contados', 'ubicaciones_asignadas', 'ubicaciones_contadas',
    'contador', 'tipo_de_inventario', 'prioridad', '%_completado', 'inventario',
    'estado_de_inventario', 'criterio', 'codigo_inventario', 'accion'
]

faltantes = [col for col in columnas_requeridas if col not in df.columns]
if faltantes:
    st.error(f"❌ Columnas faltantes: {faltantes}")
    st.stop()

# Procesamiento de fechas y horas
df['fecha_de_inicio'] = pd.to_datetime(df['fecha_de_inicio'], errors='coerce')
df['fecha_de_termino'] = pd.to_datetime(df['fecha_de_termino'], errors='coerce')

def convertir_a_horas(tiempo):
    if pd.isna(tiempo):
        return 0
    if isinstance(tiempo, str):
        try:
            h, m, s = map(int, tiempo.split(":"))
            return h + m / 60 + s / 3600
        except:
            return 0
    try:
        return tiempo.hour + tiempo.minute / 60 + tiempo.second / 3600
    except:
        return float(tiempo)

df["horas_decimal"] = df["total_horas"].apply(convertir_a_horas)

# 📅 Filtro por rango de fechas
st.sidebar.subheader("📅 Rango de fechas")
min_fecha = df["fecha_de_inicio"].min().date()
max_fecha = df["fecha_de_inicio"].max().date()
rango = st.sidebar.date_input("Seleccionar período", (min_fecha, max_fecha), min_value=min_fecha, max_value=max_fecha)

if isinstance(rango, tuple) and len(rango) == 2:
    inicio, fin = pd.to_datetime(rango[0]), pd.to_datetime(rango[1])
    df = df[(df["fecha_de_inicio"] >= inicio) & (df["fecha_de_inicio"] <= fin)]

# Filtros adicionales
clientes = st.sidebar.multiselect("Cliente", df["cliente"].dropna().unique(), default=df["cliente"].dropna().unique())
coordinadores = st.sidebar.multiselect("Coordinador", df["coordinador"].dropna().unique(), default=df["coordinador"].dropna().unique())
tipos_inv = st.sidebar.multiselect("Tipo de inventario", df["tipo_de_inventario"].dropna().unique(), default=df["tipo_de_inventario"].dropna().unique())
estados = st.sidebar.multiselect("Estado", df["estado_de_inventario"].dropna().unique(), default=df["estado_de_inventario"].dropna().unique())
prioridades = st.sidebar.multiselect("Prioridad", df["prioridad"].dropna().unique(), default=df["prioridad"].dropna().unique())

df = df[
    (df["cliente"].isin(clientes)) &
    (df["coordinador"].isin(coordinadores)) &
    (df["tipo_de_inventario"].isin(tipos_inv)) &
    (df["estado_de_inventario"].isin(estados)) &
    (df["prioridad"].isin(prioridades))
]

# KPIs generales
st.subheader("📌 Indicadores Generales - Equipo control de stock")
col1, col2, col3 = st.columns(3)
col1.metric("⏱ Total horas trabajadas", round(df["horas_decimal"].sum(), 2))
col2.metric("✅ % promedio completado", f"{df['%_completado'].mean()*100:.1f}%")
col3.metric("📦 Inventarios únicos", df["codigo_inventario"].nunique())

# 📊 Indicadores por Contador
resumen = df.groupby("contador").agg(
    total_horas=("horas_decimal", "sum"),
    contenedores_contados=("contenedores_contados", "sum"),
    ubicaciones_contadas=("ubicaciones_contadas", "sum"),
    productividad_contenedores=("contenedores_contados", lambda x: round(x.sum() / df["horas_decimal"].sum(), 2)),
    productividad_ubicaciones=("ubicaciones_contadas", lambda x: round(x.sum() / df["horas_decimal"].sum(), 2)),
    porcentaje_completado=("%_completado", "mean"),
    clientes=("cliente", "nunique")
).reset_index()

resumen["porcentaje_completado"] = resumen["porcentaje_completado"] * 100
resumen = resumen.round(2)

st.subheader("📊 Indicadores por Contador")
st.dataframe(resumen, use_container_width=True)

# 📈 Visualizaciones
with st.expander("📈 Visualizaciones Detalladas"):
    fig1 = px.bar(resumen, x="total_horas", y="contador", orientation="h", text="total_horas", color="contador",
                  title="⏱ Horas trabajadas por contador")
    fig1.update_traces(textposition='inside')
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.bar(resumen, x="contenedores_contados", y="contador", orientation="h", text="contenedores_contados", color="contador",
                  title="📦 Contenedores contados por contador")
    fig2.update_traces(textposition='inside')
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.bar(resumen, x="ubicaciones_contadas", y="contador", orientation="h", text="ubicaciones_contadas", color="contador",
                  title="📍 Ubicaciones contadas por contador")
    fig3.update_traces(textposition='inside')
    st.plotly_chart(fig3, use_container_width=True)

# 📊 Distribución porcentual por Tipo de Inventario
tipo_inv_pie = df["tipo_de_inventario"].value_counts().reset_index()
tipo_inv_pie.columns = ["tipo_de_inventario", "cantidad"]

fig4 = px.pie(
    tipo_inv_pie,
    names="tipo_de_inventario",
    values="cantidad",
    title="📊 Distribución porcentual por Tipo de Inventario",
    hole=0.4  # para un gráfico tipo dona, opcional
)

fig4.update_traces(textinfo='percent+label')  # Mostrar % y etiqueta
st.plotly_chart(fig4, use_container_width=True)

# 📄 Resumen por tipo de inventario
resumen_tipo_de_inventario = df.groupby("tipo_de_inventario")["contenedores_contados"].sum().reset_index().sort_values(by="contenedores_contados", ascending=False)
st.subheader("📋 Resumen de Contenedores contados por tipo de inventario")
st.dataframe(resumen_tipo_de_inventario, use_container_width=True)

# 📄 Resumen por Cliente
resumen_cliente = df.groupby("cliente")["contenedores_contados"].sum().reset_index().sort_values(by="contenedores_contados", ascending=False)
st.subheader("📋 Resumen de Contenedores contados por Cliente")
st.dataframe(resumen_cliente, use_container_width=True)

# 📄 Resumen por tipo y estado de inventario
resumen_tipo_estado = (
    df.groupby(["tipo_de_inventario", "estado_de_inventario"])["codigo_inventario"]
    .nunique()
    .reset_index()
    .sort_values(by="codigo_inventario", ascending=False)
)

resumen_tipo_estado.columns = ["Tipo de Inventario", "Estado de Inventario", "Inventarios Únicos"]

st.subheader("📋 Resumen por Tipo y Estado de Inventario")
st.dataframe(resumen_tipo_estado, use_container_width=True)

import plotly.express as px

fig_estado = px.bar(
    resumen_tipo_estado,
    x="Tipo de Inventario",
    y="Inventarios Únicos",
    color="Estado de Inventario",
    barmode="group",
    title="📊 Inventarios Únicos por Tipo y Estado"
)
st.plotly_chart(fig_estado, use_container_width=True)



