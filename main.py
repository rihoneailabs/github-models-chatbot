import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
import dotenv

dotenv.load_dotenv()
app = FastAPI()
# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store chat history
chat_history = []


def call_llm(prompt: str) -> str:
    endpoint = "https://models.inference.ai.azure.com"
    model_name = "DeepSeek-R1"
    token = os.environ["GITHUB_TOKEN"]

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(token),
    )

    response = client.complete(
        messages=[
            UserMessage(prompt)
        ],
        max_tokens=1000,
        model=model_name
    )
    return response.choices[0].message.content

@app.get("/", response_class=HTMLResponse)
async def get_home():
    with open("static/index.html") as f:
        return f.read()

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = {"sender": "user", "message": data}
            chat_history.append(message)
            
            # Simple bot response
            bot_response = call_llm(data)
            response_message = {"sender": "bot", "message": bot_response}
            chat_history.append(response_message)
            
            # Send response back to client
            await websocket.send_json(response_message)
    except:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)