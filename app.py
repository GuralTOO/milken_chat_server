from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO, send
from old_school_retrieval import get_answer_stream, search_items, get_openai_summary

print("starting server daddy")

app = Flask(__name__)
CORS(app)  # this would enable CORS for all routes
app.config['SECRET_KEY'] = 'mysecret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


@socketio.on('message')
def handle_message(input_text):
    # Each chunk is sent as soon as it is received
    print('received message: ' + input_text)
    for chunk in get_answer_stream(input_text):
        send(chunk)

# api endpoint to get results of search_items


@app.route('/search/<text_query>')
def search(text_query):
    print("Searching for: " + text_query)
    results = search_items(class_name="Econ_club_data_06142023", variables=[
        "url", "page_text"], text_query=text_query, k=3)

    for result in results:
        result["summary"] = get_openai_summary(result["page_text"], text_query)
        # remove the page_text from the result
        del result["page_text"]

    print("Search results with summaries: \n", results)

    # convert results to json and return
    return {"results": results}


if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=8001)
