from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flasgger import Swagger, swag_from
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

# Swagger Config
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Quiz App API",
        "description": "API Documentation for Quiz Application",
        "version": "1.0.0"
    }
}
swagger = Swagger(app, template=swagger_template)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
)

db = SQLAlchemy(app)


class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    score = db.Column(db.Integer)
    total = db.Column(db.Integer)
    percentage = db.Column(db.Float)


questions = [
    {"q": "What does CPU stand for?", "a": "central processing unit"},
    {"q": "What does GPU stand for?", "a": "graphical processing unit"},
    {"q": "What does RAM stand for?", "a": "random access memory"},
    {"q": "What does ROM stand for?", "a": "read only memory"},
    {"q": "Mouse is an input or output device?", "a": "input"}
]


@app.route("/api/questions", methods=["GET"])
@swag_from({
    "responses": {
        200: {
            "description": "List of questions",
            "examples": {
                "application/json": questions
            }
        }
    }
})
def get_questions():
    return jsonify(questions)


@app.route("/api/submit", methods=["POST"])
@swag_from({
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "answers": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    ],
    "responses": {
        200: {
            "description": "Quiz submission result",
            "examples": {
                "application/json": {
                    "name": "John",
                    "score": 4,
                    "percentage": 80.0
                }
            }
        }
    }
})
def submit():
    data = request.json
    answers = data.get("answers")
    name = data.get("name", "Unknown")

    score = sum(
        1 for i, question in enumerate(questions)
        if answers[i].strip().lower() == question["a"]
    )

    percentage = (score / len(questions)) * 100

    res = Result(name=name, score=score, total=len(questions), percentage=percentage)
    db.session.add(res)
    db.session.commit()

    return jsonify({"name": name, "score": score, "percentage": percentage})


@app.route("/api/results", methods=["GET"])
@swag_from({
    "responses": {
        200: {
            "description": "Latest quiz results",
            "schema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "score": {"type": "integer"},
                        "total": {"type": "integer"},
                        "percentage": {"type": "number"}
                    }
                }
            }
        }
    }
})
def get_results():
    results = Result.query.order_by(Result.id.desc()).limit(20).all()
    return jsonify([{
        "name": r.name,
        "score": r.score,
        "total": r.total,
        "percentage": r.percentage
    } for r in results])


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)