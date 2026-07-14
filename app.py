import streamlit as st
import pandas as pd
import os
import io
from fpdf import FPDF
from datetime import datetime

# ========================
# CONFIGURACIÓN DE PÁGINA
# ========================
st.set_page_config(page_title="Rifa", page_icon="🎟️")

PRECIO = 3000

# Usamos la carpeta /tmp que es más resistente a los reinicios de Streamlit Cloud
DB_FILE = "/tmp/rifa_db.csv"

# Contraseña fija del administrador para evitar errores de st.secrets
ADMIN_PASSWORD = "admin"

# ========================
# FUNCIONES AUXILIARES DE CONVERSIÓN
# ========================
def generar_excel_bytes(dataframe_agenda):
    """Genera los bytes de Excel de forma aislada para evitar errores de sintaxis"""
    try:
        output_buffer = io.BytesIO()
        dataframe_agenda.to_excel(output_buffer, index=False, engine='openpyxl')
        return output_buffer.getvalue()
    except Exception:
        return b""

# ========================
# BASE DE DATOS RESISTENTE (LOCAL EN FORMATO CSV)
# ========================
def cargar():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=["numero", "nombre", "telefono", "estado"])
        guardar(df)
        return df
    try:
        df_cargado = pd.read_csv(DB_FILE)
        if df_cargado.empty:
            return pd.DataFrame(columns=["numero", "nombre", "telefono", "estado"])
        return df_cargado.astype(str).fillna("")
    except Exception:
        return pd.DataFrame(columns=["numero", "nombre", "telefono", "estado"])

def guardar(df):
    try:
        df.to_csv(DB_FILE, index=False)
        # Copia de respaldo para descargas en Excel
        df.to_excel("compradores.xlsx", index=False)
    except Exception as e:
        st.error(f"Error al guardar datos: {e}")

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
    pdf.cell(0, 7, f"Nombre: {nombre}".encode('latin-1', 'ignore').decode('latin-1'), ln=1)
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

if "admin_login" not in st.session_state:
    st.session_state.admin_login = False

# ========================
# INTERFAZ PRINCIPAL POR PESTAÑAS
# ========================
st.title("🎟️ RIFA PREMIUM")

tab1, tab2 = st.tabs(["Reservar", "Administrador"])

# ========================
# PESTAÑA 1: RESERVAS
# ========================
with tab1:
    cantidad = st.number_input("¿Cuántos números quieres?", 1, 20, 1, key="input_cant")
    nombre = st.text_input("Nombre", key="input_nom")
    telefono = st.text_input("Telefono", key="input_tel")

    todos = [f"{i:03d}" for i in range(1000)]
    
    if not df.empty:
        vendidos = df[df["estado"].str.strip() == "Vendido"]["numero"].tolist()
        reservados = df[df["estado"].str.strip() == "Pendiente"]["numero"].tolist()
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

    seleccion = st.multiselect("Selecciona números", opciones, key="multi_num")
    numeros = [mapa[s] for s in seleccion if mapa[s] not in vendidos and mapa[s] not in reservados]

    total = len(numeros) * PRECIO
    st.success(f"💰 Total a pagar: ${total}")

    if st.button("Reservar", key="btn_reservar"):
        if not nombre or not telefono:
            st.error("Completa los datos")
        elif len(numeros) != cantidad:
            st.error("Selecciona la cantidad correcta de números libres (Verdes)")
        else:
            nuevos = []
            for n in numeros:
                if n not in df["numero"].tolist():
                    nuevos.append({
                        "numero": n,
                        "nombre": nombre,
                        "telefono": telefono,
                        "estado": "Pendiente"
                    })

            if nuevos:
                df_actualizado = pd.concat([df, pd.DataFrame(nuevos)], ignore_index=True)
                guardar(df_actualizado)
                st.success("✅ Reserva guardada con éxito")
                st.rerun()
            else:
                st.error("Uno o más números seleccionados ya no están disponibles.")

# ========================
# PESTAÑA 2: ADMINISTRADOR
# ========================
with tab2:
    st.subheader("🔒 Panel Administrador")
    
    if not st.session_state.admin_login:
        clave = st.text_input("Contraseña", type="password", key="pwd_admin_field")
        if st.button("Ingresar", key="btn_login_admin"):
            if clave == ADMIN_PASSWORD:
                st.session_state.admin_login = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
    else:
        st.success("Acceso concedido ✅")
        
        if st.button("Cerrar Sesión", key="btn_logout_admin"):
            st.session_state.admin_login = False
            st.session_state.pdf_admin = None
            st.rerun()

        if st.session_state.pdf_admin is not None:
            data = st.session_state.pdf_admin
            st.download_button(
                label=f"📄 Descargar comprobante de {data['nombre']}",
                data=data["file"],
                file_name=f"comprobante_{data['telefono']}.pdf",
                mime="application/pdf",
                key="download_pdf_btn"
            )
            if st.button("Limpiar descarga actual", key="clear_pdf_btn"):
                st.session_state.pdf_admin = None
                st.rerun()

        # Filtro de solicitudes con limpieza de strings
        pendientes = df[df["estado"].str.strip() == "Pendiente"] if not df.empty else pd.DataFrame()

        if pendientes.empty:
            st.info("No hay reservas pendientes de aprobación")
        else:
            st.write("### 🟡 Pendientes")

            for i, row in pendientes.iterrows():
                st.write(f"**Número:** {row['numero']} — **Cliente:** {row['nombre']} — **Teléfono:** {row['telefono']}")
                col1, col2 = st.columns(2)

                # APROBAR BOLETO
                with col1:
                    if st.button(f"✅ Aprobar {row['numero']}", key=f"approve_btn_{row['numero']}_{i}"):
                        df.loc[i, "estado"] = "Vendido"
                        guardar(df)
                        
                        cliente = df[(df["telefono"] == row["telefono"]) & (df["estado"].str.strip() == "Vendido")]
                        numeros_cliente = cliente["numero"].tolist()

                        pdf_bytes = generar_pdf(row["nombre"], row["telefono"], numeros_cliente)
                        st.session_state.pdf_admin = {
                            "nombre": row["nombre"],
                            "telefono": row["telefono"],
                            "file": pdf_bytes
                        }
                        st.success(f"¡Boleto {row['numero']} aprobado!")
                        st.rerun()

                # RECHAZAR / ELIMINAR RESERVA ERRONEA
                with col2:
                    if st.button(f"❌ Rechazar {row['numero']}", key=f"reject_btn_{row['numero']}_{i}"):
                        df = df.drop(i)
                        guardar(df)
                        st.warning(f"¡Reserva del boleto {row['numero']} eliminada!")
                        st.rerun()

        # ==========================================
        # AGENDA DESPLEGABLE OPTIMIZADA EN LÍNEAS CORTAS
        # ==========================================
        st.write("---")
        
        with st.expander("📋 Ver Agenda de Números Vendidos", expanded=False):
            if df.empty:
                st.info("Aún no hay base de datos registrada.")
            else:
                v_df = df[df["estado"].str.strip() == "Vendido"].copy()
                if v_df.empty:
                    st.info("Aún no se han vendido números.")
                else:
                    v_df = v_df.sort_values(by="numero")
                    columnas_renombradas = {"numero": "Boleto", "nombre": "Nombre del Cliente", "telefono": "Teléfono"}
