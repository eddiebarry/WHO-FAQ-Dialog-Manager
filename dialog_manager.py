import flask
from flask import request, jsonify
from match import matcher

app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/api/v2/qna', methods=['GET'])
def api_question():
    # Check if an ID was provided as part of the URL.
    # If ID is provided, assign it to a variable.
    # If no ID is provided, display an error in the browser.
    if 'question' in request.args:
        q = str(request.args['question'])
        q = q.replace('_',' ')
        print(q)
    else:
        print(request.args)
        return "Error: No id field provided. Please specify an id."

    
    q_closest,a_closest = match.return_closest(q)

    resp_json = {
        "question": q,
        "question_closest": q_closest,
        "answer_closest": a_closest
    }

    return jsonify(resp_json)

app.run(host='0.0.0.0')

