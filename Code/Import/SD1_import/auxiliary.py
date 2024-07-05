def millimeters_to_meters(some_length_in_integer_mm: str) -> str:
    """
    From string expressing lengths in integer millimeter, to string expressing the same in meters (decimal notation)
    :param some_length_in_integer_mm:
    :return:
    """
    return some_length_in_integer_mm[:-3] + '.' + some_length_in_integer_mm[-3:]


def replace_strings(input_string: str, string_mapping: dict, reverse_mapping: bool = False) -> str:
    """
    Function to replace strings based on a given mapping dictionary.
    :param input_string: any string
    :param string_mapping: dictionary of terms, key = a term, value = its equivalent
    :param reverse_mapping: if False, the keys will be looked up in input_string and replaced by the corresp. value;
    if True, the values will be looked up in input_string and replaced by the keys
    :return a string which is a copy of the input string, but for all replacements
    """
    for original, replacement in string_mapping.items():
        input_string = input_string.replace((original if not reverse_mapping else replacement),
                                            (replacement if not reverse_mapping else original))
    return input_string
