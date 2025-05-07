from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Google Sheets Auth
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets']
creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Pedidos WhatsApp").sheet1

usuarios = {}

@app.route("/whatsapp", methods=['POST'])
def whatsapp():
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')
    resp = MessagingResponse()
    msg = resp.message()

    if from_number not in usuarios:
        usuarios[from_number] = {"step": 0, "data": {}}

    pasos = ["cliente", "direccion", "horario", "cantidad", "producto"]
    usuario = usuarios[from_number]

    if incoming_msg.lower() == "hacer pedido":
        usuario["step"] = 0
        usuario["data"] = {}
        msg.body("📝 Empezamos tu pedido. ¿Cuál es el nombre del cliente?")
    else:
        if usuario["step"] < len(pasos):
            campo = pasos[usuario["step"]]
            usuario["data"][campo] = incoming_msg
            usuario["step"] += 1

            if usuario["step"] < len(pasos):
                siguiente = pasos[usuario["step"]]
                msg.body(f"Por favor, ingresá {siguiente}:")
            else:
                datos = usuario["data"]
                sheet.append_row([datos[c] for c in pasos])
                msg.body("✅ Pedido recibido. ¡Gracias!")
                usuarios[from_number] = {"step": 0, "data": {}}
        else:
            msg.body("Escribí 'hacer pedido' para iniciar un nuevo pedido.")

    return str(resp)

@app.route("/api/pedidos", methods=["GET"])
def obtener_pedidos():
    registros = sheet.get_all_records()
    return jsonify(registros)

if __name__ == "__main__":
    app.run(debug=True)
