import os
import json
import markdown2
from markdown_it import MarkdownIt

from support import SupportService
from flask import Flask, make_response, request

from openai import OpenAI
client = OpenAI()

from dotenv import load_dotenv
load_dotenv(override=True)

app = Flask(__name__)
support_service = SupportService()

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

@app.route('/compare', methods=['GET'])
def compare():
    params = request.args.to_dict()
    if "bill_url" in params:
        bill_url = params["bill_url"]
        output = params["output"] if "output" in params else "json"

        # for this URL type, just append PDF...
        if ".pdf" not in bill_url and "malegislature.gov" in bill_url:
            bill_url = f"{bill_url}.pdf"

        if ".pdf" not in bill_url:
            response = jsonify(message="Bill URL must point to a PDF document")
            response.status_code = 400
            return response

        if "malegislature.gov" not in bill_url:
            response = jsonify(message="Bill URL must point to a PDF hosted by malegislature.gov")
            response.status_code = 400
            return response

        response = support_service.compare_bill(bill_url=bill_url)
        if response:
            if output == "json":
                md = MarkdownIt()
                tokens = md.parse(response)

                def parse_tokens(tokens):
                    parsed = []
                    for token in tokens:
                        token_data = {
                            "type": token.type,
                            "tag": token.tag,
                            "content": token.content,
                            "level": token.level
                        }
                        parsed.append(token_data)

                    return parsed

                parsed_structure = parse_tokens(tokens)
                return jsonify(parsed_structure)

            elif output == "html":
                return markdown2.markdown(response)

            return response

@app.route('/', methods=['GET'])
def search():
    output = support_service.compose_language()
    if output:
        return jsonify(output)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=os.environ["API_PORT"])