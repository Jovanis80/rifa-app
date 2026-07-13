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

        # Botón fijo superior para descargas de comprobantes generados
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

        # Filtrar solicitudes pendientes
        pendientes = df[df["estado"] == "Pendiente"] if not df.empty else pd.DataFrame()

        if pendientes.empty:
            st.info("No hay reservas pendientes de aprobación")
        else:
            st.write("### 🟡 Pendientes")

            # Muestra cada solicitud pendiente en filas individuales con botones independientes
            for i, row in pendientes.iterrows():
                st.write(f"**Número:** {row['numero']} — **Cliente:** {row['nombre']} — **Teléfono:** {row['telefono']}")
                col1, col2 = st.columns(2)

                # APROBAR BOLETO
                with col1:
                    if st.button(f"✅ Aprobar {row['numero']}", key=f"approve_btn_{row['numero']}"):
                        df.loc[df["numero"] == row["numero"], "estado"] = "Vendido"
                        guardar(df)
                        exportar_excel(df)
                        
                        # Buscar todos los boletos comprados acumulados de este cliente específico
                        cliente = df[(df["telefono"] == row["telefono"]) & (df["estado"] == "Vendido")]
                        numeros_cliente = cliente["numero"].tolist()

                        # ====== AQUÍ ESTABA EL ERROR (CORREGIDO) ======
                        # Generar el archivo PDF y asignarlo correctamente a session_state
                        pdf_bytes = generar_pdf(row["nombre"], row["telefono"], numeros_cliente)
                        st.session_state.pdf_admin = {
                            "nombre": row["nombre"],
                            "telefono": row["telefono"],
                            "file": pdf_bytes
                        }
                        st.success(f"¡Boleto {row['numero']} aprobado!")
                        st.rerun() # Fuerza a Streamlit a mostrar el botón de descarga inmediatamente
