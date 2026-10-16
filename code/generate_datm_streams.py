"""Generate a CESM (CDEPS) style datm.streams.xml file.

Any field not given is written blank, so fill it in afterwards or pass it in.
"""

import argparse
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


def write_datm_streams(streams, path):
    """Write a list of stream dicts to a datm.streams.xml file.

    Each dict can have "name", "datafiles" (list of paths), "datavars"
    (list of (name_in_file, name_in_model) pairs), "offset", and any key in
    STREAM_FIELDS. Anything missing is written blank.
    """
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", default="datm.streams.xml")
    args = parser.parse_args()
    write_datm_streams([{}], args.output)
