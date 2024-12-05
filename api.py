import os
from database import Database
from flask import Flask, jsonify

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

db = Database()

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "OK",
        "message": "API is operational"
    })

@app.route('/all', methods=['GET'])
def all_blocks():
    data = db.select_all(
        """SELECT block_id, category, chapter, section, article, segment, content
           FROM blocks;"""
    )

    if data:
        output = []
        for block in data:
            output.append({
                "block_id": block[0],
                "category": block[1],
                "chapter": block[2],
                "section": block[3],
                "article": block[4],
                "segment": block[5],
                "content": block[6],
            })

        return jsonify(output)



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=os.environ["API_PORT"])