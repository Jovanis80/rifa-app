import streamlit as st
import pandas as pd
import os
import json
from fpdf import FPDF
from datetime import datetime

# ========================
# CONFIGURACIÓN DE PÁGINA
# ========================
st.set_page_config(page_title="Rifa", page_icon="🎟️")

DB_FILE = "rifa_db.json"
PRECIO = 3000
ADMIN_PASSWORD = "JVR_2026_SEGUR0"

# ========================
# BASE DE DATOS RESISTENTE
# ========================
def cargar():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=["numero", "nombre", "telefono", "estado"])
        guardar(df)
        return df
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            datos = json.load(f)
        df_cargado = pd.DataFrame(datos)
        if df_cargado.empty:
            return pd.DataFrame(columns=["numero", "nombre", "telefono", "estado"])
        return df_cargado.astype(str).fillna("")
    except Exception:
        return pd.DataFrame(columns=["numero", "nombre", "telefono", "estado"])

def guardar(df):
    datos_dict = df.to_dict(orient="records")
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(datos_dict, f, ensure_ascii=False, indent=4)

def exportar_excel(df):
    df.to_excel("compradores.xlsx", index=False)

# Carga inicial de datos
df = cargar()

# ========================
# GENERADOR DE PDF
# ========================
def generar_pdf(nombre, telefono, numeros):
    pdf = FPDF()
    pdf.add_page()

    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    total = PRECIO * len(numeros)

    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(180, 0, 0) 
    pdf.cell(0, 12, "J.V.R PREMIUM RIFA", ln=1, align="C")
    pdf.ln(5)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 7, f"Nombre: {nombre}", ln=1)
    pdf.cell(0, 7, f"Telefono: {telefono}", ln=1)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(180, 0, 0) 
    pdf.cell(0, 8, "NUMERO DE BOLETO", ln=1)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, " - ".join(numeros), ln=1)
    pdf.ln(4)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, f"Fecha: {fecha_actual}", ln=1)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 7, f"Total pagado: ${total}", ln=1)
    pdf.ln(5)

    pdf.cell(0, 6, "Premio principal:", ln=1)
    pdf.cell(0, 6, "Televisor Smart TV Sankey 42 pulgadas", ln=1)
    pdf.cell(0, 6, "Android Full HD", ln=1)
    pdf.ln(4)

    pdf.cell(0, 6, "Opcion alternativa:", ln=1)
    pdf.cell(0, 6, "$1.300.000 en efectivo", ln=1)
    pdf.ln(5)

    pdf.cell(0, 6, "Sorteo: 30 de octubre", ln=1)
    pdf.cell(0, 6, "Loteria de Medellin", ln=1)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 6, "Responsable: Jovanis Vanegas Ropain", ln=1)
    pdf.cell(0, 6, "Contacto: 3126613272", ln=1)
    pdf.ln(8)

    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, "Gracias por tu compra, mucha suerte!", ln=1)

    return pdf.output(dest="S").encode("latin-1")

# ========================
# CONTROL DE ESTADOS (SESSION STATE)
# ========================
if "pdf_admin" not in st.session_state:
    st.session_state.pdf_admin = None

# NAVEGACIÓN LATERAL ESTÁTICA
st.sidebar.title("Navegación 🧭")
seccion = st.sidebar.radio("Ir a:", ["Reservar Boletos", "Panel Administrador"], key="radio_navigation")

# ========================
# SECCIÓN: RESERVAR BOLETOS
# ========================
if seccion == "Reservar Boletos":
    st.title("🎟️ RIFA PREMIUM — RESERVAS")
    
    cantidad = st.number_input("¿Cuántos números quieres?", 1, 20, 1, key="input_cant")
    nombre = st.text_input("Nombre", key="input_nom")
    telefono = st.text_input("Teléfono", key="input_tel")

    todos = [f"{i:03d}" for i in range(1000)]
    
    if not df.empty:
        vendidos = df[df["estado"] == "Vendido"]["numero"].tolist()
        reservados = df[df["estado"] == "Pendiente"]["numero"].tolist()
    else:
        vendidos, reservados = [], []

    opciones = []
    mapa = {}
    for n in todos:
        if n in vendidos:
            label = f"🔴 {n} (Vendido)"
        elif n in reservados:
            label = f"🟡 {n} (Reservado)"
        else:
            label = f"🟢 {n}"
        opciones.append(label)
        mapa[label] = n

    seleccion = st.multiselect("Selecciona números", opciones, key="multi_num")
    numeros = [mapa[s] for s in seleccion if mapa[s] not in vendidos]

    total = len(numeros) * PRECIO
    st.info(f"💰 Total a pagar: ${total}")

    if st.button("Confirmar Reserva", use_container_width=True, key="btn_confirmar_res"):
        if not nombre or not telefono:
            st.error("Por favor completa tu nombre y teléfono.")
        elif len(numeros) != cantidad:
            st.error(f"Debes seleccionar exactamente {cantidad} números.")
        else:
            nuevos = []
            for n in numeros:
                nuevos.append({
                    "numero": n,
                    "nombre": nombre,
                    "telefono": telefono,
                    "estado": "Pendiente"
                })

            df_actualizado = pd.concat([df, pd.DataFrame(nuevos)], ignore_index=True)
            guardar(df_actualizado)
            exportar_excel(df_actualizado)
            st.success("✅ ¡Reserva registrada! Avisa al administrador para que la apruebe.")
            st.rerun()

# ========================
# SECCIÓN: ADMINISTRADOR
# ========================
elif seccion == "Panel Administrador":
    st.title("🔒 PANEL ADMINISTRADOR")
    clave = st.text_input("Introduce la contraseña de acceso", type="password", key="pwd_admin_field")

    if clave == ADMIN_PASSWORD:
        st.success("Acceso verificado.")

        # Contenedor inmutable para PDFs generados
        if st.session_state.pdf_admin is not None:
            data = st.session_state.pdf_admin
            st.download_button(
                label=f"📄 DESCARGAR COMPROBANTE DE {data['nombre'].upper()}",
                data=data["file"],
                file_name=f"comprobante_{data['telefono']}.pdf",
                mime="application/pdf",
                key="download_pdf_final"
            )
            if st.button("Limpiar descarga anterior", key="clear_pdf_final"):
                st.session_state.pdf_admin = None
                st.rerun()

        # Cargar datos pendientes de forma segura
        pendientes = df[df["estado"] == "Pendiente"] if not df.empty else pd.DataFrame()

        st.write("### 🟡 Gestión de Solicitudes Pendientes")
        if pendientes.empty:
            st.info("No tienes reservas pendientes por procesar.")
        else:
            # Lista plana de textos explicativos para el selector
            opciones_pendientes = [
                f"Boleto: {row['numero']} | Cliente: {row['nombre']} | Tel: {row['telefono']}" 
                for _, row in pendientes.iterrows()
            ]
            
            seleccion_admin = st.selectbox(
                "Selecciona una solicitud de la lista:", 
                opciones_pendientes,
                key="select_pedido_admin"
            )
            
            # CORRECCIÓN DEFINITIVA DE MANEJO DE STRINGS (Acceso por índices individuales de la lista)
            partes = [p.strip() for p in seleccion_admin.split("|")]
            num_seleccionado = partes[0].replace("Boleto:", "").strip()
            nom_seleccionado = partes[1].replace("Cliente:", "").strip()
            tel_seleccionado = partes[2].replace("Tel:", "").strip()

            c1, c2 = st.columns(2)
            with c1:
                if st.button(f"Aprobar Número {num_seleccionado}", use_container_width=True, key="btn_aprob_ok"):
                    df.loc[df["numero"] == num_seleccionado, "estado"] = "Vendido"
                    guardar(df)
                    exportar_excel(df)
                    
               if "pdf_admin" not in st.session_state:
    st.session_state.pdf_admin = None
                    
                    pdf_bytes = generar_pdf(nom_seleccionado, tel_seleccionado, numeros_cliente)
                    st.session_state.pdf_admin = {
                        "file": pdf_bytes,
                        "telefono": tel_seleccionado,
                        "nombre": nom_seleccionado
                    }
                    st.rerun()

            with c2:
                if st.button(f"Rechazar Número {num_seleccionado}", use_container_width=True, key="btn_rech_ok"):
                    df = df[df["numero"] != num_seleccionado]
                    guardar(df)
                    exportar_excel(df)
                    st.rerun()

        # Base de datos global
        st.write("### 📋 Base de Datos Actual")
        st.dataframe(df, use_container_width=True, key="data_table_view")

        # Eliminación Directa
        st.write("### ❌ Eliminación Directa de Registros")
        num_baja = st.text_input("Escribe el número exacto que deseas eliminar (ej: 005)", key="input_baja_manual")

        if st.button("Eliminar permanentemente", key="btn_baja_manual"):
            if num_baja:
                if not df.empty and num_baja in df["numero"].values:
                    df = df[df["numero"] != num_baja]
                    guardar(df)
                    exportar_excel(df)
                    st.success(f"Boleto {num_baja} borrado de los registros.")
                    st.rerun()
                else:
                    st.error("El número ingresado no existe en los registros actuales.")
            else:
                st.error("Debes ingresar un número válido.")
