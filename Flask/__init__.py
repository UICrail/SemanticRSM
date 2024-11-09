# HTML interface for testing of sRSM functionalities
# Just run this and navigate using your usual browser.

from flask import Flask

import pages


def create_app():
    rsm_test_app = Flask(__name__)
    rsm_test_app.register_blueprint(pages.bp)
    return rsm_test_app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=8000, debug=True)
