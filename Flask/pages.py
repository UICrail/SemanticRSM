from flask import Blueprint, request, render_template_string
import markdown2

bp = Blueprint('pages', __name__, template_folder='templates')

CSS_STYLES = """
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


def get_html_from_markdown(file_path):
    with open(file_path, 'r') as file:
        markdown_content = file.read()
    return markdown2.markdown(markdown_content, extras=["break-on-newline"])


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
    html_content = get_html_from_markdown('templates/about.md')
    html_with_styles = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>About</title>
        {CSS_STYLES}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    return render_template_string(html_with_styles)


@bp.route('/drawio_to_rdf', methods=['GET', 'POST'])
def drawio_to_rdf():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file_content = file.read().decode('utf-8')
            if file.filename.endswith('.xml'):
                # result = drawIO_to_RDF(file_content)
                result = f"""
                <!doctype html>
                <html lang="en">
                    <body>
                        <h1>Uploaded drawIO file content</h1>
                        <pre>{file_content}</pre>
                    </body>
                </html>
                """
                return result
            elif file.filename.endswith('.svg'):
                result = f"""
                <!doctype html>
                <html lang="en">
                    <body>
                        <h1>Uploaded SVG file</h1>
                        {file_content}
                    </body>
                </html>
                """
                return result
    return '''
    <!doctype html>
    <html lang="en">
      <body>
        <h1>Drag and drop a drawIO file (xml format) or an SVG file</h1>
        <form method="post" enctype="multipart/form-data">
          <input type="file" name="file">
          <input type="submit" value="Upload">
        </form>
      </body>
    </html>
    '''
