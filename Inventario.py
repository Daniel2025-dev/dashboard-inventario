# inventario.py
# Dashboard de Inventario con UI moderna (Streamlit + Plotly)
# - Carga Excel desde ruta relativa o uploader
# - Normaliza columnas (maneja acentos y variantes)
# - Filtros con sidebar modernizada (alto contraste)
# - KPIs en cards, indicadores por contador (promedio de horas, productividad correcta)
# - Visualizaciones con etiquetas internas y paleta actual
# - Resúmenes por tipo/estado/cliente con tablas y gráficos
# - Código listo para ejecutarse localmente o en Streamlit Cloud
# - Mejora visual sustancial + KPIs adicionales + formato numérico con puntos y %.
# - Ajustes: tasa de cumplimiento extendida, tooltips backlog, export con openpyxl.
# - Sidebar: recuadros y chips de filtros con paleta oscura, cambio visible y total.

import os
from io import BytesIO
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ======================================================
# 🌈 CONFIGURACIÓN GENERAL + TEMA/ESTILOS
# ======================================================
st.set_page_config(page_title="Dashboard de Inventario", layout="wide", page_icon="📦")

# --------- UTILIDADES DE FORMATO (puntos y %) ----------
def num_dot(x, decimals=0):
    try:
        if pd.isna(x):
            x = 0
        fmt = f"{{:,.{decimals}f}}".format(float(x))
        # Reemplaza comas por puntos (miles) y deja punto decimal
        fmt = fmt.replace(",", "X").replace(".", ",").replace("X", ".")
        if decimals == 0:
            fmt = fmt.replace(",00", "")
        return fmt
    except Exception:
        return str(x)

def pct(x, decimals=1):
    try:
        v = float(x) * 100 if abs(float(x)) <= 1 else float(x)  # acepta 0.87 o 87
        fmt = f"{v:.{decimals}f}"
        return f"{fmt}%"
    except Exception:
        return "0%"

def series_num_dot(s, decimals=0):
    return s.fillna(0).apply(lambda v: num_dot(v, decimals))

# --------- CSS (incluye ajustes de FILTERS en sidebar) ----------
st.markdown("""
<style>
/* Tipografía base */
html, body, [class*="css"] { font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
.main { padding-top: 0rem; }

/* Header superior */
.app-header {
  background: linear-gradient(90deg, #0ea5e9 0%, #6366f1 100%);
  color: white; padding: 18px 24px; border-radius: 16px; margin-bottom: 18px;
  display: flex; align-items: center; gap: 12px;
}
.app-header h1 { margin: 0; font-size: 1.55rem; font-weight: 800; letter-spacing: .2px; }

/* KPI Cards */
.kpi {
  background: white; border: 1px solid #eef0f5; border-radius: 14px; padding: 16px;
  box-shadow: 0 6px 18px rgba(2,6,23,.06);
}
.kpi .label { color: #64748b; font-size: .85rem; margin-bottom: 6px; }
.kpi .value { font-size: 1.6rem; font-weight: 800; color: #0f172a; }

/* Contenedor de gráfico / bloque */
.block {
  background: white; border: 1px solid #eef0f5; border-radius: 16px; padding: 14px 14px 8px;
  box-shadow: 0 6px 20px rgba(2,6,23,.06); margin-bottom: 12px;
}

/* ===== Sidebar oscuro ===== */
section[data-testid="stSidebar"]{
  background: linear-gradient(180deg,#0b1220 0%, #0c1325 100%);
  border-right: 1px solid #0f172a;
}
section[data-testid="stSidebar"] *{ color:#e5e7eb !important; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3{
  color:#f8fafc !important; letter-spacing:.2px;
}

/* ====== CAMPOS de filtros (Selectbox / Multiselect) ====== */
/* Recuadro del input */
section[data-testid="stSidebar"] .stSelectbox > div > div,
section[data-testid="stSidebar"] .stMultiSelect > div > div,
section[data-testid="stSidebar"] .stDateInput > div > div{
  background:#1e293b !important;          /* fondo oscuro armonizado */
  border:1px solid #3b4252 !important;     /* borde gris azulado */
  border-radius:12px !important;
  box-shadow:none !important;
}

/* Placeholder y texto dentro del input */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea{
  color:#e5e7eb !important;
}
section[data-testid="stSidebar"] input::placeholder{
  color:#9ca3af !important;
}

/* Chips (etiquetas) dentro del multiselect */
section[data-testid="stSidebar"] div[data-baseweb="tag"]{
  background:#2563eb !important;          /* azul principal */
  border:1px solid #3b82f6 !important;
  color:#ffffff !important;                /* texto BLANCO */
  border-radius:8px !important;
  padding:.22rem .5rem !important;
  font-weight:600; letter-spacing:.2px;
}
section[data-testid="stSidebar"] div[data-baseweb="tag"]:hover{
  background:#1d4ed8 !important; border-color:#60a5fa !important;
}
section[data-testid="stSidebar"] div[data-baseweb="tag"] span{ color:#ffffff !important; }
section[data-testid="stSidebar"] div[data-baseweb="tag"] svg{ fill:#bfdbfe !important; }

/* Dropdown de opciones */
section[data-testid="stSidebar"] div[role="listbox"]{
  background:#0b1220 !important; border:1px solid #334155 !important;
}
section[data-testid="stSidebar"] div[role="option"]{
  color:#e5e7eb !important;
}
section[data-testid="stSidebar"] div[role="option"][aria-selected="true"]{
  background:#1d4ed8 !important; color:#ffffff !important;
}

/* Focus/hover de inputs */
section[data-testid="stSidebar"] .stSelectbox > div > div:focus-within,
section[data-testid="stSidebar"] .stMultiSelect > div > div:focus-within,
section[data-testid="stSidebar"] .stDateInput > div > div:focus-within{
  border-color:#60a5fa !important; box-shadow:0 0 0 2px rgba(56,189,248,.25) !important;
}

/* Scrollbar sidebar */
section[data-testid="stSidebar"] ::-webkit-scrollbar{ width:10px; }
section[data-testid="stSidebar"] ::-webkit-scrollbar-track{ background:#0b1220; }
section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb{ background:#334155; border-radius:10px; border:2px solid #0b1220; }
section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover{ background:#475569; }

/* Dataframe hover */
.dataframe tbody tr:hover { background: #f8fafc; }

/* Botones coherentes */
button[kind="primary"]{ background:#6366f1 !important; border:0 !important; }
button[kind="primary"]:hover{ background:#4f46e5 !important; }
</style>
""", unsafe_allow_html=True)

# --------- HEADER (sin etiqueta secundaria) ---------
st.markdown("""
<div class="app-header">
  <div style="font-size:28px">📦</div>
  <div><h1>Dashboard de Inventario – Warehousing</h1></div>
</div>
""", unsafe_allow_html=True)

# --------- Plotly defaults (paleta moderna) ----------
PALETA = ["#0ea5e9","#6366f1","#22c55e","#f59e0b","#62748E","#a855f7","#14b8a6","#f43f5e"]
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = PALETA
px.defaults.height = 420

# ==========================================
# 📥 CARGA DE DATOS
# ==========================================
RELATIVE_EXCEL = "Dashboard_Lista de tareas 2025.xlsx"

@st.cache_data
def leer_excel_desde_bytes(b: bytes) -> pd.DataFrame:
    return pd.read_excel(BytesIO(b))  # openpyxl por defecto

@st.cache_data
def leer_excel_desde_ruta(path: str) -> pd.DataFrame:
    return pd.read_excel(path)

def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    cols = (df.columns
        .str.strip().str.lower().str.replace(" ", "_")
        .str.replace("á","a").str.replace("é","e").str.replace("í","i").str.replace("ó","o").str.replace("ú","u")
        .str.replace("ñ","n"))
    df.columns = cols
    df = df.rename(columns={
        "accion":"accion", "accion_ejecutada":"accion", "accion_realizada":"accion",
        "codigo_inventario":"codigo_inventario", "codigo":"codigo_inventario",
        "codigo__inventario":"codigo_inventario", "código_inventario":"codigo_inventario"
    })
    return df

def a_horas_decimales(x):
    if pd.isna(x): return 0
    if isinstance(x, str):
        try:
            parts = x.split(":"); parts += ["0"]*(3-len(parts))
            h, m, s = map(int, parts[:3]); return h + m/60 + s/3600
        except: return 0
    try:
        return getattr(x, "hour", 0) + getattr(x, "minute", 0)/60 + getattr(x, "second", 0)/3600
    except:
        try: return float(x)
        except: return 0

# Carga tolerante
if os.path.exists(RELATIVE_EXCEL):
    df = leer_excel_desde_ruta(RELATIVE_EXCEL)
    st.caption(f"📁 Archivo cargado desde el proyecto: {RELATIVE_EXCEL}")
else:
    st.info("No se encontró el Excel relativo. Puedes subir uno para continuar.")
    up = st.file_uploader("Sube un archivo Excel (.xlsx / .xls)", type=["xlsx","xls"])
    if up is None:
        st.stop()
    df = leer_excel_desde_bytes(up.getvalue())
    st.caption(f"☁️ Archivo cargado desde uploader: {up.name}")

# ============================
# 🧹 LIMPIEZA / PREPARACIONES
# ============================
df = normalizar_columnas(df)

requeridas = [
    "fecha_de_inicio","fecha_de_termino","total_horas","cliente","coordinador",
    "contenedores_asignados","contenedores_contados","ubicaciones_asignadas",
    "ubicaciones_contadas","contador","tipo_de_inventario","prioridad",
    "estado_de_inventario","codigo_inventario"
]
faltantes = [c for c in requeridas if c not in df.columns]
if faltantes:
    st.error(f"❌ Columnas faltantes en el archivo: {faltantes}")
    st.stop()

df["fecha_de_inicio"] = pd.to_datetime(df["fecha_de_inicio"], errors="coerce")
df["fecha_de_termino"] = pd.to_datetime(df["fecha_de_termino"], errors="coerce")
df["horas_decimal"] = df["total_horas"].apply(a_horas_decimales)

col_pct = "%_completado" if "%_completado" in df.columns else None
if col_pct is None:
    df["%_completado"] = 0.0
    col_pct = "%_completado"

# ======================
# 🔎 FILTROS (sidebar)
# ======================
st.sidebar.header("📅 Rango de fechas")
fmin = df["fecha_de_inicio"].min().date()
fmax = df["fecha_de_inicio"].max().date()
rango = st.sidebar.date_input("Selecciona el período", (fmin, fmax), min_value=fmin, max_value=fmax)
if isinstance(rango, tuple) and len(rango) == 2:
    ini, fin = pd.to_datetime(rango[0]), pd.to_datetime(rango[1])
    df = df[df["fecha_de_inicio"].between(ini, fin)]

st.sidebar.header("🎯 Filtros")
clientes = st.sidebar.multiselect("Cliente", sorted(df["cliente"].dropna().unique()),
                                  default=list(sorted(df["cliente"].dropna().unique())))
coordinadores = st.sidebar.multiselect("Coordinador", sorted(df["coordinador"].dropna().unique()),
                                       default=list(sorted(df["coordinador"].dropna().unique())))
tipos = st.sidebar.multiselect("Tipo de inventario", sorted(df["tipo_de_inventario"].dropna().unique()),
                               default=list(sorted(df["tipo_de_inventario"].dropna().unique())))
estados = st.sidebar.multiselect("Estado", sorted(df["estado_de_inventario"].dropna().unique()),
                                 default=list(sorted(df["estado_de_inventario"].dropna().unique())))
prioridades = st.sidebar.multiselect("Prioridad", sorted(df["prioridad"].dropna().unique()),
                                     default=list(sorted(df["prioridad"].dropna().unique())))

df = df[
    df["cliente"].isin(clientes) &
    df["coordinador"].isin(coordinadores) &
    df["tipo_de_inventario"].isin(tipos) &
    df["estado_de_inventario"].isin(estados) &
    df["prioridad"].isin(prioridades)
]

# ======================
# 🔢 KPIs
# ======================
total_horas = df["horas_decimal"].sum()
prom_completado = df[col_pct].mean() if len(df) else 0
inventarios_unicos = df["codigo_inventario"].nunique()

total_contenedores_asig = df["contenedores_asignados"].fillna(0).sum()
total_contenedores_cont = df["contenedores_contados"].fillna(0).sum()
total_ubic_asig = df["ubicaciones_asignadas"].fillna(0).sum()
total_ubic_cont = df["ubicaciones_contadas"].fillna(0).sum()

avance_contenedores = (total_contenedores_cont / total_contenedores_asig) if total_contenedores_asig else 0
avance_ubicaciones = (total_ubic_cont / total_ubic_asig) if total_ubic_asig else 0
backlog_contenedores = max(total_contenedores_asig - total_contenedores_cont, 0)
backlog_ubicaciones = max(total_ubic_asig - total_ubic_cont, 0)

# ====== reconocimiento ampliado de "completado" ======
df["estado_de_inventario_norm"] = df["estado_de_inventario"].astype(str).str.lower().str.strip()
estados_completos = {
    "completado","completada","completo",
    "finalizado","finalizada","terminado","terminada",
    "cerrado","cerrada","ok","hecho","listo"
}
def es_pct_completo(v):
    try:
        val = float(v)
        if val <= 1:   # 0.0-1.0
            return val >= 0.99
        else:          # 0-100
            return val >= 99
    except:
        return False

mask_estado = df["estado_de_inventario_norm"].isin(estados_completos) \
              | df["estado_de_inventario_norm"].str.contains("100", na=False)
mask_pct = df[col_pct].apply(es_pct_completo)

cumplidos = df.loc[mask_estado | mask_pct, "codigo_inventario"].nunique()
total_invs = df["codigo_inventario"].nunique()
tasa_cumplimiento = (cumplidos / total_invs) if total_invs else 0

duracion_prom_por_inv = df.groupby("codigo_inventario")["horas_decimal"].sum().mean() if total_invs else 0
prod_global_cont = (total_contenedores_cont / total_horas) if total_horas else 0
prod_global_ubic = (total_ubic_cont / total_horas) if total_horas else 0

tooltip_backlog_cont = ("Backlog contenedores: contenedores asignados que aún no han sido contados. "
                        "Fórmula = Asignados - Contados.")
tooltip_backlog_ubic = ("Backlog ubicaciones: ubicaciones asignadas que aún no han sido contadas. "
                        "Fórmula = Asignadas - Contadas.")

k1,k2,k3,k4 = st.columns(4)
with k1:
    st.markdown(f'<div class="kpi" title="Suma de horas en el período/filtrado.">'
                f'<div class="label">Total horas trabajadas</div>'
                f'<div class="value">{num_dot(total_horas, 2)} h</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi" title="Promedio de avance de los registros filtrados.">'
                f'<div class="label">% promedio completado</div>'
                f'<div class="value">{pct(prom_completado, 1)}</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi" title="Códigos de inventario únicos en la vista.">'
                f'<div class="label">Inventarios únicos</div>'
                f'<div class="value">{num_dot(inventarios_unicos)}</div></div>', unsafe_allow_html=True)
with k4:
    st.markdown(f'<div class="kpi" title="Inventarios con estado final o ≥99% de avance.">'
                f'<div class="label">Tasa de cumplimiento</div>'
                f'<div class="value">{pct(tasa_cumplimiento, 1)}</div></div>', unsafe_allow_html=True)

k5,k6,k7,k8 = st.columns(4)
with k5:
    st.markdown(f'<div class="kpi" title="Contenedores contados / asignados.">'
                f'<div class="label">Avance contenedores</div>'
                f'<div class="value">{pct(avance_contenedores, 1)}</div></div>', unsafe_allow_html=True)
with k6:
    st.markdown(f'<div class="kpi" title="Ubicaciones contadas / asignadas.">'
                f'<div class="label">Avance ubicaciones</div>'
                f'<div class="value">{pct(avance_ubicaciones, 1)}</div></div>', unsafe_allow_html=True)
with k7:
    st.markdown(f'<div class="kpi" title="{tooltip_backlog_cont}">'
                f'<div class="label">Backlog contenedores</div>'
                f'<div class="value">{num_dot(backlog_contenedores)}</div></div>', unsafe_allow_html=True)
with k8:
    st.markdown(f'<div class="kpi" title="{tooltip_backlog_ubic}">'
                f'<div class="label">Backlog ubicaciones</div>'
                f'<div class="value">{num_dot(backlog_ubicaciones)}</div></div>', unsafe_allow_html=True)

k9,k10 = st.columns(2)
with k9:
    st.markdown(f'<div class="kpi" title="Contenedores contados por hora trabajada (global).">'
                f'<div class="label">Prod. global (contenedores/h)</div>'
                f'<div class="value">{num_dot(prod_global_cont, 2)}</div></div>', unsafe_allow_html=True)
with k10:
    st.markdown(f'<div class="kpi" title="Ubicaciones contadas por hora trabajada (global).">'
                f'<div class="label">Prod. global (ubicaciones/h)</div>'
                f'<div class="value">{num_dot(prod_global_ubic, 2)}</div></div>', unsafe_allow_html=True)

# =====================================
# 📊 INDICADORES POR CONTADOR
# =====================================
resumen = (
    df.groupby("contador", dropna=False)
      .agg(
          horas_totales=("horas_decimal","sum"),
          horas_promedio=("horas_decimal","mean"),
          contenedores_contados=("contenedores_contados","sum"),
          ubicaciones_contadas=("ubicaciones_contadas","sum"),
          porcentaje_completado=(col_pct,"mean"),
          clientes=("cliente","nunique")
      ).reset_index()
)

# Productividades → usa np.nan para evitar dtype object
resumen["productividad_contenedores"] = resumen["contenedores_contados"] / resumen["horas_totales"].replace(0, np.nan)
resumen["productividad_ubicaciones"] = resumen["ubicaciones_contadas"] / resumen["horas_totales"].replace(0, np.nan)

# ---------- COERCE A NUMÉRICO (evita TypeError en round) ----------
cols_num = [
    "horas_totales","horas_promedio","contenedores_contados","ubicaciones_contadas",
    "porcentaje_completado","productividad_contenedores","productividad_ubicaciones"
]
for c in cols_num:
    resumen[c] = pd.to_numeric(resumen[c], errors="coerce")

# Formateo
resumen_fmt = resumen.copy()
resumen_fmt["porcentaje_completado"] = (resumen_fmt["porcentaje_completado"]*100).round(2)
resumen_fmt["horas_promedio"] = resumen_fmt["horas_promedio"].round(2)
resumen_fmt["productividad_contenedores"] = resumen_fmt["productividad_contenedores"].round(2)
resumen_fmt["productividad_ubicaciones"] = resumen_fmt["productividad_ubicaciones"].round(2)
resumen_fmt["contenedores_contados"] = resumen_fmt["contenedores_contados"].fillna(0).astype(int)
resumen_fmt["ubicaciones_contadas"] = resumen_fmt["ubicaciones_contadas"].fillna(0).astype(int)

st.markdown("### 📊 Indicadores por Contador")
st.dataframe(
    resumen_fmt.rename(columns={"horas_promedio":"prom_horas"})[
        ["contador","prom_horas","contenedores_contados","ubicaciones_contadas",
         "productividad_contenedores","productividad_ubicaciones","porcentaje_completado","clientes"]
    ].style.format({
        "prom_horas": lambda v: num_dot(v, 2),
        "productividad_contenedores": lambda v: num_dot(v, 2),
        "productividad_ubicaciones": lambda v: num_dot(v, 2),
        "porcentaje_completado": lambda v: pct(v, 2),
        "contenedores_contados": lambda v: num_dot(v, 0),
        "ubicaciones_contadas": lambda v: num_dot(v, 0),
        "clientes": lambda v: num_dot(v, 0),
    }),
    use_container_width=True
)

# ===========================
# 🧭 TABS: Visualizaciones / Resúmenes
# ===========================
tab1, tab2 = st.tabs(["📈 Visualizaciones", "📋 Resúmenes"])

with tab1:
    st.markdown('<div class="block">', unsafe_allow_html=True)
    orden_hp = resumen_fmt.sort_values("prom_horas")
    fig1 = px.bar(
        orden_hp, x="prom_horas", y="contador", orientation="h", color="contador",
        text=orden_hp["prom_horas"].apply(lambda v: f"{(0 if pd.isna(v) else v):.2f} h"),
        title="⏱ Promedio de horas por contador"
    )
    fig1.update_traces(textposition="inside",
                       hovertemplate="<b>%{y}</b><br>Horas prom.: %{x:.2f} h")
    fig1.update_layout(xaxis_title="Horas promedio", yaxis_title="",
                       margin=dict(l=10,r=10,t=60,b=10), showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="block">', unsafe_allow_html=True)
        orden = resumen_fmt.sort_values("contenedores_contados")
        fig2 = px.bar(
            orden, x="contenedores_contados", y="contador", orientation="h", color="contador",
            text=orden["contenedores_contados"].apply(lambda v: num_dot(v, 0)),
            title="📦 Contenedores contados (totales)"
        )
        fig2.update_traces(textposition="inside",
                           hovertemplate="<b>%{y}</b><br>Contenedores: %{x}")
        fig2.update_layout(xaxis_title="Unidades", yaxis_title="",
                           margin=dict(l=10,r=10,t=60,b=10), showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="block">', unsafe_allow_html=True)
        orden = resumen_fmt.sort_values("ubicaciones_contadas")
        fig3 = px.bar(
            orden, x="ubicaciones_contadas", y="contador", orientation="h", color="contador",
            text=orden["ubicaciones_contadas"].apply(lambda v: num_dot(v, 0)),
            title="📍 Ubicaciones contadas (totales)"
        )
        fig3.update_traces(textposition="inside",
                           hovertemplate="<b>%{y}</b><br>Ubicaciones: %{x}")
        fig3.update_layout(xaxis_title="Unidades", yaxis_title="",
                           margin=dict(l=10,r=10,t=60,b=10), showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="block">', unsafe_allow_html=True)
    tipo_inv_pie = df["tipo_de_inventario"].value_counts().reset_index()
    tipo_inv_pie.columns = ["tipo_de_inventario", "cantidad"]
    fig4 = px.pie(
        tipo_inv_pie, names="tipo_de_inventario", values="cantidad",
        title="📊 Distribución porcentual por Tipo de inventario", hole=.45
    )
    fig4.update_traces(textinfo="percent+label", hovertemplate="<b>%{label}</b><br>%{percent}")
    st.plotly_chart(fig4, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tipos de inventario", int(df["tipo_de_inventario"].nunique()))
    c2.metric("Estados de inventario", int(df["estado_de_inventario"].nunique()))
    c3.metric("Clientes únicos", int(df["cliente"].nunique()))
    c4.metric("Inventarios únicos", int(df["codigo_inventario"].nunique()))

    st.markdown("### 📋 Resúmenes")

    resumen_tipo_estado = (
        df.groupby(["tipo_de_inventario", "estado_de_inventario"])["codigo_inventario"]
          .nunique().reset_index().sort_values("codigo_inventario", ascending=False)
    )
    resumen_tipo_estado.columns = ["Tipo de Inventario", "Estado de Inventario", "Inventarios Únicos"]
    st.write("**Inventarios únicos por Tipo y Estado**")
    st.dataframe(
        resumen_tipo_estado.style.format({"Inventarios Únicos": lambda v: num_dot(v, 0)}),
        use_container_width=True
    )

    resumen_tipo = (
        df.groupby("tipo_de_inventario")["codigo_inventario"]
          .nunique().reset_index().sort_values("codigo_inventario", ascending=False)
    )
    resumen_tipo.columns = ["Tipo de Inventario", "Inventarios Únicos"]
    st.write("**Inventarios únicos por Tipo**")
    st.dataframe(
        resumen_tipo.style.format({"Inventarios Únicos": lambda v: num_dot(v, 0)}),
        use_container_width=True
    )

    resumen_cliente = (
        df.groupby("cliente")["codigo_inventario"]
          .nunique().reset_index().sort_values("codigo_inventario", ascending=False)
    )
    resumen_cliente.columns = ["Cliente", "Inventarios Únicos"]
    st.write("**Inventarios únicos por Cliente**")
    st.dataframe(
        resumen_cliente.style.format({"Inventarios Únicos": lambda v: num_dot(v, 0)}),
        use_container_width=True
    )

    orden_tipos = resumen_tipo.sort_values("Inventarios Únicos")
    fig_tipos = px.bar(
        orden_tipos, x="Inventarios Únicos", y="Tipo de Inventario", orientation="h",
        text=orden_tipos["Inventarios Únicos"].apply(lambda v: num_dot(v,0)),
        color="Tipo de Inventario", title="📊 Inventarios únicos por Tipo"
    )
    fig_tipos.update_traces(textposition="inside")
    fig_tipos.update_layout(xaxis_title="Inventarios únicos", yaxis_title="",
                            uniformtext_minsize=8, uniformtext_mode="hide", showlegend=False)
    st.plotly_chart(fig_tipos, use_container_width=True)

    fig_estado = px.bar(
        resumen_tipo_estado, x="Tipo de Inventario", y="Inventarios Únicos",
        color="Estado de Inventario", barmode="group",
        text=resumen_tipo_estado["Inventarios Únicos"].apply(lambda v: num_dot(v,0)),
        title="📊 Inventarios únicos por Tipo y Estado"
    )
    fig_estado.update_traces(textposition="inside")
    fig_estado.update_layout(xaxis_title="Tipo de inventario", yaxis_title="Inventarios únicos",
                             legend_title="Estado", uniformtext_minsize=8, uniformtext_mode="hide")
    st.plotly_chart(fig_estado, use_container_width=True)

    top_n = 15
    resumen_cliente_top = resumen_cliente.head(top_n).sort_values("Inventarios Únicos")
    fig_clientes = px.bar(
        resumen_cliente_top, x="Inventarios Únicos", y="Cliente", orientation="h",
        text=resumen_cliente_top["Inventarios Únicos"].apply(lambda v: num_dot(v,0)),
        color="Cliente", title=f"👥 Top {top_n} clientes por inventarios únicos"
    )
    fig_clientes.update_traces(textposition="inside")
    fig_clientes.update_layout(xaxis_title="Inventarios únicos", yaxis_title="",
                               uniformtext_minsize=8, uniformtext_mode="hide", showlegend=False)
    st.plotly_chart(fig_clientes, use_container_width=True)

# ======================
# 📤 Descarga de datos filtrados (engine=openpyxl)
# ======================
def to_excel_bytes(df_in: pd.DataFrame) -> bytes:
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df_in.to_excel(writer, index=False, sheet_name="filtrado")
    return out.getvalue()

st.download_button(
    "⬇️ Descargar datos filtrados (Excel)",
    data=to_excel_bytes(df),
    file_name="inventario_filtrado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)

# ===== ULTRA-OVERRIDE FINAL PARA ASEGURAR AZUL EN CHIPS DEL SIDEBAR =====
st.markdown("""
<style>
section[data-testid="stSidebar"] .stMultiSelect > div > div {
  background-color: #1e293b !important;
  border: 1px solid #3b4252 !important;
  border-radius: 12px !important;
  box-shadow: none !important;
}
section[data-testid="stSidebar"] [data-baseweb="tag"],
section[data-testid="stSidebar"] span[data-baseweb="tag"],
section[data-testid="stSidebar"] div[data-baseweb="tag"]{
  background-color: #2563eb !important;
  background: #2563eb !important;
  border: 1px solid #3b82f6 !important;
  color: #ffffff !important;
  border-radius: 8px !important;
  padding: .22rem .5rem !important;
  font-weight: 600 !important;
  letter-spacing: .2px !important;
}
section[data-testid="stSidebar"] [data-baseweb="tag"] span { color: #ffffff !important; }
section[data-testid="stSidebar"] [data-baseweb="tag"] svg  { fill:  #bfdbfe !important; }
section[data-testid="stSidebar"] [data-baseweb="tag"]:hover {
  background-color: #1d4ed8 !important;
  background: #1d4ed8 !important;
  border-color: #60a5fa !important;
}
section[data-testid="stSidebar"] div[role="listbox"] {
  background:#0b1220 !important; border:1px solid #334155 !important;
}
section[data-testid="stSidebar"] div[role="option"] { color:#e5e7eb !important; }
section[data-testid="stSidebar"] div[role="option"][aria-selected="true"] {
  background:#1d4ed8 !important; color:#ffffff !important;
}
</style>
""", unsafe_allow_html=True)

# ========== FIN ==========

