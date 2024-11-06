# not further investigated for the time being

from xml.etree import ElementTree as ET


class SVGParser():
    """Turns the original drawIO diagram (saved as SVG) into a JSON OSM file."""

    def __init__(self, input_file):
        self.input_file = input_file
        self.elements = []

    def parse_svg(self):
        """Parse the SVG file and extract elements based on drawIO conventions."""
        tree = ET.parse(self.input_file)
        root = tree.getroot()

        for element in root.findall('.//{http://www.w3.org/2000/svg}g'):
            # Extract required attributes from the SVG 'g' (group) element
            self.elements.append(self._parse_element(element))

    def _parse_element(self, element):
        """Parse an individual SVG element and convert it to the desired format."""
        # This example extracts just the 'id' attribute and text content.
        # Modify the logic as needed based on your SVG structure and drawIO conventions.
        return {
            'id': element.get('id'),
            'text': element.find('.//{http://www.w3.org/2000/svg}text').text if element.find(
                './/{http://www.w3.org/2000/svg}text') is not None else ''
        }

    def generate(self):
        """Main method to generate output."""
        self.parse_svg()
        # Further processing of self.elements as needed
        return self.elements


if __name__ == '__main__':
    file_path = 'TestData/241023-Simple_Example+RTC-121'
    generator = SVGParser(file_path + '.drawio.xml.svg')
    output = generator.generate()
