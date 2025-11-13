from edf.block import Document
from edf.datafy import datafy_document
from edf.parser import read_document
from edf.schema import Schema, analyze_schema_document


def loads_document(data: str) -> Document:
    return read_document(data)


def loads_data(data: str, schema: Schema) -> list:
    doc = read_document(data)
    return datafy_document(schema, doc)


def loads_schema(data: str) -> Schema:
    doc = read_document(data)
    return analyze_schema_document(doc)
