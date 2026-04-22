import os
import psycopg2
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Función para conectar con la base de datos de Render
def get_db_connection():
    db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, sslmode='require')

def motor_nlu_db(mensaje):
    """Lógica NLU: Busca conceptos en la base de datos."""
    mensaje = mensaje.lower().strip()
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Buscamos si el mensaje coincide con alguna keyword
        query = "SELECT respuesta FROM conocimiento_paralelo WHERE %s ILIKE ANY(keywords) OR concepto ILIKE %s LIMIT 1;"
        cur.execute(query, (f"%{mensaje}%", f"%{mensaje}%"))
        
        resultado = cur.fetchone()
        cur.close()
        conn.close()

        if resultado:
            return resultado[0]
        else:
            return "No encontré ese concepto. Prueba con: Amdahl, Flynn, MPI, CUDA o Cluster."
    
    except Exception as e:
        if conn: conn.close()
        return f"Error de conexión: {str(e)}"

# Interfaz visual HTML
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Chatbot TICs - Cómputo Paralelo</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background-color: #f4f4f9; display: flex; justify-content: center; padding: 20px; }
        .chat-container { width: 100%; max-width: 500px; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h2 { color: #333; text-align: center; }
        #chat-box { height: 300px; border: 1px solid #ddd; overflow-y: scroll; padding: 10px; margin-bottom: 10px; background: #fafafa; display: flex; flex-direction: column; }
        .msg { margin: 5px 0; padding: 8px 12px; border-radius: 15px; max-width: 80%; }
        .user { align-self: flex-end; background: #007bff; color: white; }
        .bot { align-self: flex-start; background: #e9ecef; color: #333; }
        .input-area { display: flex; gap: 10px; }
        input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        button { padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="chat-container">
        <h2>🤖 Chatbot Paralelo</h2>
        <div id="chat-box">
            <div class="msg bot">¡Hola! Soy tu asistente de TICs. Pregúntame sobre Cómputo Paralelo.</div>
        </div>
        <div class="input-area">
            <input type="text" id="userInput" placeholder="Escribe un tema...">
            <button onclick="sendMessage()">Enviar</button>
        </div>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chat-box');
            const message = input.value.trim();
            if (!message) return;

            // Mostrar mensaje del usuario
            chatBox.innerHTML += `<div class="msg user">${message}</div>`;
            input.value = '';

            // Consultar al servidor
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mensaje: message })
            });
            const data = await response.json();

            // Mostrar respuesta del bot
            chatBox.innerHTML += `<div class="msg bot">${data.respuesta}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data or 'mensaje' not in data:
        return jsonify({"respuesta": "Error: No se recibió mensaje."}), 400
    
    respuesta_final = motor_nlu_db(data['mensaje'])
    return jsonify({"respuesta": respuesta_final})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
