"""Write CESM (CDEPS) style <comp>.streams.xml files.

Shared by the generate_<comp>_streams.py scripts. Any field not given is
written blank, so fill it in afterwards or pass it in.
"""

import xml.etree.ElementTree as ET

# Tags inside each <stream_info>, in the order CESM writes them.
STREAM_FIELDS = [
    "taxmode",
    "tintalgo",
    "readmode",
    "mapalgo",
    "dtlimit",
    "year_first",
    "year_last",
    "year_align",
    "vectors",
    "meshfile",
    "lev_dimname",
]


def blank_streams(groups):
    """One blank stream per group, mapping stream name -> model field names.

    File variable names are left blank: ("", "Sa_u") writes <var>  Sa_u</var>.
    """
    return [
        {"name": name, "datavars": [("", field) for field in fields]}
        for name, fields in groups.items()
    ]


def missing_fields(streams, required):
    """Required model fields that no stream provides."""
    provided = {
        name_in_model
        for stream in streams
        for _, name_in_model in stream.get("datavars", [])
    }
    return [field for field in required if field not in provided]


def write_streams(streams, path, required=()):
    """Write a list of stream dicts to a <comp>.streams.xml file.

    Each dict can have "name", "datafiles" (list of paths), "datavars"
    (list of (name_in_file, name_in_model) pairs), "offset", and any key in
    STREAM_FIELDS. Anything missing is written blank. Raises ValueError if a
    model field in `required` isn't in any stream's datavars.
    """
    missing = missing_fields(streams, required)
    if missing:
        raise ValueError(f"Streams are missing required fields: {missing}")

    root = ET.Element("file", id="stream", version="2.0")
    for stream in streams:
        info = ET.SubElement(root, "stream_info", name=stream.get("name", ""))
        for field in STREAM_FIELDS:
            ET.SubElement(info, field).text = str(stream.get(field, ""))
        datafiles = ET.SubElement(info, "datafiles")
        for datafile in stream.get("datafiles", []):
            ET.SubElement(datafiles, "file").text = str(datafile)
        datavars = ET.SubElement(info, "datavars")
        for name_in_file, name_in_model in stream.get("datavars", []):
            ET.SubElement(datavars, "var").text = f"{name_in_file}  {name_in_model}"
        ET.SubElement(info, "offset").text = str(stream.get("offset", ""))

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(path, xml_declaration=True, encoding="utf-8", short_empty_elements=False)
