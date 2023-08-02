from flask import Flask
from flask_socketio import SocketIO, send
from old_school_retrieval import get_answer_stream

print("starting server daddy")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


@socketio.on('message')
def handle_message(input_text):
    # Each chunk is sent as soon as it is received
    print('received message: ' + input_text)
    for chunk in get_answer_stream(input_text):
        send(chunk)


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=8001)
