import os
import markdown2
from flask import Blueprint, request, render_template_string, send_from_directory
from Graph_transformation.full_transformation import transform_osm_to_rsm
from Import.drawIO_import.drawIO_XML_to_OSMgeojson import OSM_GEOJSON_EXTENSION
from html import escape

# Constants
LOCAL_FOLDER = os.path.dirname(__file__)
TEMPORARY_FILES_FOLDER = os.path.join(LOCAL_FOLDER, 'temporary_files')
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
    .back-button {
        margin-top: 20px;
    }
</style>
"""

BACK_TO_HOME_BUTTON = """
<button class="back-button" onclick="window.location.href='/'">Back to sRSM Home</button>
"""


# Helper Functions
def get_html_content_with_styles(title, body_content, include_back_button=True):
    back_button_html = BACK_TO_HOME_BUTTON if include_back_button else ""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        {CSS_STYLES}
    </head>
    <body>
        {body_content}
        <div style="margin-top: 20px;">
            {back_button_html}
        </div>
    </body>
    </html>
    """


def get_html_from_markdown(file_path):
    with open(file_path, 'r') as file:
        markdown_content = file.read()
    return markdown2.markdown(markdown_content, extras=["break-on-newline"])


# Routes

@bp.route('/')
def home():
    home_content = '''
    <body>
        <h1>SemanticRSM test and demo site</h1>
        <p>This site is based on the Semantic RSM (sRSM) repository:<br>
        <a href="https://github.com/UICrail/SemanticRSM/" target="_blank">Semantic RSM GitHub repository hosted by
        UIC</a><br>
        </p>
        <nav>
        <ul>
        <li><a href="/about">About the present site<br>
        </a></li>
        <li><a href="/drawio_to_rdf">drawIO to RDF<br>
        </a>Draw a network schema (using <a
        href="https://www.drawio.com/" target="_blank">the free diagramming software
        draw.io</a>) and get its sRSM representation as an
        RDF/Turtle file</li>
        <li>import railway networks from Open Street Map networks and
        generate the corresponding sRSM representation (page under
        preparation)</li>
        </ul>
        <p>For any question or suggestion, please use the Semantic RSM
        GitHub repository and post an issue.<br>
        </p>
        <p><i>this version: Nov. 1st, 2024</i><br>
        </p>
        <ul>
        </ul>
        </nav>
    </body>
    '''
    html = get_html_content_with_styles('sRSM demo', home_content, include_back_button=False)
    return html


@bp.route('/about')
def about():
    html_content = get_html_from_markdown('templates/about.md')
    about_content = f"""
    {html_content}
    """
    html = get_html_content_with_styles('About', about_content)
    return render_template_string(html)


@bp.route('/drawio_to_rdf', methods=['GET', 'POST'])
def drawio_to_rdf():
    result_html = ""
    file_name = "No file selected"
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file_name = file.filename
            file_path = os.path.join(TEMPORARY_FILES_FOLDER, file.filename)
            print('Saving XML file to ', file_path)
            file.save(file_path)
            file_content = file.read().decode('utf-8')
            if file.filename.endswith('.xml'):
                from Code.Import.drawIO_import import drawIO_XML_to_OSMgeojson as dxo
                osm_generator = dxo.OSMgeojsonGenerator()
                osm_generator.convert_drawio_to_osm(file_path)
                file_path = file_path.split('.')[0] + OSM_GEOJSON_EXTENSION
                result = transform_osm_to_rsm(file_path, 'Pierre_Tane_test_121_via_flask', TEMPORARY_FILES_FOLDER)
                if result:
                    escaped_result = escape(result)
                    rdf_turtle_path = os.path.join(TEMPORARY_FILES_FOLDER, 'output.rdf')
                    with open(rdf_turtle_path, 'w') as rdf_file:
                        rdf_file.write(result)
                    result_html = f"""<h2>Resulting sRSM file, in RDF Turtle format:</h2>
                    <div style="max-height: 300px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; margin-top: 20px; font-size: 80%;">
                        <pre>{escaped_result}</pre>
                    </div>
                    <a href="/download_rdf" download class="button">Download RDF Turtle file</a>"""
            elif file.filename.endswith('.svg'):
                result_html = f"""
                <div style="max-height: 300px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; margin-top: 20px;">
                    <pre>{file_content}</pre>
                </div>
                """

    drawio_content = f"""
    <h1>Select a drawIO file (xml format or SVG format)</h1>
    <form method="post" enctype="multipart/form-data" onchange="document.getElementById('file-name').textContent = this.files[0].name">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    <p>Selected file: <span id="file-name">{file_name}</span></p>
    {result_html}
    """
    html = get_html_content_with_styles('drawio to RDF', drawio_content)
    return html


@bp.route('/download_rdf')
def download_rdf():
    return send_from_directory(TEMPORARY_FILES_FOLDER, 'output.rdf', as_attachment=True)
