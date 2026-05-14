from __future__ import annotations

import os

from flask import Flask, jsonify, render_template, request

from strata_triage.config import PROJECT_ROOT, Settings
from strata_triage.errors import LLMProviderError, MissingApiKeyError, TriageError
from strata_triage.facade import process_enquiry

DEFAULT_SAMPLE = """Hi, I'm on the committee for 12 Ocean View Parade. We're not happy with how long
it's taking to get quotes for the lift upgrade and owners are getting frustrated.
Can someone call me back this week? My number is 04xx xxx xxx.
"""


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or Settings()
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "templates"),
    )
    app.config["SETTINGS"] = settings

    @app.route("/", methods=["GET", "POST"])
    def index():
        result = None
        error = None
        enquiry_text: str | None = None

        if request.method == "POST":
            enquiry_text = request.form.get("enquiry", "")
            try:
                result = process_enquiry(enquiry_text)
            except TriageError as e:
                error = e.user_message

        return render_template(
            "index.html",
            enquiry_text=enquiry_text,
            result=result,
            error=error,
            default_sample=DEFAULT_SAMPLE,
            mock_mode=settings.triage_use_mock,
        )

    @app.post("/api/triage")
    def api_triage():
        body = request.get_json(silent=True) or {}
        text = body.get("enquiry", "")
        if not isinstance(text, str):
            return jsonify(error="Field 'enquiry' must be a string."), 400
        try:
            out = process_enquiry(text)
        except MissingApiKeyError as e:
            return jsonify(error=e.user_message), 503
        except LLMProviderError as e:
            status = 502
            if e.http_status == 401:
                status = 401
            elif e.http_status == 429:
                status = 429
            elif e.http_status is not None and e.http_status >= 500:
                status = 502
            return jsonify(error=e.user_message, code=e.provider_code), status
        except TriageError as e:
            return jsonify(error=e.user_message), 400
        return jsonify(out)

    return app


def run_dev() -> None:
    port = int(os.environ.get("PORT", "5000"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
