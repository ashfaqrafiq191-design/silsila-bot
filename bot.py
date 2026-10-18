import os
from flask import Flask, request, jsonify
import requests
import google.generativeai as genai

app = Flask(__name__)

# Gemini API Key (आपकी नई जनरेट की हुई की यहाँ सेट कर दी गई है)
GEMINI_API_KEY = "AQ.Ab8RN6KwSfHWe_QwZEOKa9peR4Gd-S5cwmGFK8yl9qhWt9u-Sg"
genai.configure(api_key=GEMINI_API_KEY)

# मेटा व्हाट्सएप क्रेडेंशियल्स (जो हमने टेस्ट डैशबोर्ड से लिए थे)
WHATSAPP_TOKEN = "EAAX093RpFZAs7OTZB9zsDKxE5" # आपका मेटा एक्सेस टोकन
PHONE_NUMBER_ID = "1676718530696603" # आपका फोन नंबर आईडी
VERIFY_TOKEN = "sagar055"

# Gemini मॉडल सेट करें जो सिर्फ दीनी और authentic जवाब दे
generation_config = {
  "temperature": 0.7,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 1024,
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction="तुम सिलसिला الأبصار (Silsila Al-Absar) के एक दीनी असिस्टेंट हो। यूजर के हर सवाल का जवाब केवल और केवल कुरान की आयतों और सही हदीस के प्रमाणित संदर्भों (References) के साथ उर्दू या हिंदी में दें।"
)

# 1. Webhook Verification (मेटा इसे वेरीफाई करेगा)
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return 'Verification failed', 403
    return 'Hello World', 200

# 2. Receive WhatsApp Message & Reply via Gemini AI
@app.route('/webhook', methods=['POST'])
def receive_message():
    data = request.json
    try:
        if 'entry' in data:
            changes = data['entry'][0]['changes'][0]
            value = changes['value']
            if 'messages' in value:
                message_data = value['messages'][0]
                sender_phone = message_data['from'] # यूजर का व्हाट्सएप नंबर
                user_message = message_data['text']['body'] # यूजर का सवाल

                # Gemini AI से जवाब प्राप्त करें
                chat_session = model.start_chat(history=[])
                ai_response = chat_session.send_message(user_message)
                reply_text = ai_response.text

                # व्हाट्सएप पर रिप्लाई भेजने का अनुरोध (Request)
                url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
                headers = {
                    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "to": sender_phone,
                    "text": {"body": reply_text}
                }
                requests.post(url, json=payload, headers=headers)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
