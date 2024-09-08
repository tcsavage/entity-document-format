# Entity Document Format

> [!WARNING]
> This project is in a very early stage of development. Do not trust it. Do not use it. Do not look at it. Do not think about it. Do not even think about thinking about it. Or do. But you've been warned.

This library implements a simple format for human-readable documents that can be used to describe entities in a tree structure. The format is designed to be easy for humans to read and write. It might be slightly harder for machines to process however.

EDF takes inspiration from many places, but primarily HCL (HashiCorp Configuration Language) and Python.

## Running the example

```bash
edf to-json example.edf -s example-schema.edf
```

## Conversion to data

An EDF document can be converted to standard Python dicts and lists in two different ways:

- conversion to canonical form 
- schema-guided conversion

Conversion to canonical form requires no schema and is lossless. It is the most straightforward way to convert an EDF document to a Python data structure. The resulting data structure is a nested list of dicts and lists. The function to do this is `edf.canonical.canonicalize_json`.

For example, the following EDF document:

```edf
foo test {
    foo = "bar"

    inner {
        bar = 42
    }

    inner {
        bar = 141
    }
}
```

Will be converted to the following Python data structure:

```python
[
  {
    "$kind": "foo",
    "$name": "test",
    "$children": [
      {
        "$kind": "inner",
        "$name": None,
        "$children": [],
        "bar": 42
      },
      {
        "$kind": "inner",
        "$name": None,
        "$children": [],
        "bar": 141
      }
    ],
    "foo": "bar"
  }
]
```

Schema-guided conversion requires a schema to describe how the EDF document should be converted. The schema is its own EDF document that describes each of the available block types and their attributes. The function to do this is `edf.datafy.datafy_document` (`edf.io.loads_data` provides a convenient shorthand to parse and datafy).

For example, the following schema:

```edf
block foo {
    attribute foo {
        type = "string"
    }
    
    sub_block {
        field = "inners"
        
        block inner {
            anonymous = true
            attribute bar {
                type = "number"
            }
        }
    }
}
```

Describes the same document as above. However, when this schema is used to "datafy" the document, the following Python data structure is produced:

```python
[
  {
    "id": "test",
    "foo": "bar",
    "inners": [
      {
        "bar": 42
      },
      {
        "bar": 141
      }
    ]
  }
]
```
