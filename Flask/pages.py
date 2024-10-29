from flask import Blueprint, request, render_template_string
from flask import render_template
from markdown import markdown
import markdown2

from Flask.templates import *

bp = Blueprint('pages', __name__, template_folder = 'templates')


@bp.route('/')
def home():
    return '''
    <!doctype html>
    <html lang="en">
      <body>
        <h1>SemanticRSM test site</h1>
        <nav>
          <ul>
            <li><a href="/about">About</a></li>
            <li><a href="/drawio_to_rdf">DrawIO to RDF</a></li>
          </ul>
        </nav>
      </body>
    </html>
    '''


@bp.route('/about')
def about():
    import os
    #current_folder = os.path.dirname(os.path.abspath(__file__))
    with open('templates/about.md', 'r') as file:
        markdown_content = file.read()
    html_content = markdown2.markdown(markdown_content, extras=["break-on-newline"])

    # Define CSS styles for styling the content
    css_styles = """
    <style>
        body {
            font-family: 'Helvetica Neue', Arial, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            margin: 30px;
            color: #333;
        }

        h1, h2, h3, h4, h5, h6 {
            font-weight: bold;
            margin-top: 20px;
        }

        p {
            margin: 10px 0;
        }

        a {
            color: #3498db;
        }

        a:hover {
            color: #2980b9;
        }

        ul, ol {
            margin: 10px 0;
            padding-left: 20px;
        }

        blockquote {
            border-left: 4px solid #ddd;
            padding-left: 20px;
            color: #666;
        }

        code, pre {
            background-color: #f5f5f5;
            border-radius: 4px;
            padding: 4px 8px;
        }
    </style>
    """

    # Embed the CSS styles within the HTML content
    html_with_styles = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>About</title>
        {css_styles}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    return render_template_string(html_with_styles)

@bp.route('/drawio_to_rdf', methods=['GET', 'POST'])
def drawIO_to_RSM():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.xml'):
            file_content = file.read().decode('utf-8')
            # result = drawIO_to_RDF(file_content)
            result = None
            return result
    return '''
    <!doctype html>
    <html lang="en">
      <body>
        <h1>Drag and drop a drawIO file (xml format)</h1>
        <form method="post" enctype="multipart/form-data">
          <input type="file" name="file">
          <input type="submit" value="Upload">
        </form>
      </body>
    </html>
    '''
