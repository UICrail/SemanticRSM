# Styles defined by drawIO
DASHED_LINE = "dashed=1"
# Constants for characterizing designer-defined artefacts.
SLIP_SWITCH_KEY = "slip switch"
SLIP_SWITCH_STYLE = [DASHED_LINE]
ARTEFACTS = {SLIP_SWITCH_KEY: SLIP_SWITCH_STYLE}
# File extensions
DRAWIO_XML_EXTENSION = '.drawio.xml'  # input file; do not change (it is produced by drawIO export)
OSM_JSON_EXTENSION = '.osm.json'  # output file

# helper function for determining what the artefact stands for, only looking at its style
def classify_artefact_by_style(observed_styles: str) -> str | None:
    """
    If all observed styles match the first encountered artefact in ARTEFACTS, this function will consider that
    the observed styles denote such an artefact.
    This means that more styles can be added by the user (ex. : color...).
    The programmer should however be aware that his own ARTEFACT classification may be ambiguous...
    :param observed_styles:
    :return: inferred artefact category (index in ARTEFACTS), or None if not found
    """
    # TODO: consider sth more sophisticated, using a taxonomy-like dict where the artefact categories are the leaves, not the index
    # or (better) a multi-dimensional sieve
    for artefact, artefact_styles in ARTEFACTS.items():
        for artefact_style in artefact_styles:
            if artefact_style not in observed_styles:
                continue
            return artefact
    return None