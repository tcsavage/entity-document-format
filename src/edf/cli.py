from typing import TextIO

import click


@click.group("edf")
def edf_group():
    pass


@edf_group.command("to-json")
@click.argument("input", type=click.File("r"))
@click.option("--output", "-o", type=click.File("w"), default="-")
@click.option("--schema", "-s", type=click.File("r"))
@click.option("--indent", "-i", type=int, default=2)
@click.option("--compact", "-c", is_flag=True, help="Produce compact JSON output")
@click.option("--object", is_flag=True, help="Interpret the input as an object instead of a list")
def edf_to_json_cmd(input: TextIO, output: TextIO, schema: TextIO, indent: int, compact: bool, object: bool):
    import json
    from edf.canonical import canonicalize_json
    from edf.io import loads_schema, loads_data, loads_document

    if schema:
        schema_loaded = loads_schema(schema.read())
        data = loads_data(input.read(), schema_loaded)
    else:
        doc = loads_document(input.read())
        data = canonicalize_json(doc)

    if object:
        if len(data) != 1:
            raise ValueError("Expected a single object")
        data = data[0]
    json.dump(data, output, indent=None if compact else indent)


@edf_group.command("parse-schema")
@click.argument("input", type=click.File("r"))
@click.option("--output", "-o", type=click.File("w"), default="-")
def edf_parse_schema_cmd(input: TextIO, output: TextIO):
    from pprint import pprint
    from edf.io import loads_schema

    schema = loads_schema(input.read())
    pprint(schema, stream=output)


@edf_group.command("to-xml")
@click.argument("input", type=click.File("r"))
@click.option("--output", "-o", type=click.File("w"), default="-")
def edf_to_xml_cmd(input: TextIO, output: TextIO):
    from edf.io import loads_document
    from edf.xml import document_to_xml_string

    doc = loads_document(input.read())
    output.write(document_to_xml_string(doc))


if __name__ == "__main__":
    edf_group()
