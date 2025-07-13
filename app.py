from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)


# 🟢 Connect to your local MongoDB server
client = MongoClient("mongodb+srv://tanaydhanvijay:i!Q3yTTXK_uAp2q@cluster0.vwydarf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['github_webhook']           # Database name
collection = db['events']               # Collection name

@app.route('/')
def index():
    return render_template('index.html')

# 🔴 GitHub will send webhook events to this endpoint
@app.route('/webhook', methods=['POST'])
def github_webhook():
    data = request.json                            # JSON payload sent from GitHub
    event_type = request.headers.get('X-GitHub-Event')  # e.g., push, pull_request

    event = {}  # Dictionary to hold the parsed event data

    # ✅ PUSH event
    if event_type == "push":
        event['type'] = "PUSH"
        event['author'] = data['pusher']['name']                         # Who pushed
        event['to_branch'] = data['ref'].split('/')[-1]                  # Which branch
        event['timestamp'] = datetime.utcnow().strftime("%d %B %Y - %I:%M %p UTC")

    # ✅ PULL REQUEST event
    elif event_type == "pull_request":
        action = data['action']
        if action == "opened":
            event['type'] = "PULL_REQUEST"
            event['author'] = data['pull_request']['user']['login']
            event['from_branch'] = data['pull_request']['head']['ref']
            event['to_branch'] = data['pull_request']['base']['ref']
            event['timestamp'] = datetime.utcnow().strftime("%d %B %Y - %I:%M %p UTC")

    # ✅ MERGE (optional Brownie Points)
    elif event_type == "pull_request" and data.get("pull_request", {}).get("merged"):
        event['type'] = "MERGE"
        event['author'] = data['pull_request']['user']['login']
        event['from_branch'] = data['pull_request']['head']['ref']
        event['to_branch'] = data['pull_request']['base']['ref']
        event['timestamp'] = datetime.utcnow().strftime("%d %B %Y - %I:%M %p UTC")

    else:
        return jsonify({"message": "Event ignored"}), 200

    # ✅ Save the parsed event to MongoDB
    collection.insert_one(event)

    return jsonify({"message": "Event stored"}), 201


# 🟢 API endpoint to return the last 10 events (used by frontend)
@app.route('/events', methods=['GET'])
def get_events():
    events = list(collection.find().sort('_id', -1).limit(10))  # Latest 10
    for e in events:
        e['_id'] = str(e['_id'])  # Convert ObjectId to string for JSON
    return jsonify(events)

# 🚀 Start the Flask server on port 5000
if __name__ == '__main__':
    app.run(port=5000)

