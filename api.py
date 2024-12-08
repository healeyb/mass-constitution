import os
import json
from database import Database
from flask import Flask, make_response

from dotenv import load_dotenv
load_dotenv(override=True)

app = Flask(__name__)
db = Database()

def jsonify(output, status=200, indent=4, sort_keys=True):
    response = make_response(json.dumps(output, indent=indent, sort_keys=sort_keys))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    response.headers['mimetype'] = 'application/json'
    response.status_code = status
    return response

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "OK",
        "message": "API is operational"
    }, status=200)

@app.route('/', methods=['GET'])
def search():
    data = db.select_all(
        """SELECT b.block_id, b.category, b.chapter, b.section, b.article, b.segment, 
              b.text, b.amendments, 
              b.is_annulled, b.is_amended, b.is_superseded,
              catm.subtitle AS category_subtitle, 
              chm.subtitle AS chapter_subtitle, 
              sm.subtitle AS section_subtitle,
              am.ratified AS amendment_ratified
           FROM blocks b
              LEFT JOIN category_metadata catm USING (category)
              LEFT JOIN chapter_metadata chm ON (
                 chm.category = b.category AND 
                 chm.chapter = b.chapter
              )
              LEFT JOIN section_metadata sm ON (
                 sm.category = b.category AND 
                 sm.chapter = b.chapter AND 
                 sm.section = b.section
              )
              LEFT JOIN amendment_metadata am ON (
                 b.category = 'amendment' AND 
                 am.article = b.article
              );"""
    )

    output = []
    if data:
        for block in data:
            chapter_block = None
            if block['chapter']:
                chapter_block = {
                    "number": block['chapter'],
                    "subtitle": block['chapter_subtitle'],
                }

            section_block = None
            if block['section']:
                section_block = {
                    "number": block['section'],
                    "subtitle": block['section_subtitle'],
                }

            metadata = {
                "part": {
                    "name": block['category'].replace("_", " ").title(),
                    "subtitle": block['category_subtitle'],
                },
                "chapter": chapter_block,
                "section": section_block,
                "article": block['article'],
                "paragraph": block['segment'],
            }

            if block['amendment_ratified']:
                metadata["ratified"] = block['amendment_ratified']

            output.append({
                # "id": block['block_id'],
                "position": metadata,
                "text": block['text'],
                "flags": {
                    "is_annulled": True if block['is_annulled'] else False,
                    "is_amended": True if block['is_amended'] else False,
                    "is_superseded": True if block['is_superseded'] else False,
                },
                "changes": json.loads(block['amendments']) if block['amendments'] else None,
            })

    return jsonify(output)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=os.environ["API_PORT"])