from quart import Quart, render_template, request, jsonify
import asyncio
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'PyCharacterAI')))
from PyCharacterAI import Client

app = Quart(__name__)
token = "58009acf6549b6c5004c478c9f9620a18c4d5227"
client = Client()

async def authenticate():
    await client.authenticate_with_token(token)
    username = (await client.fetch_user())['user']['username']
    return username

@app.route('/')
async def index():
    username = await authenticate()
    return await render_template('index.html', username=username)

@app.route('/chat', methods=['POST'])
async def chat():
    data = await request.get_json()
    message = data['message']
    character_id = "uX8qHZKfWjy8v62H6A7uLGnhVBw971UAJ3CUqgcPURc"
    chat = await client.create_or_continue_chat(character_id)
    answer = await chat.send_message(message)
    return jsonify({'response': f"{answer.src_character_name}: {answer.text}"})

if __name__ == "__main__":
    app.run(debug=True)
