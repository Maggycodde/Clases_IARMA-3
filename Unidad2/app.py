from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

try:
    from scipy.signal import periodogram
    HAY_SCIPY = True
except ImportError:
    HAY_SCIPY = False

st.set_page_config(
    page_title="SoundLens · Análisis musical",
    layout="wide",
    initial_sidebar_state="expanded",
)

FONDO = "#0B0F14"
SUPERFICIE = "#151A22"
BORDE = "#262D3A"
TEXTO = "#E6EAF0"
TEXTO_SUAVE = "#9AA4B2"
MENTA = "#2DD4A7"   
AMBAR = "#F5B83D"    
LILA = "#C084FC"     
ARENA = "#E7D8B8"

ESCALA_MENTA = [[0, "#0F1B1A"], [1, MENTA]]
ESCALA_DIVERGENTE = [[0, LILA], [0.5, SUPERFICIE], [1, AMBAR]]
SECUENCIA = [MENTA, AMBAR, LILA, ARENA]

ORDEN_POP = ["Baja", "Media", "Alta", "Muy Alta"]
ORDEN_DUR = ["2:00 - 2:44", "2:45 - 3:29", "3:30 - 4:14", "4:15 - 5:00"]

RUTA_CSV = Path(__file__).parent / "songs_2000_2020_50k_limpio.csv"

pio.templates["soundlens"] = go.layout.Template(
    layout=dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXTO, family="Inter, Segoe UI, sans-serif"),
        colorway=SECUENCIA,
        xaxis=dict(gridcolor=BORDE, zerolinecolor=BORDE, linecolor=BORDE, automargin=True),
        yaxis=dict(gridcolor=BORDE, zerolinecolor=BORDE, linecolor=BORDE, automargin=True),
        title=dict(font=dict(size=16, color=TEXTO), x=0, xanchor="left"),
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=SUPERFICIE, font_color=TEXTO),
    )
)
pio.templates.default = "soundlens"

CSS = """
<style>
.stApp { background-color: __FONDO__; }
.block-container { padding-top: 2rem; max-width: 1400px; }
[data-testid="stSidebar"] {
    background-color: __SUPERFICIE__;
    border-right: 1px solid __BORDE__;
}
[data-testid="stMetric"] {
    background-color: __SUPERFICIE__;
    border: 1px solid __BORDE__;
    border-radius: 14px;
    padding: 16px 18px;
}
[data-testid="stMetricValue"] { color: __MENTA__; font-weight: 700; }
[data-testid="stMetricLabel"] { color: __TEXTO_SUAVE__; }
h1, h2, h3 { letter-spacing: -0.01em; }
.marca { font-size: 1.5rem; font-weight: 800; color: __TEXTO__; }
.marca span { color: __MENTA__; }
.sub-marca { color: __TEXTO_SUAVE__; font-size: 0.85rem; margin-bottom: 0.5rem; }
.pagina-titulo { font-size: 2rem; font-weight: 800; margin-bottom: 0; color: __TEXTO__; }
.pagina-sub { color: __TEXTO_SUAVE__; margin-top: 0.2rem; margin-bottom: 1.2rem; }
.card {
    background-color: __SUPERFICIE__;
    border: 1px solid __BORDE__;
    border-left: 4px solid __AMBAR__;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.card-title { color: __AMBAR__; font-weight: 700; font-size: 0.85rem;
              text-transform: uppercase; letter-spacing: 0.04em; }
.card-text { color: __TEXTO__; margin-top: 4px; }
#MainMenu, footer { visibility: hidden; }
</style>
"""
for _clave, _valor in {
    "__FONDO__": FONDO, "__SUPERFICIE__": SUPERFICIE, "__BORDE__": BORDE,
    "__TEXTO__": TEXTO, "__TEXTO_SUAVE__": TEXTO_SUAVE,
    "__MENTA__": MENTA, "__AMBAR__": AMBAR,
}.items():
    CSS = CSS.replace(_clave, _valor)
st.markdown(CSS, unsafe_allow_html=True)

def mostrar(fig, altura=None):
    """Muestra una gráfica de Plotly respetando la plantilla propia."""
    if altura:
        fig.update_layout(height=altura)
    try:
        st.plotly_chart(fig, width="stretch", theme=None)
    except TypeError: 
        st.plotly_chart(fig, use_container_width=True, theme=None)


def mostrar_tabla(df, altura=None, ocultar_indice=False):
    opciones = {}
    if altura:
        opciones["height"] = altura
    if ocultar_indice:
        opciones["hide_index"] = True
    try:
        st.dataframe(df, width="stretch", **opciones)
    except TypeError:
        st.dataframe(df, use_container_width=True, **opciones)


def formato_duracion(segundos):
    segundos = int(round(segundos))
    return f"{segundos // 60}:{segundos % 60:02d}"


def encabezado(titulo, subtitulo):
    st.markdown(f'<div class="pagina-titulo">{titulo}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pagina-sub">{subtitulo}</div>', unsafe_allow_html=True)


def tarjeta(titulo, texto):
    st.markdown(
        f'<div class="card"><div class="card-title">{titulo}</div>'
        f'<div class="card-text">{texto}</div></div>',
        unsafe_allow_html=True,
    )


def conteo_ordenado(serie, orden, nombre):
    """Cuenta categorías y las devuelve en el orden indicado."""
    tabla = serie.value_counts().reindex(orden).fillna(0).reset_index()
    tabla.columns = [nombre, "Canciones"]
    return tabla

@st.cache_data(show_spinner="Cargando datos…")
def cargar_datos():
    if not RUTA_CSV.exists():
        return None
    df = pd.read_csv(RUTA_CSV)
    df["Release Date"] = pd.to_datetime(df["Release Date"])
    df["Year"] = df["Release Date"].dt.year
    if "Grupo_Duracion" not in df.columns:
        df["Grupo_Duracion"] = pd.cut(
            df["Duration"], bins=[119, 164, 209, 254, 300], labels=ORDEN_DUR)
    if "Grupo_Popularidad" not in df.columns:
        df["Grupo_Popularidad"] = pd.cut(
            df["Popularity"], bins=[0, 25, 50, 75, 100],
            labels=ORDEN_POP, include_lowest=True)
    df["Grupo_Duracion"] = df["Grupo_Duracion"].astype(str)
    df["Grupo_Popularidad"] = df["Grupo_Popularidad"].astype(str)
    return df

def pagina_resumen(f, df):
    encabezado("Resumen general",
               "Vista rápida de la colección según los filtros activos.")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Canciones", f"{len(f):,}")
    c2.metric("Popularidad media", f"{f['Popularity'].mean():.1f}")
    c3.metric("Duración media", formato_duracion(f["Duration"].mean()))
    c4.metric("Géneros", f["Genre"].nunique())
    c5.metric("Años", f"{f['Year'].min()}–{f['Year'].max()}")

    st.write("")
    pop_gen = f.groupby("Genre")["Popularity"].mean().sort_values(ascending=False)
    anual = f.groupby("Year")["Popularity"].mean()

    col_a, col_b = st.columns(2)
    with col_a:
        if len(pop_gen) > 1:
            tarjeta("Popularidad por género",
                    f"<b>{pop_gen.index[0]}</b> lidera con {pop_gen.iloc[0]:.1f} y "
                    f"<b>{pop_gen.index[-1]}</b> cierra con {pop_gen.iloc[-1]:.1f}. "
                    f"La diferencia entre ambos es de solo {pop_gen.iloc[0] - pop_gen.iloc[-1]:.1f} puntos.")
        else:
            tarjeta("Popularidad por género",
                    f"Con un solo género seleccionado ({pop_gen.index[0]}) "
                    f"la popularidad media es {pop_gen.iloc[0]:.1f}.")
    with col_b:
        tarjeta("Año más popular",
                f"<b>{int(anual.idxmax())}</b> tiene la popularidad media más alta "
                f"({anual.max():.1f}) y <b>{int(anual.idxmin())}</b> la más baja ({anual.min():.1f}).")

    col_c, col_d = st.columns(2)
    with col_c:
        por_genero = f["Genre"].value_counts().reset_index()
        por_genero.columns = ["Género", "Canciones"]
        fig = px.bar(por_genero, x="Canciones", y="Género", orientation="h",
                     color_discrete_sequence=[MENTA], title="Canciones por género")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        mostrar(fig, 380)
    with col_d:
        grupos = conteo_ordenado(f["Grupo_Popularidad"], ORDEN_POP, "Grupo")
        fig = px.pie(grupos, names="Grupo", values="Canciones", hole=0.55,
                     color="Grupo",
                     color_discrete_map={"Baja": LILA, "Media": ARENA,
                                         "Alta": AMBAR, "Muy Alta": MENTA},
                     category_orders={"Grupo": ORDEN_POP},
                     title="Canciones por nivel de popularidad")
        fig.update_traces(textinfo="percent", sort=False)
        mostrar(fig, 380)


def pagina_distribuciones(f, df):
    encabezado("Distribuciones",
               "Cómo se reparten la popularidad y la duración, y si hay valores atípicos.")

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.histogram(f, x="Popularity", nbins=30, color_discrete_sequence=[MENTA],
                           title="Distribución de la popularidad",
                           labels={"Popularity": "Popularidad", "count": "Canciones"})
        mostrar(fig, 340)
    with col_b:
        fig = px.histogram(f, x="Duration", nbins=30, color_discrete_sequence=[AMBAR],
                           title="Distribución de la duración",
                           labels={"Duration": "Duración (segundos)", "count": "Canciones"})
        mostrar(fig, 340)

    col_c, col_d = st.columns(2)
    with col_c:
        fig = px.box(f, x="Popularity", color_discrete_sequence=[MENTA],
                     title="Valores atípicos en popularidad",
                     labels={"Popularity": "Popularidad"})
        mostrar(fig, 280)
    with col_d:
        fig = px.box(f, x="Duration", color_discrete_sequence=[AMBAR],
                     title="Valores atípicos en duración",
                     labels={"Duration": "Duración (segundos)"})
        mostrar(fig, 280)

    col_e, col_f = st.columns(2)
    with col_e:
        fig = px.bar(conteo_ordenado(f["Grupo_Popularidad"], ORDEN_POP, "Grupo"),
                     x="Grupo", y="Canciones", color_discrete_sequence=[MENTA],
                     title="Canciones por grupo de popularidad")
        mostrar(fig, 320)
    with col_f:
        fig = px.bar(conteo_ordenado(f["Grupo_Duracion"], ORDEN_DUR, "Grupo"),
                     x="Grupo", y="Canciones", color_discrete_sequence=[AMBAR],
                     title="Canciones por grupo de duración")
        mostrar(fig, 320)

    fig = px.density_heatmap(f, x="Duration", y="Popularity", nbinsx=30, nbinsy=20,
                             color_continuous_scale=ESCALA_MENTA,
                             title="Relación entre duración y popularidad",
                             labels={"Duration": "Duración (segundos)",
                                     "Popularity": "Popularidad"})
    mostrar(fig, 420)


def pagina_generos(f, df):
    encabezado("Géneros musicales",
               "Comparación del volumen y la popularidad entre géneros.")

    col_a, col_b = st.columns(2)
    with col_a:
        por_genero = f["Genre"].value_counts().reset_index()
        por_genero.columns = ["Género", "Canciones"]
        fig = px.bar(por_genero, x="Canciones", y="Género", orientation="h",
                     color_discrete_sequence=[MENTA], title="Canciones por género")
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        mostrar(fig, 380)
    with col_b:
        pop_genero = f.groupby("Genre")["Popularity"].mean().sort_values().reset_index()
        pop_genero.columns = ["Género", "Popularidad media"]
        fig = px.bar(pop_genero, x="Popularidad media", y="Género", orientation="h",
                     range_x=[0, 100], color_discrete_sequence=[AMBAR],
                     title="Popularidad media por género")
        mostrar(fig, 380)

    fig = px.box(f, x="Genre", y="Popularity", color_discrete_sequence=[MENTA],
                 title="Dispersión de la popularidad por género",
                 labels={"Genre": "Género", "Popularity": "Popularidad"})
    mostrar(fig, 380)

    cruce = pd.crosstab(f["Genre"], f["Grupo_Popularidad"], normalize="index") * 100
    cruce = cruce.reindex(columns=[c for c in ORDEN_POP if c in cruce.columns])
    fig = px.imshow(cruce, text_auto=".1f", aspect="auto",
                    color_continuous_scale=ESCALA_MENTA,
                    title="% de canciones por nivel de popularidad en cada género",
                    labels={"x": "Nivel de popularidad", "y": "Género", "color": "%"})
    mostrar(fig, 420)

    st.subheader("Resumen estadístico por género")
    resumen = (f.groupby("Genre")
               .agg(Canciones=("Title", "count"),
                    Popularidad_media=("Popularity", "mean"),
                    Popularidad_mediana=("Popularity", "median"),
                    Duracion_media_seg=("Duration", "mean"))
               .round(2).sort_values("Canciones", ascending=False))
    mostrar_tabla(resumen)


def pagina_tiempo(f, df):
    encabezado("Tendencia temporal",
               "Evolución de la producción y la popularidad a lo largo de los años.")

    por_anio = (f.groupby("Year")
                .agg(Canciones=("Title", "count"),
                     Popularidad=("Popularity", "mean"),
                     Duracion=("Duration", "mean"))
                .round(2).reset_index())

    fig = px.line(por_anio, x="Year", y="Canciones", markers=True, text="Canciones",
                  color_discrete_sequence=[MENTA],
                  title="Canciones por año de lanzamiento",
                  labels={"Year": "Año"})
    fig.update_traces(mode="lines+markers+text", texttemplate="%{text:,}",
                      textposition="top center", textfont=dict(size=12, color=TEXTO),
                      cliponaxis=False)
    fig.update_xaxes(dtick=1, tickformat="d")
    fig.update_yaxes(range=[0, por_anio["Canciones"].max() * 1.25])
    mostrar(fig, 420)

    fig = px.line(por_anio, x="Year", y="Popularidad", markers=True, text="Popularidad",
                  color_discrete_sequence=[AMBAR],
                  title="Popularidad media por año",
                  labels={"Year": "Año", "Popularidad": "Popularidad media"})
    fig.update_traces(mode="lines+markers+text", texttemplate="%{text:.1f}",
                      textposition="top center", textfont=dict(size=12, color=TEXTO),
                      cliponaxis=False)
    fig.update_xaxes(dtick=1, tickformat="d")
    fig.update_yaxes(range=[0, 100])
    mostrar(fig, 420)

    st.subheader("Detalle por año")
    tabla_anio = pd.DataFrame({
        "Año": por_anio["Year"].astype(str),
        "Canciones": por_anio["Canciones"],
        "Popularidad media": por_anio["Popularidad"].round(2),
        "Duración media": [formato_duracion(x) for x in por_anio["Duracion"]],
    })
    mostrar_tabla(tabla_anio, altura=36 * (len(tabla_anio) + 1) + 3, ocultar_indice=True)

    st.subheader("Correlación entre variables")
    corr = f[["Duration", "Popularity", "Year"]].corr().round(2)
    nombres = ["Duración", "Popularidad", "Año"]
    corr.columns = nombres
    corr.index = nombres

    col_a, col_b = st.columns([3, 2])
    with col_a:
        fig = px.imshow(corr, text_auto=".2f", color_continuous_scale=ESCALA_DIVERGENTE,
                        zmin=-1, zmax=1, title="Mapa de calor de correlación")
        fig.update_traces(textfont_size=18)
        mostrar(fig, 420)
    with col_b:
        st.write("")
        st.write("")
        mostrar_tabla(corr.reset_index().rename(columns={"index": "Variable"}),
                      altura=3 * 36 + 3 + 36, ocultar_indice=True)
        st.caption("Valores cercanos a 0 indican que no hay relación lineal entre las variables.")

    st.subheader("Espectro de potencia de la duración")
    if HAY_SCIPY and len(f) > 10:
        senal = f.sort_values("Release Date")["Duration"].to_numpy()
        frecuencias, potencia = periodogram(senal)
        fig = px.line(x=frecuencias[1:], y=potencia[1:],
                      color_discrete_sequence=[LILA],
                      title="Periodograma de la duración (canciones ordenadas por fecha)",
                      labels={"x": "Frecuencia", "y": "Potencia"})
        mostrar(fig, 420)
        st.caption("Sin picos marcados: no hay ciclos periódicos en la duración, "
                   "lo que coincide con el comportamiento casi aleatorio del resto de los datos.")
    else:
        st.info("Para ver el espectro de potencia instala scipy: python -m pip install scipy")


def pagina_datos(f, df):
    encabezado("Explorador de datos",
               "Busca canciones y descarga los resultados filtrados.")

    busqueda = st.text_input("Buscar por título, artista o álbum",
                             placeholder="Ejemplo: Smith")
    resultado = f
    if busqueda:
        b = busqueda.strip().lower()
        mascara = (f["Title"].str.lower().str.contains(b, regex=False)
                   | f["Artist"].str.lower().str.contains(b, regex=False)
                   | f["Album"].str.lower().str.contains(b, regex=False))
        resultado = f[mascara]

    st.caption(f"{len(resultado):,} canciones encontradas (se muestran las primeras 1,000).")
    vista = resultado[["Title", "Artist", "Album", "Genre", "Release Date",
                       "Duration", "Popularity", "Grupo_Duracion",
                       "Grupo_Popularidad"]].head(1000).copy()
    vista["Release Date"] = vista["Release Date"].dt.date
    mostrar_tabla(vista, 480)

    st.download_button("Descargar resultados (CSV)",
                       resultado.to_csv(index=False).encode("utf-8"),
                       file_name="canciones_filtradas.csv", mime="text/csv")


def pagina_acerca(f, df):
    encabezado("Acerca de", "Información del proyecto y del conjunto de datos.")

    st.markdown(
        "**SoundLens** es un panel interactivo para explorar un conjunto de "
        f"**{len(df):,} canciones** lanzadas entre {df['Year'].min()} y {df['Year'].max()}. "
        "Los datos fueron limpiados y transformados previamente en un notebook de "
        "Jupyter (`practica2.ipynb`)."
    )

    st.subheader("Diccionario de datos")
    diccionario = pd.DataFrame({
        "Columna": ["Title", "Artist", "Album", "Genre", "Release Date", "Duration",
                    "Popularity", "Year", "Grupo_Duracion", "Grupo_Popularidad"],
        "Descripción": [
            "Título de la canción", "Artista", "Álbum", "Género musical",
            "Fecha de lanzamiento", "Duración en segundos (120 a 300)",
            "Popularidad (0 a 100)", "Año de lanzamiento (derivada)",
            "Rango de duración: 2:00-2:44, 2:45-3:29, 3:30-4:14, 4:15-5:00",
            "Nivel de popularidad: Baja, Media, Alta, Muy Alta"],
    })
    mostrar_tabla(diccionario)

    st.subheader("Cómo usar el panel")
    st.markdown(
        "1. Elige una sección en el menú de la izquierda.\n"
        "2. Ajusta los filtros: todas las gráficas y tablas se actualizan.\n"
        "3. Usa **Restablecer filtros** para volver a la vista completa."
    )
    st.info("Nota: el conjunto de datos parece generado de forma sintética "
            "(títulos y artistas aleatorios, distribuciones casi uniformes), "
            "por eso las diferencias entre géneros y años son mínimas.")

PAGINAS = {
    "Resumen": pagina_resumen,
    "Distribuciones": pagina_distribuciones,
    "Géneros": pagina_generos,
    "Tendencia temporal": pagina_tiempo,
    "Explorador de datos": pagina_datos,
    "Acerca de": pagina_acerca,
}


def barra_lateral(df):
    generos = sorted(df["Genre"].unique())
    a_min, a_max = int(df["Year"].min()), int(df["Year"].max())
    d_min, d_max = int(df["Duration"].min()), int(df["Duration"].max())

    por_defecto = {
        "f_generos": generos,
        "f_anios": (a_min, a_max),
        "f_dur": (d_min, d_max),
        "f_pop": (0, 100),
    }
    for clave, valor in por_defecto.items():
        st.session_state.setdefault(clave, valor)

    def restablecer():
        for clave, valor in por_defecto.items():
            st.session_state[clave] = valor

    with st.sidebar:
        st.markdown('<div class="marca">Sound<span>Lens</span></div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="sub-marca">Panel de análisis musical 2000-2020</div>',
                    unsafe_allow_html=True)

        pagina = st.radio("Navegación", list(PAGINAS.keys()),
                          label_visibility="collapsed")

        st.divider()
        st.markdown("**Filtros**")
        st.multiselect("Género musical", generos, key="f_generos")
        st.slider("Año de lanzamiento", a_min, a_max, key="f_anios")
        st.slider("Duración (segundos)", d_min, d_max, key="f_dur")
        st.slider("Popularidad", 0, 100, key="f_pop")
        st.button("Restablecer filtros", on_click=restablecer)

    filtrado = df[
        df["Genre"].isin(st.session_state["f_generos"])
        & df["Year"].between(*st.session_state["f_anios"])
        & df["Duration"].between(*st.session_state["f_dur"])
        & df["Popularity"].between(*st.session_state["f_pop"])
    ]

    with st.sidebar:
        st.caption(f"Mostrando {len(filtrado):,} de {len(df):,} canciones")

    return pagina, filtrado


def main():
    df = cargar_datos()
    if df is None:
        st.error(f"No se encontró el archivo **{RUTA_CSV.name}**.")
        st.write("Colócalo en la misma carpeta que `app.py` "
                 "(se genera al ejecutar el notebook `practica2.ipynb`).")
        st.stop()

    pagina, filtrado = barra_lateral(df)

    if filtrado.empty:
        st.warning("No hay canciones con los filtros seleccionados. "
                   "Ajusta los filtros o pulsa «Restablecer filtros».")
        st.stop()

    PAGINAS[pagina](filtrado, df)


main()