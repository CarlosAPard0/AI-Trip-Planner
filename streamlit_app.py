import streamlit as st
import requests
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

# ===============================
# CONFIGURACIÓN GENERAL
# ===============================
st.set_page_config(
    page_title="AI Trip Planner",
    page_icon="✈️",
    layout="centered"
)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_ENDPOINT = "/query"
FULL_API_URL = f"{BACKEND_URL}{API_ENDPOINT}"

# ===============================
# ESTADO
# ===============================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "preferences" not in st.session_state:
    st.session_state.preferences = {
        "budget": "Medio",
        "travel_type": [],
        "days": 5,
        "people": 1,
        "other_notes": ""
    }

# ===============================
# SIDEBAR – PREFERENCIAS
# ===============================
with st.sidebar:
    st.title("⚙️ Preferencias del viaje")

    st.session_state.preferences["budget"] = st.selectbox(
        "💰 Presupuesto",
        ["Bajo", "Medio", "Alto", "Otro"]
    )

    st.session_state.preferences["travel_type"] = st.multiselect(
        "🎯 Tipo de viaje",
        [
            "Aventura",
            "Cultural",
            "Gastronómico",
            "Relax",
            "Otro"
        ]
    )

    st.session_state.preferences["days"] = st.number_input(
        "📅 Duración (días)",
        min_value=1,
        max_value=60,
        value=5
    )

    st.session_state.preferences["people"] = st.number_input(
        "👥 Número de personas",
        min_value=1,
        max_value=20,
        value=1
    )

    st.session_state.preferences["other_notes"] = st.text_area(
        "📝 Otros detalles importantes",
        placeholder="Ej: viajo con niños, mascotas, restricciones alimentarias..."
    )

    st.divider()

    if st.button("🧹 Nuevo viaje"):
        st.session_state.messages = []
        st.success("Conversación reiniciada")

# ===============================
# UI PRINCIPAL
# ===============================
st.title("✈️ AI Trip Planner")
st.caption("Asistente inteligente para planificar tus viajes")

# ===============================
# HISTORIAL DE CHAT
# ===============================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ===============================
# INPUT DEL USUARIO
# ===============================
prompt = st.chat_input("Describe el viaje que quieres planificar...")

if prompt:
    # Mensaje usuario
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Respuesta IA
    with st.chat_message("assistant"):
        with st.spinner("🧠 Planificando tu viaje..."):
            try:
                payload = {
                    "question": f"""
Usuario quiere planificar un viaje con los siguientes datos:

MENSAJE:
{prompt}

PREFERENCIAS:
- Presupuesto: {st.session_state.preferences['budget']}
- Tipo de viaje: {', '.join(st.session_state.preferences['travel_type']) or 'No especificado'}
- Duración: {st.session_state.preferences['days']} días
- Personas: {st.session_state.preferences['people']}
- Otros detalles: {st.session_state.preferences['other_notes'] or 'Ninguno'}

Genera un plan claro y estructurado.
"""
                }

                response = requests.post(
                    FULL_API_URL,
                    json=payload,
                    timeout=60
                )

                response.raise_for_status()
                data = response.json()

                assistant_reply = data.get(
                    "answer",
                    "No se recibió respuesta del asistente."
                )

                st.markdown(assistant_reply)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_reply
                })

            except Exception:
                msg = "⚠️ Error al generar el plan de viaje."
                st.error(msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": msg
                })

# ===============================
# EXPORTAR A PDF
# ===============================
def generate_pdf(messages, preferences):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    x = 2 * cm
    y = height - 2 * cm

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(x, y, "AI Trip Planner – Plan de Viaje")
    y -= 1.5 * cm

    pdf.setFont("Helvetica", 11)
    pdf.drawString(x, y, "Preferencias:")
    y -= 0.8 * cm

    for key, value in preferences.items():
        text = f"- {key}: {value}"
        pdf.drawString(x, y, text)
        y -= 0.6 * cm

    y -= 0.8 * cm
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(x, y, "Conversación:")
    y -= 0.8 * cm
    pdf.setFont("Helvetica", 10)

    for msg in messages:
        role = "Usuario" if msg["role"] == "user" else "Asistente"
        for line in msg["content"].split("\n"):
            if y < 2 * cm:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = height - 2 * cm
            pdf.drawString(x, y, f"{role}: {line}")
            y -= 0.5 * cm

    pdf.save()
    buffer.seek(0)
    return buffer

if st.session_state.messages:
    st.divider()
    if st.button("📄 Exportar plan a PDF"):
        pdf_file = generate_pdf(
            st.session_state.messages,
            st.session_state.preferences
        )
        st.download_button(
            label="⬇️ Descargar PDF",
            data=pdf_file,
            file_name="plan_de_viaje.pdf",
            mime="application/pdf"
        )
