import os

import rdflib
from lxml import etree

current_dir = os.path.curdir
RAILML32_TEST_DATA_FOLDER = os.path.join(current_dir, 'TestData')
RAILML32_OUTPUT_FOLDER = os.path.join(current_dir, 'TestOutputs')  # default output directory


class Railml32ToRsm:
    def __init__(self):
        self._root = None
        self._output_path = ''
        self._output_directory = None
        self._graph = None

    def process_railML32(self, input_path: str, output_directory: str, short_name: str = ''):
        """
        :param short_name:
        :param input_path:
        :param output_directory:
        :return:
        """
        self.output_directory = output_directory
        self._output_path = self._generate_output_path(output_directory, input_path, short_name)
        self.load_source(input_path)
        self._graph = rdflib.Graph()
        self._save_graph_to_file()

    def load_source(self, path: str) -> str:
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
        """
        Property to get the output directory. Ensures the directory exists (creates it if necessary).
        :return: str, the output directory path
        """
        if self._output_directory:
            if not os.path.exists(self._output_directory):
                try:
                    os.makedirs(self._output_directory)
                except OSError as e:
                    print(f"ERROR: could not create {self._output_directory}: {e}")
        else:
            self._output_directory = RAILML32_OUTPUT_FOLDER
        return self._output_directory

    @output_directory.setter
    def output_directory(self, value: str):
        self._output_directory = value

    @staticmethod
    def _generate_output_path(output_directory: str, input_path: str, short_name: str) -> str:
        if short_name:
            return os.path.join(output_directory, f"{short_name}.ttl")
        else:
            return os.path.join(output_directory, f"{os.path.basename(input_path)}.ttl")


if __name__ == "__main__":
    railml32_to_rsm = Railml32ToRsm()
    railml32_to_rsm.process_railML32(
        os.path.join(RAILML32_TEST_DATA_FOLDER, "railML32_test_file.xml"),
        RAILML32_OUTPUT_FOLDER,
        "test_file"
    )
    print(f"RSM file generated at {railml32_to_rsm._output_path}")
