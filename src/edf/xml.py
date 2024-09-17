from xml.dom import minidom as xml

from edf.block import Block, Document


def block_to_xml_element(block: Block, owner_doc: xml.Document) -> xml.Element:
    e = owner_doc.createElement(block.kind)
    if block.name:
        e.setAttribute("id", block.name)
    if block.value:
        e.nodeValue = str(block.value)
    else:
        for attr_name, attr_value in block.attributes.items():
            e.setAttribute(attr_name, str(attr_value))
        for child in block.children:
            e.appendChild(block_to_xml_element(child, owner_doc))
    return e


def document_to_xml_document(doc: Document) -> xml.Document:
    d = xml.Document()
    root = d.createElement("document")
    d.appendChild(root)
    for block in doc:
        root.appendChild(block_to_xml_element(block, d))
    return d


def document_to_xml_string(doc: Document) -> str:
    return document_to_xml_document(doc).toprettyxml(indent="  ")
