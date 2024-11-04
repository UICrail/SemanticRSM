import os
from html import escape

import markdown2
from flask import Blueprint, request, render_template_string, send_from_directory

from Graph_transformation.full_transformation import transform_osm_to_rsm
from Import.drawIO_import.drawIO_XML_to_OSMgeojson import OSM_GEOJSON_EXTENSION

# Constants
LOCAL_FOLDER = os.path.dirname(__file__)
TEMPORARY_FILES_FOLDER = os.path.join(LOCAL_FOLDER, 'temporary_files')
bp = Blueprint('pages', __name__, template_folder='templates')

CSS_STYLES = """
<style>
    body {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 12px;
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
        <a href="https://github.com/UICrail/SemanticRSM/" target="_blank">Semantic
        RSM GitHub repository hosted by UIC</a><br>
        </p>
        <h2>Proposed functions<br>
        </h2>
        <nav>
        <ul>
        <li><a href="/drawio_to_rdf">drawIO to RDF<br>
        </a>Draw a network schema (using <a
        href="https://www.drawio.com/" target="_blank">the free
        diagramming software draw.io</a>) and get its sRSM
        representation as an RDF/Turtle file.</li>
        <li><a href="/osm_to_rdf">OSM to RDF<br>
        </a>Import railway networks from Open Street Map networks and
        generate the corresponding sRSM representation.</li>
        </ul>
        <h2>Everything else</h2>
        <p>For any question or suggestion, please use the Semantic RSM
        GitHub repository and post an issue there.</p>
        <p>Concerning data from <a href="https://www.openstreetmap.org" target="_blank">OpenStreetMap</a>: these data are made available under ODbL (see <a href="https://opendatacommons.org/licenses/odbl/" target="_blank">this page</a>).</p>
        <p><a href="/about">About the present site</a></p>
        <p><br>
        </p>
        <p><i>this version: Nov. 4th, 2024</i><br>
        </p>
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
                with open(file_path, 'r', encoding='utf-8') as svg_file:
                    file_content = svg_file.read()
                result_html = f"""
                <div style="max-height: 300px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; margin-top: 20px;">
                    {file_content}
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


@bp.route('/osm_to_rdf', methods=['GET', 'POST'])
def osm_to_rdf():
    osm_file_name = "No file selected"
    if request.method == 'POST':
        file = request.files['file']
        if file:
            osm_file_name = file.filename
            osm_file_path = os.path.join(TEMPORARY_FILES_FOLDER, file.filename)
            file.save(osm_file_path)
            convert_button = f"""
            <form method="post" action="/convert_to_sRSM">
                <input type='hidden' name='file_path' value='{osm_file_path}'>
                <input type="submit" value="Convert to sRSM">
            </form>
            """
        else:
            convert_button = ""
    else:
        convert_button = ""

    osm_content = f"""
        <h1>Convert an OpenStreetMap railway network into a semantic RSM
      file</h1>
    <h2>Usage<br>
    </h2>
    <p>The OSM railway network can be obtained using a query in <a
        href="https://overpass-turbo.eu/" target="_blank"
        moz-do-not-send="true">Overpass Turbo</a>.<br>
    </p>
    <p>The resulting OSM file will contain railway nodes and ways (in
      OSM parlance). Export it in GeoJSON. It will then be transformed into a RailSystemModel file
      in RDF/Turtle format.<br>
    </p>
    <p>At present, there is only one available option: crossings can be
      all instantiated as diamond crossings (FR: traversée simple, DE:
      [einfache] Kreuzung) or as double slip crossings (FR: traversée
      jonction double, DE: Doppelkreuzweiche).<br>
    </p>
    <p>The software also returns a representation of the transformed
      network in KML format, for visual inspection in QGIS, Google
      Earth, or similar.<br>
    </p>
    <h2>OpenStreetMap queries</h2>
    <p>Using Overpass Turbo, this is how you get the whole Austrian
      network:</p>
    <blockquote>
      <p>area[name="Österreich"];<br>
        way[railway=rail](area);<br>
        (._;&gt;;);<br>
        out;<br>
      </p>
    </blockquote>
    <p>Primarily, ways get queried and nodes are obtained by recursion.
      And this is how to get the network that is contained in a boundary
      box:<br>
    </p>
    <blockquote>
      <p>way[railway=rail]({{bbox}});<br>
        (._;&gt;;);<br>
        out;<br>
      </p>
    </blockquote>
    <h2>There you go...<br>
    </h2>
    <form method="post" enctype="multipart/form-data" onchange="document.getElementById('file-name').textContent = this.files[0].name">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    <p>Selected file: <span id="file-name">{osm_file_name}</span></p>
    {convert_button}
    """
    html = get_html_content_with_styles('OSM to RDF', osm_content)
    return html


@bp.route('/convert_to_sRSM', methods=['POST'])
def osm_to_ttl():
    file_path = request.form['file_path']
    result = transform_osm_to_rsm(file_path, 'converted_osm', TEMPORARY_FILES_FOLDER)
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
    else:
        result_html = "<p>An error occurred during conversion.</p>"

    html = get_html_content_with_styles('Converted RDF', result_html)
    return render_template_string(html)


@bp.route('/download_rdf')
def download_rdf():
    return send_from_directory(TEMPORARY_FILES_FOLDER, 'output.rdf', as_attachment=True)
