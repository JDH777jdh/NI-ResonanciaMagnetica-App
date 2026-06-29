# modules/insumos.py — GESTIÓN DE INSUMOS (Bodega Central)
import tempfile, os, calendar
from datetime import datetime
import pytz, streamlit as st
import pandas as pd
from norte_imagen_core import PDFNorteImagen, generar_id_documento, validar_pin

tz_chile = pytz.timezone("America/Santiago")

_CATEGORIAS = ["Contraste / Farmacológico","Descartable","Equipamiento Menor",
               "Protección Personal","Otros"]


def render(db, bucket, usuario: dict):
    tab1, tab2, tab3, tab4 = st.tabs([
        "📦 Stock Actual", "➕ Ajuste / Recepción",
        "📋 Movimientos", "📊 Informe Mensual",
    ])
    with tab1: _stock_actual(db, usuario)
    with tab2: _ajuste_stock(db, usuario)
    with tab3: _movimientos(db)
    with tab4: _informe_mensual(db, bucket, usuario)


# ── STOCK ACTUAL ──────────────────────────────────────────────────
@st.fragment(run_every=120)
def _stock_actual(db, usuario):
    filtro_cat = st.selectbox("Categoría:", ["Todas"] + _CATEGORIAS,
                               key="filt_cat_ins")
    try:
        query = db.collection("insumos")
        if filtro_cat != "Todas":
            query = query.where("categoria","==",filtro_cat)
        docs  = query.order_by("nombre").get()
    except Exception as e:
        st.error(f"Error: {e}"); return

    alertas = 0
    filas   = []
    for doc in docs:
        d = doc.to_dict()
        stock = int(d.get("stock_actual",0))
        minimo= int(d.get("stock_minimo",0))
        if stock <= minimo:
            alertas += 1
        filas.append({
            "ID": doc.id,
            "Insumo":     d.get("nombre",""),
            "Categoría":  d.get("categoria",""),
            "Stock":      stock,
            "Mín.":       minimo,
            "Unidad":     d.get("unidad","unidades"),
            "Estado":     ("🔴 Crítico" if stock == 0 else
                          "⚠️ Bajo" if stock <= minimo else "✅ OK"),
        })

    if alertas:
        st.markdown(
            f"<div style='background:#fef2f2;border:1px solid #fecaca;"
            f"border-radius:7px;padding:8px 12px;font-size:11px;color:#991b1b;"
            f"margin-bottom:8px'>⚠️ {alertas} insumo(s) bajo stock mínimo</div>",
            unsafe_allow_html=True,
        )

    if filas:
        df = pd.DataFrame(filas)
        # Color por estado
        def color_estado(val):
            if "Crítico" in str(val): return "color:#dc2626;font-weight:700"
            if "Bajo" in str(val):    return "color:#d97706;font-weight:700"
            return "color:#16a34a;font-weight:600"

        st.dataframe(
            df.drop(columns=["ID"]),
            use_container_width=True,
            hide_index=True, height=380,
        )
        st.caption(f"Total: {len(filas)} insumos registrados")
    else:
        st.info("Sin insumos registrados. Use la pestaña 'Ajuste / Recepción'.")


# ── AJUSTE / RECEPCIÓN ────────────────────────────────────────────
def _ajuste_stock(db, usuario: dict):
    rol = usuario.get("rol","")
    if rol not in ("tm","tm_coordinador","calidad","secretaria","owner"):
        st.warning("Sin permisos para ajustar stock."); return

    accion = st.radio("Acción:", ["Recepción de insumos","Ajuste de stock",
                                   "Alta de nuevo insumo"],
                       horizontal=True, key="accion_ins")

    if accion == "Alta de nuevo insumo":
        _alta_insumo(db, usuario); return

    # Buscar insumo existente
    try:
        docs   = db.collection("insumos").order_by("nombre").get()
        opts   = {doc.id: doc.to_dict().get("nombre","") for doc in docs}
    except Exception as e:
        st.error(f"Error: {e}"); return

    if not opts:
        st.info("Sin insumos. Cree uno con 'Alta de nuevo insumo'."); return

    sel_id = st.selectbox("Insumo:", list(opts.keys()),
                           format_func=lambda x: opts[x], key="ins_sel")
    try:
        ins_doc = db.collection("insumos").document(sel_id).get().to_dict() or {}
    except Exception:
        ins_doc = {}

    stock_act = int(ins_doc.get("stock_actual",0))
    st.markdown(
        f"<div style='background:#f8fafc;border:1px solid #e2e8f0;"
        f"border-radius:7px;padding:8px 12px;font-size:11px;margin-bottom:8px'>"
        f"Stock actual: <strong>{stock_act} {ins_doc.get('unidad','')}</strong>"
        f" · Mín: {ins_doc.get('stock_minimo',0)}</div>",
        unsafe_allow_html=True,
    )

    cantidad  = st.number_input("Cantidad:", min_value=1, step=1, key="ins_qty")
    proveedor = st.text_input("Proveedor / Referencia:", key="ins_prov") \
                if accion == "Recepción de insumos" else ""
    motivo    = st.text_input("Motivo del ajuste:", key="ins_motivo") \
                if accion == "Ajuste de stock" else ""
    pin       = st.text_input("PIN:", type="password", key="pin_ins",
                               label_visibility="visible")

    if st.button("💾 REGISTRAR", type="primary", use_container_width=True):
        if not validar_pin(pin, usuario.get("hash","")): 
            st.error("❌ PIN incorrecto."); return
        nuevo = (stock_act + cantidad if accion == "Recepción de insumos"
                 else max(0, stock_act - cantidad))
        ahora = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
        try:
            db.collection("insumos").document(sel_id).update({"stock_actual": nuevo})
            db.collection("movimientos_insumos").add({
                "insumo_id":   sel_id,
                "insumo":      opts[sel_id],
                "accion":      accion,
                "cantidad":    cantidad if accion == "Recepción de insumos" else -cantidad,
                "stock_post":  nuevo,
                "proveedor":   proveedor,
                "motivo":      motivo,
                "usuario":     usuario.get("nombre",""),
                "timestamp":   ahora,
            })
            st.success(f"✅ Stock actualizado: {nuevo} {ins_doc.get('unidad','')}")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")


def _alta_insumo(db, usuario: dict):
    st.markdown("---")
    nombre   = st.text_input("Nombre del insumo:", key="ins_new_nom")
    cat      = st.selectbox("Categoría:", _CATEGORIAS, key="ins_new_cat")
    unidad   = st.text_input("Unidad (ej: unidades, ml, caja):", key="ins_new_uni")
    stock_i  = st.number_input("Stock inicial:", min_value=0, step=1, key="ins_new_st")
    stock_m  = st.number_input("Stock mínimo:", min_value=0, step=1, key="ins_new_min")
    pin      = st.text_input("PIN:", type="password", key="pin_ins_new")

    if st.button("➕ CREAR INSUMO", type="primary", use_container_width=True):
        if not nombre.strip():
            st.error("Ingrese el nombre del insumo."); return
        if not validar_pin(pin, usuario.get("hash","")):
            st.error("❌ PIN incorrecto."); return
        try:
            ahora = datetime.now(tz_chile).strftime("%d/%m/%Y %H:%M:%S")
            db.collection("insumos").add({
                "nombre":        nombre.strip(),
                "categoria":     cat,
                "unidad":        unidad,
                "stock_actual":  stock_i,
                "stock_minimo":  stock_m,
                "creado_por":    usuario.get("nombre",""),
                "fecha_alta":    ahora,
            })
            st.success(f"✅ Insumo '{nombre}' creado correctamente.")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")


# ── MOVIMIENTOS ───────────────────────────────────────────────────
def _movimientos(db):
    filtro = st.text_input("🔍 Buscar insumo:", key="filt_mov",
                            label_visibility="collapsed",
                            placeholder="Buscar insumo…")
    try:
        docs = (db.collection("movimientos_insumos")
                  .order_by("timestamp", direction="DESCENDING")
                  .limit(100).get())
    except Exception as e:
        st.error(f"Error: {e}"); return

    filas = []
    for doc in docs:
        d = doc.to_dict()
        if filtro and filtro.lower() not in d.get("insumo","").lower():
            continue
        qty = int(d.get("cantidad",0))
        filas.append({
            "Fecha/Hora": d.get("timestamp",""),
            "Insumo":     d.get("insumo",""),
            "Acción":     d.get("accion",""),
            "Cantidad":   f"+{qty}" if qty > 0 else str(qty),
            "Stock post": d.get("stock_post",""),
            "Usuario":    d.get("usuario",""),
        })

    if filas:
        st.dataframe(pd.DataFrame(filas), use_container_width=True,
                     hide_index=True, height=350)
    else:
        st.info("Sin movimientos registrados.")


# ── INFORME MENSUAL ───────────────────────────────────────────────
def _informe_mensual(db, bucket, usuario: dict):
    ahora  = datetime.now(tz_chile)
    periodo = st.text_input("Período (ej: Junio 2026):",
                             value=ahora.strftime("%B %Y"), key="periodo_ins")
    pin    = st.text_input("PIN:", type="password", key="pin_ins_rpt")

    if st.button("📊 GENERAR INFORME PDF", type="primary", use_container_width=True):
        if not validar_pin(pin, usuario.get("hash","")):
            st.error("❌ PIN incorrecto."); return
        try:
            docs = (db.collection("movimientos_insumos")
                      .order_by("timestamp", direction="DESCENDING")
                      .limit(500).get())
            filas_pdf = [[d.to_dict().get("timestamp",""),
                          d.to_dict().get("insumo",""),
                          d.to_dict().get("accion",""),
                          str(d.to_dict().get("cantidad","")),
                          str(d.to_dict().get("stock_post",""))]
                         for d in docs]
        except Exception as e:
            st.error(f"Error: {e}"); return

        ahora_str = ahora.strftime("%d/%m/%Y %H:%M:%S")
        _, id_v, nombre_pdf = generar_id_documento(
            "INSUMOS", db, "", "",
        )
        pdf = PDFNorteImagen("INSUMOS", config={
            "id_verificacion": id_v,
            "periodo": periodo,
        })
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.section_title_dark("REGISTRO DE MOVIMIENTOS DE INSUMOS")
        pdf.tabla(
            ["Fecha/Hora","Insumo","Acción","Cantidad","Stock post"],
            filas_pdf,
            anchos=[38,60,38,22,22],
        )
        pdf.estampar_sello_digital(
            usuario.get("nombre",""), usuario.get("sis",""),
            usuario.get("rol","tm"), ahora_str,
        )
        pdf_bytes = pdf.compilar()
        st.download_button("⬇️ Descargar Informe PDF",
                           data=pdf_bytes, file_name=nombre_pdf,
                           mime="application/pdf", use_container_width=True)
