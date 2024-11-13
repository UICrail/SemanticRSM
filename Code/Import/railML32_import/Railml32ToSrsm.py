import os

import rdflib
from lxml import etree

current_dir = os.path.curdir
RAILML32_TEST_DATA_FOLDER = os.path.join(current_dir, 'TestData')
RAILML32_OUTPUT_FOLDER = os.path.join(current_dir, 'TestOutputs')  # default output directory


class Railml32ToRsm:
    def __init__(self):
        self._root = None
        self._input_path = None
        self._output_directory = None
        self._output_path = None
        self._graph = None

    def process_railML32(self, input_path: str, output_directory: str, short_name: str = ''):
        """
        :param short_name: for the output file. If not provided, the input file base name shall be kept.
        :param input_path:
        :param output_directory:
        :return:
        """
        self._input_path = input_path
        self.output_directory = output_directory
        self.output_path = short_name
        self._load_source(input_path)
        self._graph = rdflib.Graph()
        self._save_graph_to_file()

    def _load_source(self, path: str) -> str:
        """
        :param path: str, path to the source code file to be loaded
        :return: str, message indicating success or failure
        """
        try:
            tree = etree.parse(path)
            self._root = tree.getroot()
            return f"INFO: successfully loaded railML3.2 file: {path}"
        except (OSError, etree.XMLSyntaxError) as e:
            return f"ERROR: Error loading XML file: {e}"

    def _save_graph_to_file(self):
        """
        Serializes the RDFLib graph to a Turtle (.ttl) file in the output directory.
        """
        try:
            self._graph.serialize(destination=self._output_path, format='turtle')
            print(f"INFO: RDF graph successfully saved to {self._output_path}")
        except Exception as e:
            print(f"ERROR: Failed to save RDF graph to {self._output_path}: {e}")

    @property
    def output_directory(self):
        return self._output_directory

    @output_directory.setter
    def output_directory(self, value: str):
        if value:
            self._output_directory = value
        else:
            self._output_directory = RAILML32_OUTPUT_FOLDER
        if not os.path.exists(self._output_directory):
            try:
                os.makedirs(self._output_directory)
            except OSError as e:
                print(f"ERROR: could not create {self._output_directory}: {e}")

    @property
    def output_path(self):
        return self._output_path

    @output_path.setter
    def output_path(self, value: str):
        if value:
            self._output_path = os.path.join(self.output_directory, f"{value}.ttl")
        else:
            self._output_path = os.path.join(self.output_directory, f"{os.path.basename(value)}.ttl")


if __name__ == "__main__":
    railml32_to_rsm = Railml32ToRsm()
    railml32_to_rsm.process_railML32(
        os.path.join(RAILML32_TEST_DATA_FOLDER, "railML32_test_file.xml"),
        RAILML32_OUTPUT_FOLDER,
        "test_file"
    )
    print(f"RSM file generated at {railml32_to_rsm._output_path}")
