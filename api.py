from database import Database
from flask import Flask, jsonify

app = Flask(__name__)
db = Database()

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "OK",
        "message": "API is operational"
    })

@app.route('/all', methods=['GET'])
def all_blocks():
    data = db.select_all("SELECT * FROM blocks;")
    if data:
        print(data)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)