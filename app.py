import streamlit as st
import pandas as pd
import os
import json
from fpdf import FPDF
from datetime import datetime

# ========================
# CONFIG
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

# Inicialización segura de los datos
df = cargar()

# ========================
# PDF CORREGIDO CON NUEVO DISEÑO Y FECHA
# ========================
def generar_pdf(nombre, telefono, numeros):
    pdf = FPDF()
    pdf.add_page()

    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    total = PRECIO * len(numeros)

    # Título principal en Rojo
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(180, 0, 0) # Color Rojo para J.V.R PREMIUM RIFA
    pdf.cell(0, 12, "J.V.R PREMIUM RIFA", ln=1, align="C")
    pdf.ln(5)

    # Restablecer color a negro para los datos del cliente
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 7, f"Nombre: {nombre}", ln=1)
    pdf.cell(0, 7, f"Telefono: {telefono}", ln=1)
    pdf.ln(5)

    # Subtítulo de boletos en Rojo
    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(180, 0, 0) # Color Rojo para NUMERO DE BOLETO
    pdf.cell(0, 8, "NUMERO DE BOLETO", ln=1)
    
    # Números adquiridos en negro y negrita
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, " - ".join(numeros), ln=1)
    pdf.ln(4)

    # Bloque de fecha y costos
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, f"Fecha: {fecha_actual}", ln=1)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 7, f"Total pagado: ${total}", ln=1)
    pdf.ln(5)

    # Información de premios
    pdf.cell(0, 6, "Premio principal:", ln=1)
    pdf.cell(0, 6, "Televisor Smart TV Sankey 42 pulgadas", ln=1)
    pdf.cell(0, 6, "Android Full HD", ln=1)
    pdf.ln(4)

    pdf.cell(0, 6, "Opcion alternativa:", ln=1)
    pdf.cell(0, 6, "$1.300.000 en efectivo", ln=1)
    pdf.ln(5)

    # FECHA DEL SORTEO OBLIGATORIA
    pdf.cell(0, 6, "Sorteo: 30 de octubre", ln=1)
    pdf.cell(0, 6, "Loteria de Medellin", ln=1)
    pdf.ln(5)

    # Datos del responsable organizador en negrita
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 6, "Responsable: Jovanis Vanegas Ropain", ln=1)
    pdf.cell(0, 6, "Contacto: 3126613272", ln=1)
    pdf.ln(8)

    # Mensaje de despedida en cursiva
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, "Gracias por tu compra, mucha suerte!", ln=1)

    return pdf.output(dest="S").encode("latin-1")

# ========================
# SESSION STATE
# ========================
if "pdf_admin" not in st.session_state:
    st.session_state.pdf_admin = None

# ========================
# INTERFAZ PRINCIPAL
# ========================
st.title("🎟️ RIFA PREMIUM")

tab1, tab2 = st.tabs(["Reservar", "Administrador"])

# ========================
# APARTADO RESERVAS
# ========================
with tab1:
    cantidad = st.number_input("¿Cuántos números quieres?", 1, 20, 1)
    nombre = st.text_input("Nombre")
    telefono = st.text_input("Telefono")

    todos = [f"{i:03d}" for i in range(1000)]
    
    if not df.empty:
        vendidos = df[df["estado"] == "Vendido"]["numero"].tolist()
        reservados = df[df["estado"] == "Pendiente"]["numero"].tolist()
    else:
        vendidos = []
        reservados = []

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

    seleccion = st.multiselect("Selecciona números", opciones)
    numeros = [mapa[s] for s in seleccion if mapa[s] not in vendidos]

    total = len(numeros) * PRECIO
    st.success(f"💰 Total a pagar: ${total}")

    if st.button("Reservar"):
        if not nombre or not telefono:
            st.error("Completa los datos")
        elif len(numeros) != cantidad:
            st.error("Selecciona la cantidad correcta")
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

            st.success("✅ Reserva guardada con éxito")
            st.rerun()

# ========================
# APARTADO ADMINISTRADOR
# ========================
with tab2:
    st.subheader("🔒 Panel Administrador")
    clave = st.text_input("Contraseña", type="password")

    if clave == ADMIN_PASSWORD:
        st.success("Acceso concedido ✅")

        # CONTROL DE DESCARGAS DE COMPROBANTES (Se muestra arriba para que no desaparezca con el rerun)
        if st.session_state.pdf_admin is not None:
            data = st.session_state.pdf_admin
            st.download_button(
                label=f"📄 Descargar comprobante de {data['nombre']}",
                data=data["file"],
                file_name=f"comprobante_{data['telefono']}.pdf",
                mime="application/pdf",
                key="download_pdf_btn"
            )
            if st.button("Limpiar descarga actual"):
                st.session_state.pdf_admin = None
                st.rerun()

        if not df.empty:
            pendientes = df[df["estado"] == "Pendiente"]
        else:
            pendientes = pd.DataFrame()

        if pendientes.empty:
            st.info("No hay reservas pendientes de aprobación")
        else:
            st.write("### 🟡 Pendientes")

            for i, row in pendientes.iterrows():
                st.write(f"**Número:** {row['numero']} — **Cliente:** {row['nombre']}")
                col1, col2 = st.columns(2)

                # APROBAR
                with col1:
                    if st.button(f"✅ Aprobar {row['numero']}", key=f"a{i}"):
                        df.loc[df["numero"] == row["numero"], "estado"] = "Vendido"
                        guardar(df)
                        exportar_excel(df)
                        
                        # Buscar todos los números vendidos acumulados del cliente
                        cliente = df[(df["telefono"] == row["telefono"]) & (df["estado"] == "Vendido")]
                        numeros_cliente = cliente["numero"].tolist()

                        # Generar el PDF y guardarlo en el estado de sesión
                        pdf_bytes = generar_pdf(row["nombre"], row["telefono"], numeros_cliente)
                        st.session_state.pdf_admin = {
                            "file": pdf_bytes,
                            "telefono": row["telefono"],
                            "nombre": row["nombre"]
                        }
                        st.success("✅ Número aprobado")
                        st.rerun()

                # RECHAZAR RESERVA
                with col2:
                    if st.button(f"❌ Rechazar {row['numero']}", key=f"r{i}"):
                        df = df[df["numero"] != row["numero"]]
                        guardar(df)
                        exportar_excel(df)
                        st.rerun()

        st.write("### 📋 Base de Datos Actual")
        st.dataframe(df)

        # ELIMINACIÓN DE REGISTROS INDIVIDUALES (Líneas completadas)
        st.write("### ❌ Eliminar número específico")
        num = st.text_input("Ingresa el número a dar de baja (ej: 045)")

        if st.button("Eliminar Número"):
            if num:
                if not df.empty and num in df["numero"].values:
                    df = df[df["numero"] != num]
                    guardar(df)
                    exportar_excel(df)
                    st.success(f"🗑️ Número {num} eliminado correctamente.")
                    st.rerun()
                else:
                    st.error("El número no se encuentra registrado.")
            else:
                st.error("Por favor ingresa un número válido.")
