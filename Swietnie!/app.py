from flask import Flask, request, jsonify, render_template
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'PyCharacterAI')))

from PyCharacterAI import Client

app = Flask(__name__)

token = ""
client = Client()

def init_app():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(client.authenticate_with_token(token))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    message = request.json.get('message')
    if not message:
        return jsonify({'error': 'No message provided'}), 400

    async def process_message():
        character_id = ""
        chat = await client.create_or_continue_chat(character_id)
        answer = await chat.send_message(message)
        return answer.text

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response_text = loop.run_until_complete(process_message())

    return jsonify({'response': response_text})

if __name__ == '__main__':
    init_app()  # Initialize the app here
    app.run(debug=True)
