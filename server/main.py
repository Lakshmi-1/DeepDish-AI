from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, origins='*')

@app.route("/api/test", methods=['GET'])
def test():
    return jsonify({"message": "Hello, from Flask!"})

if __name__ == '__main__':
    app.run(debug=True, port=8080)