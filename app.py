"""
Strata enquiry triage web UI — run: flask --app app run
Or: python app.py
"""

from strata_triage.web import create_app

app = create_app()

if __name__ == "__main__":
    from strata_triage.web.app import run_dev

    run_dev()
