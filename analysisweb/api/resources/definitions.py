schemas = dict()

schemas["File"] = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "file": {"type": "string", "format": "binary"},
    },
}

schemas["Measurement"] = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "label": {"type": "string"},
        "start_date": {"type": "string", "format": "date-time"},
        "end_date": {"type": "string", "format": "date-time"},
        "meta_data": {"type": "string"},
        "files": {
            "type": "object",
            "properties": {"label": {"type": "string"}, "path": {"type": "string"}},
        },
        "jobs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "integer"}, "label": {"type": "string"}},
            },
        },
    },
}

schemas["AnalysisInput"] = {
    "type": "object",
    "properties": {
        "label": {"type": "string"},
        "type": {"type": "string", "enum": ["value", "file"]},
    },
}

schemas["AnalysisOutput"] = {
    "type": "object",
    "properties": {
        "label": {"type": "string"},
        "type": {"type": "string", "enum": ["table", "figure"]},
    },
}

schemas["Analysis"] = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "label": {"type": "string"},
        "syx_file": {"type": "string"},
        "meta_data": {"type": "string"},
        "input": {
            "type": "array",
            "items": {"$ref": "#/components/schemas/AnalysisInput"},
        },
        "output": {
            "type": "array",
            "items": {"$ref": "#/components/schemas/AnalysisOutput"},
        },
        "jobs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "integer"}, "label": {"type": "string"}},
            },
        },
    },
}

schemas["Job"] = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "label": {"type": "string"},
        "status": {"type": "string"},
        "log": {"type": "string"},
        "analysis": {
            "type": "object",
            "properties": {"id": {"type": "integer"}, "label": {"type": "string"}},
        },
        "measurement": {
            "type": "object",
            "properties": {"id": {"type": "integer"}, "label": {"type": "string"}},
        },
        "date": {"type": "string", "format": "date-time"},
        "input": {"type": "array", "items": {"type": "string"}},
        "output": {"type": "array", "items": {"type": "string"}},
        "reports": {"type": "array", "items": {"type": "string"}},
    },
}

swagger_template = {
    "openapi": "3.0.0",
    "info": {
        "title": "Analysis Web",
        "description": "This is an API for the Analysis Web platform, "
        "providing resources to manipulate measurements, analyses and jobs",
        "version": "0.0.1",
        "contact": {"email": "samuel.genheden@combine.se"},
    },
    "tags": [{"name": "measurements"}, {"name": "analyses"}, {"name": "jobs"}],
    "components": {"schemas": schemas},
}
