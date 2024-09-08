from edf.block import Document
from edf.datafy import datafy_document
from edf.lark_parser import read
from edf.schema import Schema, analyze_schema_document


def loads_document(data: str) -> Document:
    return read(data)


def loads_data(data: str, schema: Schema) -> list:
    doc = read(data)
    return datafy_document(schema, doc)


def loads_schema(data: str) -> Schema:
    doc = read(data)
    return analyze_schema_document(doc)
