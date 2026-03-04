"""
app.py  —  Projet BI · TD 01
==============================
Architecture :
  etl_build_views.py  →  vue_*.csv  →  app.py (lecture seule)

Lancement :
  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Projet BI — TD 01",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════════════════════
# CSS GLOBAL
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    h1, h2, h3 { font-family: 'IBM Plex Mono', monospace; }

    .stApp { background-color: #0f1117; color: #e8e8e0; }
    .stSidebar { background-color: #161b22 !important; border-right: 1px solid #30363d; }

    .kpi-card {
        background: linear-gradient(135deg, #1c2128, #21262d);
        border: 1px solid #30363d;
        border-left: 4px solid #58a6ff;
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 12px;
    }
    .kpi-card.orange { border-left-color: #f78166; }
    .kpi-card.green  { border-left-color: #3fb950; }
    .kpi-card.purple { border-left-color: #bc8cff; }
    .kpi-card.gold   { border-left-color: #d29922; }

    .kpi-label {
        font-size: 11px; text-transform: uppercase;
        letter-spacing: 1.5px; color: #8b949e; margin-bottom: 6px;
    }
    .kpi-value {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 22px; font-weight: 600; color: #e6edf3;
    }
    .kpi-sub { color: #3fb950; font-size: 13px; margin-top: 5px; }

    .section-header {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 13px; text-transform: uppercase;
        letter-spacing: 2px; color: #58a6ff;
        border-bottom: 1px solid #21262d;
        padding-bottom: 8px; margin: 28px 0 18px 0;
    }

    .info-box {
        background: #161b22; border-left: 3px solid #58a6ff;
        border-radius: 6px; padding: 10px 14px;
        color: #8b949e; font-size: 12px; margin: 8px 0;
    }
    .warn-box {
        background: #2d1f00; border-left: 3px solid #e3b341;
        border-radius: 6px; padding: 10px 14px;
        color: #e3b341; font-size: 13px; margin: 8px 0;
    }

    div[data-testid="stDataFrame"] { border: 1px solid #30363d; border-radius: 6px; }
    .stSelectbox label, .stMultiSelect label,
    .stDateInput label, .stRadio label {
        color: #8b949e !important; font-size: 12px !important;
    }

    /* Navigation radio buttons styled as tabs */
    div[data-testid="stSidebar"] .stRadio > div {
        gap: 6px;
    }
    div[data-testid="stSidebar"] .stRadio label {
        background: #21262d;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 8px 14px;
        cursor: pointer;
        font-size: 13px !important;
        color: #e8e8e0 !important;
        display: block;
        width: 100%;
    }
    div[data-testid="stSidebar"] .stRadio label:hover {
        background: #30363d;
    }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ══════════════════════════════════════════════════════════════════════════════
DARK   = dict(template="plotly_dark")
LAYOUT = dict(
    paper_bgcolor="#0f1117", plot_bgcolor="#161b22",
    font_color="#e8e8e0", margin=dict(l=0, r=0, t=40, b=0)
)
LAYOUT_NOAXIS = dict(paper_bgcolor="#0f1117", font_color="#e8e8e0",
                     margin=dict(l=0, r=0, t=40, b=0))

ORDRE_MOIS = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]

CHART_TYPES = ["Barres", "Barres empilees", "Lignes", "Aires", "Camembert", "Treemap"]


def fmt(v, suffix=" DA"):
    """Formate un nombre en K / M pour l'affichage."""
    try:
        v = float(v)
        if abs(v) >= 1_000_000:
            return f"{v/1_000_000:.2f}M{suffix}"
        elif abs(v) >= 1_000:
            return f"{v/1_000:.1f}K{suffix}"
        return f"{v:.2f}{suffix}"
    except Exception:
        return str(v)


def kpi(label, value, color=""):
    st.markdown(
        f'<div class="kpi-card {color}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def section(title):
    st.markdown(f'<p class="section-header">{title}</p>', unsafe_allow_html=True)


def make_chart(df, x, y, color, chart_type, facet=None):
    """Cree un graphe Plotly selon le type choisi."""
    kwargs = dict(**DARK)
    if chart_type == "Barres":
        fig = px.bar(df, x=x, y=y, color=color, barmode="group", **kwargs)
    elif chart_type == "Barres empilees":
        fig = px.bar(df, x=x, y=y, color=color, barmode="stack", **kwargs)
    elif chart_type == "Lignes":
        fig = px.line(df, x=x, y=y, color=color, markers=True, **kwargs)
    elif chart_type == "Aires":
        fig = px.area(df, x=x, y=y, color=color, **kwargs)
    elif chart_type == "Camembert":
        fig = px.pie(df, names=x, values=y, **kwargs)
        fig.update_layout(**LAYOUT_NOAXIS)
        return fig
    elif chart_type == "Treemap":
        path = [x] if color is None else [x, color]
        fig = px.treemap(df, path=path, values=y, **kwargs)
        fig.update_layout(**LAYOUT_NOAXIS)
        return fig
    else:
        fig = px.bar(df, x=x, y=y, color=color, barmode="group", **kwargs)

    if facet and facet in df.columns:
        fig = px.bar(df, x=x, y=y, color=color, barmode="group",
                     facet_col=facet, **DARK)

    fig.update_layout(**LAYOUT, yaxis=dict(tickformat=".2s"))
    return fig


def apply_filters(df, date_col, date_range, filters: dict):
    """Applique les filtres date + colonnes sur un dataframe."""
    if len(date_range) == 2:
        df = df[
            (df[date_col] >= pd.to_datetime(date_range[0])) &
            (df[date_col] <= pd.to_datetime(date_range[1]))
        ]
    for col, vals in filters.items():
        if vals:
            df = df[df[col].isin(vals)]
    return df


# ══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT DES VUES  (lecture seule — ETL deja fait dans etl_build_views.py)
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_views():
    try:
        ventes  = pd.read_csv("vue_fait_ventes.csv",  parse_dates=["Date.CMD"])
        achats  = pd.read_csv("vue_fait_achats.csv",  parse_dates=["Date.CMD"])
        marges  = pd.read_csv("vue_fait_marges.csv",  parse_dates=["Date.CMD"])
        pmp     = pd.read_csv("vue_agg_pmp.csv")
        chrono  = pd.read_csv("vue_pmp_chrono.csv",   parse_dates=["Date.CMD"])

        for df in [ventes, achats, marges]:
            if "Nom Mois" in df.columns:
                df["Nom Mois"] = pd.Categorical(
                    df["Nom Mois"], categories=ORDRE_MOIS, ordered=True
                )
        return ventes, achats, marges, pmp, chrono, None

    except FileNotFoundError as e:
        return None, None, None, None, None, str(e)


ventes_full, achats_full, marges_full, pmp_df, pmp_chrono, err = load_views()

if err:
    st.error(
        "Vues introuvables. Lancez d'abord : `python etl_build_views.py`\n\n"
        f"Detail : {err}"
    )
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
st.sidebar.markdown("## Projet BI — TD 01")
st.sidebar.markdown("---")

partie = st.sidebar.radio(
    "Choisir une partie",
    ["Partie 01 — Ventes", "Partie 02 — Achats", "Partie 03 — Marges"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<div class="info-box">Donnees chargees depuis les vues pre-calculees.<br>'
    'Pour mettre a jour : relancer <code>etl_build_views.py</code></div>',
    unsafe_allow_html=True
)


# ══════════════════════════════════════════════════════════════════════════════
# PARTIE 01 — ANALYSE DES VENTES
# ══════════════════════════════════════════════════════════════════════════════
if partie == "Partie 01 — Ventes":

    st.markdown("## Analyse des Ventes — Partie 01")
    st.markdown(
        "<p style='color:#8b949e;font-size:13px;margin-top:-12px;'>"
        "Tableau de bord dynamique · Chiffre d'Affaires & Quantites Vendues</p>",
        unsafe_allow_html=True
    )

    # ── Filtres sidebar ──────────────────────────────────────────────────────
    st.sidebar.markdown("### Filtres Globaux")

    date_range = st.sidebar.date_input(
        "Periode",
        [ventes_full["Date.CMD"].min(), ventes_full["Date.CMD"].max()],
        key="v_date"
    )
    sel_annees  = st.sidebar.multiselect("Annee(s)",
        sorted(ventes_full["Année"].unique()),
        default=sorted(ventes_full["Année"].unique()), key="v_ann")
    sel_types   = st.sidebar.multiselect("Type(s) de Vente",
        sorted(ventes_full["Type Vente"].unique()),
        default=sorted(ventes_full["Type Vente"].unique()), key="v_tv")
    sel_wilayas = st.sidebar.multiselect("Wilaya(s)",
        sorted(ventes_full["Wilaya"].unique()),
        default=sorted(ventes_full["Wilaya"].unique()), key="v_wil")
    sel_cats    = st.sidebar.multiselect("Categorie(s) Produit",
        sorted(ventes_full["Catégorie Produit"].unique()),
        default=sorted(ventes_full["Catégorie Produit"].unique()), key="v_cat")
    sel_formes  = st.sidebar.multiselect("Forme(s) Juridique",
        sorted(ventes_full["Forme Juridique"].unique()),
        default=sorted(ventes_full["Forme Juridique"].unique()), key="v_fj")

    df = apply_filters(ventes_full, "Date.CMD", date_range, {
        "Année": sel_annees, "Type Vente": sel_types,
        "Wilaya": sel_wilayas, "Catégorie Produit": sel_cats,
        "Forme Juridique": sel_formes
    })

    # ── KPIs ─────────────────────────────────────────────────────────────────
    section("Indicateurs Globaux")
    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi("Chiffre d'Affaires HT",  fmt(df["Montant HT"].sum()))
    with k2: kpi("Montant TTC Total",       fmt(df["Montant TTC"].sum()), "orange")
    with k3: kpi("Quantites Vendues",       f"{int(df['Qte'].sum()):,}", "green")
    with k4:
        best = df.groupby("Catégorie Produit")["Montant HT"].sum().idxmax() if not df.empty else "—"
        kpi("Categorie + Rentable", best, "purple")

    # ── Analyse dynamique ─────────────────────────────────────────────────────
    section("Analyse Dynamique")

    DIMS_V = ["Produit", "Catégorie Produit", "Client", "Forme Juridique",
              "Type Vente", "Wilaya", "Nom Mois", "Année"]
    IND_V  = {"Montant HT": "CA HT (DA)", "Montant TTC": "CA TTC (DA)", "Qte": "Quantite vendue"}

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        dims = st.multiselect("Parametres d'analyse", DIMS_V,
                              default=["Catégorie Produit", "Type Vente"], key="v_dims")
    with col2:
        ind = st.selectbox("Indicateur", list(IND_V.keys()),
                           format_func=lambda x: IND_V[x], key="v_ind")
    with col3:
        chart = st.selectbox("Type de graphe", CHART_TYPES, key="v_chart")

    if dims:
        res = df.groupby(dims)[ind].sum().reset_index()
        t1, t2 = st.tabs(["Graphe", "Tableau"])
        with t1:
            fig = make_chart(res, dims[0], ind,
                             dims[1] if len(dims) > 1 else None, chart)
            st.plotly_chart(fig, use_container_width=True)
        with t2:
            st.dataframe(res.sort_values(ind, ascending=False), use_container_width=True)

    # ── Q1 : Produits vendus apres une date ───────────────────────────────────
    section("Q1 — Produits vendus apres une date")

    date_q1 = st.date_input("Date de reference",
                             value=pd.to_datetime("2025-02-01"), key="v_q1")
    df_q1 = df[df["Date.CMD"] > pd.to_datetime(date_q1)]

    if df_q1.empty:
        st.info("Aucune vente apres cette date avec les filtres actifs.")
    else:
        produits_q1 = (
            df_q1.groupby(["Code Produit", "Produit", "Catégorie Produit"])
            .agg(Qte_Vendue=("Qte", "sum"), CA_HT=("Montant HT", "sum"))
            .reset_index().sort_values("CA_HT", ascending=False)
        )
        c1, c2 = st.columns(2)
        with c1:
            st.dataframe(produits_q1, use_container_width=True)
        with c2:
            fig = px.bar(produits_q1, x="Produit", y="Qte_Vendue",
                         color="Catégorie Produit",
                         title=f"Quantites vendues apres le {date_q1}", **DARK)
            fig.update_layout(**LAYOUT, xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)

    # ── Q2 : Classement produits par CA, type vente, annee ────────────────────
    section("Q2 — Classement produits par CA / type vente / annee")

    ind_q2 = st.radio("Indicateur", ["Montant HT", "Montant TTC"],
                       horizontal=True, key="v_q2ind")

    ranking = (
        df.groupby(["Produit", "Catégorie Produit", "Type Vente", "Année"])[ind_q2]
        .sum().reset_index().sort_values(ind_q2, ascending=False)
    )
    c1, c2 = st.columns([1, 2])
    with c1:
        st.dataframe(ranking, use_container_width=True)
    with c2:
        fig = px.bar(ranking, x="Produit", y=ind_q2,
                     color="Type Vente", facet_col="Année",
                     barmode="group",
                     title="Classement produits par CA et type vente", **DARK)
        fig.update_layout(**LAYOUT, xaxis_tickangle=-30,
                          yaxis=dict(tickformat=".2s"))
        st.plotly_chart(fig, use_container_width=True)

    # ── Q3 : Classement clients par wilaya & forme juridique ──────────────────
    section("Q3 — Classement clients par wilaya & forme juridique")

    ind_q3 = st.radio("Indicateur", ["Montant TTC", "Montant HT", "Qte"],
                       horizontal=True, key="v_q3ind")

    ranking_c = (
        df.groupby(["Client", "Wilaya", "Forme Juridique"])[ind_q3]
        .sum().reset_index().sort_values(ind_q3, ascending=False)
    )
    c1, c2 = st.columns([1, 2])
    with c1:
        st.dataframe(ranking_c, use_container_width=True)
    with c2:
        fig = px.bar(ranking_c, x="Client", y=ind_q3,
                     color="Wilaya", facet_col="Forme Juridique",
                     barmode="stack",
                     title="CA par client, wilaya et forme juridique", **DARK)
        fig.update_layout(**LAYOUT, xaxis_tickangle=-20,
                          yaxis=dict(tickformat=".2s"))
        st.plotly_chart(fig, use_container_width=True)

    # ── Q4 : Ventes quantitatives par produit / categorie / type / mois / annee
    section("Q4 — Ventes quantitatives par produit / type / mois / annee")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        q4_x = st.selectbox("Axe X",
            ["Nom Mois", "Produit", "Catégorie Produit", "Année"], key="v_q4x")
    with col_b:
        q4_c = st.selectbox("Couleur par",
            ["Type Vente", "Catégorie Produit", "Wilaya", "Année"], key="v_q4c")
    with col_c:
        q4_f = st.selectbox("Facette",
            ["Aucune", "Année", "Type Vente", "Catégorie Produit"], key="v_q4f")

    grp = list({q4_x, q4_c})
    if q4_f != "Aucune":
        grp = list(set(grp + [q4_f]))

    res_q4 = df.groupby(grp)["Qte"].sum().reset_index()
    fig = px.bar(res_q4, x=q4_x, y="Qte",
                 color=q4_c if q4_c in res_q4.columns else None,
                 facet_col=q4_f if q4_f != "Aucune" and q4_f in res_q4.columns else None,
                 barmode="group", title="Quantites vendues", **DARK)
    fig.update_layout(**LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    # ── Q5 : Categorie la plus rentable ───────────────────────────────────────
    section("Q5 — Categorie de produit la plus rentable")

    ind_q5 = st.radio("Indicateur", ["Montant TTC", "Montant HT"],
                       horizontal=True, key="v_q5ind")
    cat_profit = (
        df.groupby("Catégorie Produit")[ind_q5].sum().reset_index()
        .sort_values(ind_q5, ascending=False)
    )
    if not cat_profit.empty:
        best = cat_profit.iloc[0]
        st.markdown(
            f'<div class="kpi-card" style="max-width:400px;margin-bottom:20px;">'
            f'<div class="kpi-label">Categorie la plus rentable</div>'
            f'<div class="kpi-value">{best["Catégorie Produit"]}</div>'
            f'<div class="kpi-sub">{ind_q5} : {fmt(best[ind_q5])}</div>'
            f'</div>', unsafe_allow_html=True
        )
    c1, c2 = st.columns(2)
    with c1:
        fig = px.pie(cat_profit, names="Catégorie Produit", values=ind_q5,
                     title="Repartition du CA par categorie", hole=0.4, **DARK)
        fig.update_layout(**LAYOUT_NOAXIS)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(cat_profit, x="Catégorie Produit", y=ind_q5,
                     color="Catégorie Produit",
                     title="Classement des categories", **DARK)
        fig.update_layout(showlegend=False, **LAYOUT,
                          yaxis=dict(tickformat=".2s"))
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PARTIE 02 — ANALYSE DES ACHATS
# ══════════════════════════════════════════════════════════════════════════════
elif partie == "Partie 02 — Achats":

    st.markdown("## Analyse des Achats — Partie 02")
    st.markdown(
        "<p style='color:#8b949e;font-size:13px;margin-top:-12px;'>"
        "Tableau de bord dynamique · Couts & Quantites achetees</p>",
        unsafe_allow_html=True
    )

    # ── Filtres sidebar ──────────────────────────────────────────────────────
    st.sidebar.markdown("### Filtres Globaux")

    date_range = st.sidebar.date_input(
        "Periode",
        [achats_full["Date.CMD"].min(), achats_full["Date.CMD"].max()],
        key="a_date"
    )
    sel_fournisseurs = st.sidebar.multiselect("Fournisseur(s)",
        sorted(achats_full["Fournisseur"].unique()),
        default=sorted(achats_full["Fournisseur"].unique()), key="a_fou")
    sel_cats = st.sidebar.multiselect("Categorie(s) Produit",
        sorted(achats_full["Catégorie Produit"].unique()),
        default=sorted(achats_full["Catégorie Produit"].unique()), key="a_cat")
    sel_types = st.sidebar.multiselect("Type(s) Achat",
        sorted(achats_full["Type Achat"].unique()),
        default=sorted(achats_full["Type Achat"].unique()), key="a_typ")
    sel_annees = st.sidebar.multiselect("Annee(s)",
        sorted(achats_full["Année"].unique()),
        default=sorted(achats_full["Année"].unique()), key="a_ann")

    df = apply_filters(achats_full, "Date.CMD", date_range, {
        "Fournisseur": sel_fournisseurs, "Catégorie Produit": sel_cats,
        "Type Achat": sel_types, "Année": sel_annees
    })

    # ── KPIs ─────────────────────────────────────────────────────────────────
    section("Indicateurs Globaux")
    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi("Cout d'achat Total HT", fmt(df["Montant HT"].sum()))
    with k2: kpi("Montant TTC Total",     fmt(df["Montant TTC"].sum()), "orange")
    with k3: kpi("Quantites Achetees",    f"{int(df['QTY'].sum()):,}", "green")
    with k4:
        best = df.groupby("Catégorie Produit")["Montant HT"].sum().idxmax() if not df.empty else "—"
        kpi("Categorie + Couteuse", best, "purple")

    # ── Analyse dynamique ─────────────────────────────────────────────────────
    section("Analyse Dynamique")

    DIMS_A = ["Produit", "Catégorie Produit", "Fournisseur",
              "Forme Juridique", "Type Achat", "Nom Mois", "Année"]
    IND_A  = {"Montant HT": "Cout HT (DA)", "Montant TTC": "Cout TTC (DA)", "QTY": "Quantite achetee"}

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        dims = st.multiselect("Parametres d'analyse", DIMS_A,
                              default=["Catégorie Produit", "Type Achat"], key="a_dims")
    with col2:
        ind = st.selectbox("Indicateur", list(IND_A.keys()),
                           format_func=lambda x: IND_A[x], key="a_ind")
    with col3:
        chart = st.selectbox("Type de graphe", CHART_TYPES, key="a_chart")

    if dims:
        res = df.groupby(dims)[ind].sum().reset_index()
        t1, t2 = st.tabs(["Graphe", "Tableau"])
        with t1:
            fig = make_chart(res, dims[0], ind,
                             dims[1] if len(dims) > 1 else None, chart)
            st.plotly_chart(fig, use_container_width=True)
        with t2:
            st.dataframe(res.sort_values(ind, ascending=False), use_container_width=True)

    # ── Q1 : Produits achetes par annee ───────────────────────────────────────
    section("Q1 — Produits achetes par annee")

    annee_q1 = st.selectbox("Choisir une annee",
                             sorted(achats_full["Année"].unique()), key="a_q1")
    df_q1 = achats_full[achats_full["Année"] == annee_q1]

    if df_q1.empty:
        st.info("Aucun achat pour cette annee.")
    else:
        prod_a = (
            df_q1.groupby(["Code Produit", "Produit", "Catégorie Produit"])
            .agg(QTY_Totale=("QTY", "sum"), Cout_HT=("Montant HT", "sum"))
            .reset_index()
        )
        c1, c2 = st.columns(2)
        with c1:
            st.dataframe(prod_a, use_container_width=True)
        with c2:
            fig = px.bar(prod_a, x="Produit", y="QTY_Totale",
                         color="Catégorie Produit",
                         title=f"Quantites achetees en {annee_q1}", **DARK)
            fig.update_layout(**LAYOUT, xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)

    # ── Q2 : Achats quantitatifs par type / mois / annee ─────────────────────
    section("Q2 — Achats quantitatifs par produit / type / mois / annee")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        q2_x = st.selectbox("Axe X",
            ["Nom Mois", "Produit", "Catégorie Produit", "Année"], key="a_q2x")
    with col_b:
        q2_c = st.selectbox("Couleur par",
            ["Type Achat", "Catégorie Produit", "Fournisseur", "Année"], key="a_q2c")
    with col_c:
        q2_f = st.selectbox("Facette",
            ["Aucune", "Année", "Type Achat", "Catégorie Produit"], key="a_q2f")

    grp = list({q2_x, q2_c})
    if q2_f != "Aucune":
        grp = list(set(grp + [q2_f]))

    res_q2 = df.groupby(grp)["QTY"].sum().reset_index()
    fig = px.bar(res_q2, x=q2_x, y="QTY",
                 color=q2_c if q2_c in res_q2.columns else None,
                 facet_col=q2_f if q2_f != "Aucune" and q2_f in res_q2.columns else None,
                 barmode="group", title="Quantites achetees", **DARK)
    fig.update_layout(**LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    # ── Q3 : Classement fournisseurs par categorie ────────────────────────────
    section("Q3 — Classement fournisseurs par categorie produit")

    ind_q3 = st.radio("Indicateur", ["Montant HT", "Montant TTC", "QTY"],
                       horizontal=True, key="a_q3ind")
    ranking_f = (
        df.groupby(["Fournisseur", "Catégorie Produit", "Forme Juridique"])[ind_q3]
        .sum().reset_index().sort_values(ind_q3, ascending=False)
    )
    c1, c2 = st.columns([1, 2])
    with c1:
        st.dataframe(ranking_f, use_container_width=True)
    with c2:
        fig = px.bar(ranking_f, x="Fournisseur", y=ind_q3,
                     color="Catégorie Produit", barmode="stack",
                     title="Achats par fournisseur et categorie", **DARK)
        fig.update_layout(**LAYOUT, xaxis_tickangle=-20,
                          yaxis=dict(tickformat=".2s"))
        st.plotly_chart(fig, use_container_width=True)

    # ── Q4 : Categorie la plus couteuse ───────────────────────────────────────
    section("Q4 — Categorie de produit la plus couteuse")

    ind_q4 = st.radio("Indicateur", ["Montant HT", "Montant TTC"],
                       horizontal=True, key="a_q4ind")
    cat_cost = (
        df.groupby("Catégorie Produit")[ind_q4].sum().reset_index()
        .sort_values(ind_q4, ascending=False)
    )
    if not cat_cost.empty:
        best = cat_cost.iloc[0]
        st.markdown(
            f'<div class="kpi-card" style="max-width:400px;margin-bottom:20px;">'
            f'<div class="kpi-label">Categorie la plus couteuse</div>'
            f'<div class="kpi-value">{best["Catégorie Produit"]}</div>'
            f'<div class="kpi-sub">{ind_q4} : {fmt(best[ind_q4])}</div>'
            f'</div>', unsafe_allow_html=True
        )
    c1, c2 = st.columns(2)
    with c1:
        fig = px.pie(cat_cost, names="Catégorie Produit", values=ind_q4,
                     title="Repartition des couts par categorie", hole=0.4, **DARK)
        fig.update_layout(**LAYOUT_NOAXIS)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(cat_cost, x="Catégorie Produit", y=ind_q4,
                     color="Catégorie Produit",
                     title="Cout par categorie (classement)", **DARK)
        fig.update_layout(showlegend=False, **LAYOUT,
                          yaxis=dict(tickformat=".2s"))
        st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PARTIE 03 — ANALYSE DES MARGES
# ══════════════════════════════════════════════════════════════════════════════
elif partie == "Partie 03 — Marges":

    st.markdown("## Analyse des Marges — Partie 03")
    st.markdown(
        "<p style='color:#8b949e;font-size:13px;margin-top:-12px;'>"
        "Fusion Ventes & Achats · Prix Moyen Pondere · Marges dynamiques</p>",
        unsafe_allow_html=True
    )

    # Avertissement PMP = 0
    pmp_zero = marges_full[marges_full["PMP"] == 0]["Produit"].unique()
    if len(pmp_zero):
        st.markdown(
            f'<div class="warn-box">PMP = 0 DA — Taux de marge = 100% '
            f'(aucun achat enregistre) : {", ".join(pmp_zero)}</div>',
            unsafe_allow_html=True
        )

    # ── Filtres sidebar ──────────────────────────────────────────────────────
    st.sidebar.markdown("### Filtres Globaux")

    date_range = st.sidebar.date_input(
        "Periode",
        [marges_full["Date.CMD"].min(), marges_full["Date.CMD"].max()],
        key="m_date"
    )
    sel_produits = st.sidebar.multiselect("Produit(s)",
        sorted(marges_full["Produit"].unique()),
        default=sorted(marges_full["Produit"].unique()), key="m_pro")
    sel_cats = st.sidebar.multiselect("Categorie(s)",
        sorted(marges_full["Catégorie Produit"].unique()),
        default=sorted(marges_full["Catégorie Produit"].unique()), key="m_cat")
    sel_wilayas = st.sidebar.multiselect("Wilaya(s)",
        sorted(marges_full["Wilaya"].unique()),
        default=sorted(marges_full["Wilaya"].unique()), key="m_wil")
    sel_annees = st.sidebar.multiselect("Annee(s)",
        sorted(marges_full["Année"].unique()),
        default=sorted(marges_full["Année"].unique()), key="m_ann")

    df = apply_filters(marges_full, "Date.CMD", date_range, {
        "Produit": sel_produits, "Catégorie Produit": sel_cats,
        "Wilaya": sel_wilayas, "Année": sel_annees
    })

    # ── KPIs ─────────────────────────────────────────────────────────────────
    section("Indicateurs Globaux")
    ca     = df["Montant HT"].sum()
    cout   = df["Cout_Ligne"].sum()
    marge  = df["Marge_Totale"].sum()
    taux   = (marge / ca * 100) if ca > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi("Chiffre d'Affaires HT",     fmt(ca))
    with k2: kpi("Cout d'Achat (PMP x Qte)",  fmt(cout), "orange")
    with k3: kpi("Marge Brute Totale",         fmt(marge), "green" if marge >= 0 else "orange")
    with k4: kpi("Taux de Marge Global",       f"{taux:.1f}%", "purple")

    # ── Vue PMP ───────────────────────────────────────────────────────────────
    section("Prix Moyen Pondere (PMP) par Produit")
    st.caption("PMP = Somme(Montant HT achats) / Somme(QTY achetees), calcule chronologiquement")

    t1, t2 = st.tabs(["PMP Global", "PMP Cumulatif chronologique"])
    with t1:
        d = pmp_df.copy()
        d["PMP"]        = d["PMP"].apply(lambda v: fmt(v, " DA"))
        d["Cout_Total"] = d["Cout_Total"].apply(lambda v: fmt(v, " DA"))
        st.dataframe(d.rename(columns={
            "Cout_Total": "Cout Total Achats", "QTY_Totale": "QTY Totale",
            "Nb_Entrees": "Nb Entrees", "Premiere_Entree": "1ere Entree",
            "Derniere_Entree": "Derniere Entree"
        }), use_container_width=True)
    with t2:
        d2 = pmp_chrono.copy()
        for col in ["PU_Achat", "PMP_Cumul", "Cout_Cumul", "Montant HT"]:
            d2[col] = d2[col].apply(lambda v: fmt(v, ""))
        st.dataframe(d2.rename(columns={
            "PU_Achat": "Prix Unitaire Achat", "PMP_Cumul": "PMP Cumulatif",
            "Cout_Cumul": "Cout Cumulatif", "QTY_Cumul": "QTY Cumulee"
        }), use_container_width=True)

    # ── Analyse dynamique marges ───────────────────────────────────────────────
    section("Analyse Dynamique des Marges")

    DIMS_M = ["Produit", "Catégorie Produit", "Wilaya", "Nom Mois", "Année", "Type Vente"]
    IND_M  = {
        "Marge_Totale":   "Marge Totale (DA)",
        "Marge_Unitaire": "Marge Unitaire (DA)",
        "Taux_Marge":     "Taux de Marge (%)",
        "Montant HT":     "CA HT (DA)",
        "Cout_Ligne":     "Cout Achat (DA)",
        "Qte":            "Quantite vendue",
    }

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        dims = st.multiselect("Parametres d'analyse", DIMS_M,
                              default=["Catégorie Produit", "Année"], key="m_dims")
    with col2:
        ind = st.selectbox("Indicateur", list(IND_M.keys()),
                           format_func=lambda x: IND_M[x], key="m_ind")
    with col3:
        chart = st.selectbox("Type de graphe", CHART_TYPES, key="m_chart")

    if dims:
        agg_f = "mean" if ind in ["Marge_Unitaire", "Taux_Marge"] else "sum"
        res = df.groupby(dims)[ind].agg(agg_f).reset_index()
        t1, t2 = st.tabs(["Graphe", "Tableau"])
        with t1:
            fig = make_chart(res, dims[0], ind,
                             dims[1] if len(dims) > 1 else None, chart)
            # Colorer les marges negatives en rouge
            if ind in ["Marge_Totale", "Marge_Unitaire"] and chart in ["Barres", "Barres empilees"]:
                fig.update_traces(marker_color=[
                    "#f78166" if v < 0 else "#3fb950" for v in res[ind]
                ])
            st.plotly_chart(fig, use_container_width=True)
        with t2:
            disp = res.copy()
            if ind in ["Marge_Totale", "Marge_Unitaire", "Montant HT", "Cout_Ligne"]:
                disp[ind] = disp[ind].apply(lambda v: fmt(v, " DA"))
            elif ind == "Taux_Marge":
                disp[ind] = disp[ind].map("{:.2f}%".format)
            st.dataframe(disp.sort_values(res.columns[-1], ascending=False),
                         use_container_width=True)

    # ── Tableau detail ─────────────────────────────────────────────────────────
    section("Detail des Marges par Ligne de Vente")

    cols = ["Num.CMD", "Date.CMD", "Produit", "Catégorie Produit",
            "Wilaya", "Qte", "PU_Vente", "PMP", "Marge_Unitaire",
            "Marge_Totale", "Taux_Marge"]
    det = df[cols].copy()
    for c in ["PU_Vente", "PMP", "Marge_Unitaire", "Marge_Totale"]:
        det[c] = det[c].apply(lambda v: fmt(v, ""))
    det["Taux_Marge"] = det["Taux_Marge"].map("{:.1f}%".format)
    st.dataframe(det.rename(columns={
        "PU_Vente": "Prix Vente Unit.", "PMP": "PMP (Cout Unit.)",
        "Marge_Unitaire": "Marge Unit.", "Marge_Totale": "Marge Totale",
        "Taux_Marge": "Taux Marge"
    }), use_container_width=True)

    # ── Classement produits ────────────────────────────────────────────────────
    section("Classement Produits par Marge")

    prod_m = df.groupby(["Code Produit", "Produit", "Catégorie Produit"]).agg(
        CA_HT        =("Montant HT",    "sum"),
        Qte_Vendue   =("Qte",           "sum"),
        Marge_Totale =("Marge_Totale",  "sum"),
        Taux_Marge   =("Taux_Marge",    "mean"),
    ).reset_index().sort_values("Marge_Totale", ascending=False)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(prod_m, x="Produit", y="Marge_Totale",
                     color="Catégorie Produit",
                     title="Marge Totale par Produit", **DARK)
        fig.update_layout(**LAYOUT, xaxis_tickangle=-30,
                          yaxis=dict(tickformat=".2s"))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(prod_m.sort_values("Taux_Marge", ascending=False),
                     x="Produit", y="Taux_Marge",
                     color="Catégorie Produit",
                     title="Taux de Marge (%) par Produit", **DARK)
        fig.update_layout(**LAYOUT, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)
