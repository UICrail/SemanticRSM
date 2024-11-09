import os
from html import escape

import markdown2
from flask import Blueprint, render_template_string, send_from_directory, request

from Graph_transformation.full_transformation import transform_osm_to_rsm
from Import.drawIO_import.drawIO_XML_to_OSMgeojson import OSM_GEOJSON_EXTENSION

# Constants
LOCAL_FOLDER = os.path.dirname(__file__)
OUTPUT_FOLDER = os.path.join(LOCAL_FOLDER, 'output')
bp = Blueprint('pages', __name__, template_folder='templates')

uploaded_files = []
output_file = []

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

HOME_PAGE_HTML = ''' 
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
    </a>Import railway networks from Open Street Map and
    generate the corresponding sRSM representation.</li>
    </ul>
    <h2>Everything else</h2>
    <p>For any question or suggestion, please use the Semantic RSM
    GitHub repository and post an issue there.</p>
    <p>Concerning data from <a href="https://www.openstreetmap.org" target="_blank">OpenStreetMap</a>: these data are made available under ODbL (see <a href="https://opendatacommons.org/licenses/odbl/" target="_blank">this page</a>).</p>
    <p><a href="/about">About the present site</a></p>
    <p><br>
    </p>
    <p><i>this version: Nov. 8th, 2024</i><br>
    </p>
    <button onclick="erase_and_quit();">Erase temporary files and quit</button>
    <script>
        function erase_and_quit() {
            fetch('/erase_and_quit', { method: 'POST' }).then(response => {
                if (response.ok) {
                    window.close();
                }
            });
        }
    </script>
    </nav>
</body>
'''


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
    html = get_html_content_with_styles('sRSM demo', HOME_PAGE_HTML, include_back_button=False)
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
    def save_uploaded_file(file, file_path):
        print('Saving file to ', file_path)
        file.save(file_path)
        uploaded_files.append(file_path)

    def process_xml_file(file_path):
        from Code.Import.drawIO_import import drawIO_XML_to_OSMgeojson as dxo
        osm_generator = dxo.OSMgeojsonGenerator()
        osm_generator.convert_drawio_to_osm(file_path, OUTPUT_FOLDER)
        osm_file_path = file_path.split('.')[0] + OSM_GEOJSON_EXTENSION
        uploaded_files.append(osm_file_path)
        result = transform_osm_to_rsm(osm_file_path, 'output', OUTPUT_FOLDER)
        if result:
            escaped_result = escape(result)
            rdf_turtle_path = os.path.join(OUTPUT_FOLDER, 'output.ttl')
            with open(rdf_turtle_path, 'w') as rdf_file:
                rdf_file.write(result)
            uploaded_files.append(rdf_turtle_path)
            return f"""<h2>Resulting sRSM file, in RDF Turtle format:</h2>
                       <div style="max-height: 300px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; margin-top: 20px; font-size: 80%;">
                           <pre>{escaped_result}</pre>
                       </div>
                       <a href="/download_rdf" download class="button">Download RDF Turtle file</a>"""
        return ""

    def process_svg_file(file_path):
        with open(file_path, 'r', encoding='utf-8') as svg_file:
            file_content = svg_file.read()
        return f"""
                <div style="max-height: 300px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; margin-top: 20px;">
                    {file_content}
                </div>
                """

    result_html = ""
    selected_file_name = "No file selected"

    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file:
            selected_file_name = uploaded_file.filename
            temporary_file_path = os.path.join(OUTPUT_FOLDER, selected_file_name)
            save_uploaded_file(uploaded_file, temporary_file_path)

            if selected_file_name.endswith('.xml'):
                result_html = process_xml_file(temporary_file_path)
            elif selected_file_name.endswith('.svg'):
                result_html = process_svg_file(temporary_file_path)

    drawio_content = render_drawio_form(selected_file_name, result_html)
    html_response = get_html_content_with_styles('drawio to RDF', drawio_content)

    return html_response


def render_drawio_form(selected_file_name, result_html):
    return f"""
    <h1>Select a drawIO file (xml format or SVG format)</h1>
    <form method="post" enctype="multipart/form-data" onchange="document.getElementById('file-name').textContent = this.files[0].name">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    <p>Selected file: <span id="file-name">{selected_file_name}</span></p>
    {result_html}
    """


@bp.route('/osm_to_rdf', methods=['GET', 'POST'])
def osm_to_rdf():
    def generate_progress_script():
        return f"""
        <script>
            function showProgressBar(time) {{
                document.getElementById('progress-bar').style.display = 'block';
                let progress = document.getElementById('progress');
                let progressText = document.getElementById('progress-text');
                let nearlyThereText = document.getElementById('nearly-there');
                let value = 0;
                let interval = setInterval(() => {{
                    if (value < 100) {{
                        value += 100 / time;
                        progress.value = value;
                        progressText.textContent = "Processing... " + Math.min(Math.floor(value), 100) + "%";
                    }} else {{
                        progressText.textContent = "Processing... 100%";
                        nearlyThereText.style.display = 'inline';
                        clearInterval(interval);
                    }}
                }}, 1000); // 1000 ms intervals
            }}
        </script>
        """

    def generate_convert_button(osm_file_path, estimated_time):
        return f"""
        <form method="post" action="/convert_osm_to_sRSM" onsubmit="showProgressBar({estimated_time})">
            <input type='hidden' name='file_path' value='{osm_file_path}'>
            <input type="submit" value="Convert to sRSM">
        </form>
        <div id="progress-bar" style="display: none; margin-top: 10px;">
            <progress value="0" max="100" id="progress"></progress>
            <span id="progress-text">Processing...</span>
            <span id="nearly-there" style="display: none;"> (well, nearly there...)</span>
        </div>
        {generate_progress_script()}
        """

    osm_file_name = "No file selected"
    if request.method == 'POST':
        uploaded_file = request.files['file']

        if uploaded_file:
            osm_file_name = uploaded_file.filename
            file_size_mb = len(uploaded_file.read()) / (1024 * 1024)
            uploaded_file.seek(0)
            osm_file_path = os.path.join(OUTPUT_FOLDER, uploaded_file.filename)
            uploaded_files.append(osm_file_path)
            uploaded_file.save(osm_file_path)
            estimated_conversion_time = int(file_size_mb * 0.95 + 0.8) ** 2

            convert_button = generate_convert_button(osm_file_path, estimated_conversion_time)
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
      OSM parlance). Export it in GeoJSON. The GeoJSON file will then be transformed into a RailSystemModel file
      in RDF/Turtle format.<br>
    </p>
    <p>At present, there is only one available option: crossings can be
      all instantiated as diamond crossings (FR: traversée simple, DE:
      [einfache] Kreuzung) or as double slip crossings (FR: traversée
      jonction double, DE: Doppelkreuzweiche).<br>
    </p>
    <p>(on hold) The software also returns a representation of the transformed
      network in KML format, for visual inspection in QGIS, Google
      Earth, or similar.<br>
    </p>
    <h2>OpenStreetMap queries</h2>
    <p>Ways get queried and nodes are obtained by recursion. This is how you get the whole Austrian
      network:</p>
    <blockquote>
      <p>area[name="Österreich"];<br>
        way[railway=rail](area);<br>
        (._;&gt;;);<br>
        out;<br>
      </p>
    </blockquote>
    <p>And this is how to get the network that is contained in a boundary
      box:<br>
    </p>
    <blockquote>
      <p>way[railway=rail](&#123;&#123;bbox&#125;&#125;);<br>
        (._;&gt;;);<br>
        out;<br>
    </blockquote>
    <h2>There you go...<br>
    </h2>
    <form method="post" enctype="multipart/form-data" onchange="document.getElementById('file-name').textContent = this.files[0].name">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    <p>Selected file: <span id="file-name">{osm_file_name}</span></p>
    {convert_button}
    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            if (document.referrer.includes('/convert_osm_to_sRSM')) {{
                document.getElementById('progress-bar').style.display = 'none';
            }}
        }});
    </script>
    """
    html = get_html_content_with_styles('OSM to RDF', osm_content)
    return html


@bp.route('/convert_osm_to_sRSM', methods=['POST'])
def osm_to_ttl():
    import time
    file_path = request.form['file_path']
    file_name = os.path.basename(file_path)

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    start_time = time.time()
    result = transform_osm_to_rsm(file_path, 'converted_osm', OUTPUT_FOLDER)
    end_time = time.time()

    transformation_time = end_time - start_time

    if result:
        escaped_result = escape(result)
        rdf_turtle_path = os.path.join(OUTPUT_FOLDER, 'output.ttl')
        with open(rdf_turtle_path, 'w') as rdf_file:
            rdf_file.write(result)
        uploaded_files.append(rdf_turtle_path)
        result_html = f"""<h2>Resulting sRSM file, in RDF Turtle format:</h2>
        <p>Source file: {file_name}</p>
        <div style="max-height: 300px; overflow-y: scroll; border: 1px solid #ccc; padding: 10px; margin-top: 20px; font-size: 80%;">
            <pre>{escaped_result}</pre>
        </div>
        <p>Transformation time: {transformation_time:.2f} seconds | Input file size: {file_size_mb:.2f} MB</p>
        <a href="/download_rdf" download class="button">Download RDF Turtle file</a>"""
    else:
        result_html = "<p>An error occurred during conversion.</p>"

    html = get_html_content_with_styles('Converted RDF', result_html)
    return render_template_string(html)


@bp.route('/download_rdf')
def download_rdf():
    return send_from_directory(OUTPUT_FOLDER, 'output.ttl', as_attachment=True)


@bp.route('/erase_and_quit', methods=['POST'])
def erase_and_quit():
    for file_path in uploaded_files:
        if os.path.exists(file_path):
            os.remove(file_path)
    uploaded_files.clear()
    return '', 200
