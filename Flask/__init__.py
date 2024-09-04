from flask import Flask, render_template, request, redirect, url_for
import pages
def create_app():
    app = Flask(__name__)
    app.register_blueprint(pages.bp)
    return app



if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=8000, debug=True)