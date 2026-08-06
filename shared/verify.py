from shared import paths

registry_schema = {
    "version": int,
    "architecture": str,
    "instructions": [
        {
            "name": str,
            "auto_managed": bool,
            "opclass": str,
            "oplat": int,
            "fu_count": int,
            "pipelined": bool,
            "funct3": int,
            "funct7": int,
        }
    ],
}

gem5_opclass_schema = {
    "gem5_version": str,
    "source_file": str,
    "opclasses": list
}

changes_schema = {
    "version": int,
    "architecture": str,
    "instructions": [
        {
            "new": bool,
            "removed": bool,
            "changed": bool,
        }
    ]

}


def validate_schema(obj, schema, name="root"):
    """
    Validate `obj` (a dict/list, e.g. loaded from JSON or YAML) against `schema`.

    Schema conventions:
      - dict  -> obj must be a dict with those keys, each validated recursively
      - list  -> single-element list; obj must be a list whose items each match schema[0]
      - type  -> obj must be an instance of that type (int, str, bool, float, ...)

    Raises ValueError with the full breadcrumb path to the failing field.
    Returns None if valid.
    """
    if isinstance(schema, dict):
        if not isinstance(obj, dict):
            raise ValueError(f"'{name}': expected object (dict), got {type(obj).__name__}")
        for key, subschema in schema.items():
            if key not in obj:
                raise ValueError(f"'{name}.{key}': missing required key")
            validate_schema(obj[key], subschema, name=f"{name}.{key}")
        extra = set(obj.keys()) - set(schema.keys())
        if extra:
            raise ValueError(f"'{name}': unexpected key(s) not in schema: {extra}")

    elif isinstance(schema, list):
        if len(schema) != 1:
            raise ValueError(f"'{name}': schema list must contain exactly one item-type definition")
        if not isinstance(obj, list):
            raise ValueError(f"'{name}': expected list, got {type(obj).__name__}")
        item_schema = schema[0]
        for i, item in enumerate(obj):
            validate_schema(item, item_schema, name=f"{name}[{i}]")

    elif isinstance(schema, type):
        if schema is int and isinstance(obj, bool):
            raise ValueError(f"'{name}': expected int, got bool")
        elif schema is float and isinstance(obj, int) and not isinstance(obj, bool):
            pass  # allow plain ints to satisfy a float field
        elif not isinstance(obj, schema):
            raise ValueError(f"'{name}': expected {schema.__name__}, got {type(obj).__name__} ({obj!r})")

    else:
        raise ValueError(f"'{name}': invalid schema definition {schema!r}")