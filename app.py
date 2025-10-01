import hashlib
import json
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import ValidationError
from models import SurveySubmission, StoredSurveyRecord

app = Flask(__name__)
CORS(app, resources={r"/v1/*": {"origins": "*"}})


@app.route("/ping", methods=["GET"])
def ping():
    """Simple health check endpoint."""
    return jsonify({
        "status": "ok",
        "message": "API is alive",
        "utc_time": datetime.now(timezone.utc).isoformat()
    })


@app.post("/v1/survey")
def submit_survey():
    # Step 1: parse JSON
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "invalid_json", "detail": "Body must be application/json"}), 400

    # Step 2: validate payload using Pydantic
    try:
        submission = SurveySubmission(**payload)
    except ValidationError as ve:
        return jsonify({"error": "validation_error", "detail": ve.errors()}), 422

    # Step 3: prepare data for storage (hash sensitive fields)
    data_to_store = submission.dict()
    data_to_store["email"] = hashlib.sha256(data_to_store["email"].encode("utf-8")).hexdigest()
    data_to_store["age"] = hashlib.sha256(str(data_to_store["age"]).encode("utf-8")).hexdigest()

    # Step 4: create StoredSurveyRecord (raw types, Pydantic validation)
    record = StoredSurveyRecord(
        **submission.dict(),
        received_at=datetime.now(timezone.utc),
        ip=request.headers.get("X-Forwarded-For", request.remote_addr or "")
    )

    # Step 5: save hashed record to disk
    with open("survey.ndjson", "a") as f:
        f.write(json.dumps(data_to_store) + "\n")

    # Step 6: respond
    return jsonify({"status": "ok"}), 201


if __name__ == "__main__":
    app.run(port=5000, debug=True)
