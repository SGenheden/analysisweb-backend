
schemas = dict()

schemas["File"] = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string"
        },
        "file": {
            "type": "string",
            "format": "binary"
        }
    }
}

schemas["Measurement"] = {
    "type": "object",
    "properties": {
        "id": {
            "type": "integer",
        },
        "label": {
            "type": "string",
        },
        "start_date": {
            "type": "string",
            "format": "date-time"
        },
        "end_date": {
            "type": "string",
            "format": "date-time"
        },
        "meta_data": {
            "type": "string"
        },
        "files": {
            "type": "object",
            "properties": {
                "label": {
                    "type": "string"
                },
                "path": {
                    "type": "string"
                }
            }
        },
        "jobs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer"
                    },
                    "label": {
                        "type": "string"
                    }
                }
            }
        }
    }
}

schemas["FlowInput"] = {
    "type": "object",
    "properties": {
        "label": {
            "type": "string"
        },
        "type": {
            "type": "string",
            "enum": ["value", "file"]
        }
    }
}

schemas[ "FlowOutput"] = {
    "type": "object",
    "properties": {
        "label": {
            "type": "string"
        },
        "type": {
            "type": "string",
            "enum": ["table", "figure"]
        }
    }
}

schemas["Flow"] = {
    "type": "object",
    "properties": {
        "id": {
            "type": "integer",
        },
        "label": {
            "type": "string",
        },
        "syx_file": {
            "type": "string",
        },
        "meta_data": {
            "type": "string"
        },
        "input": {
            "type": "array",
            "items": {
                "$ref": "#/components/schemas/FlowInput"
            }
        },
        "output": {
            "type": "array",
            "items": {
                "$ref": "#/components/schemas/FlowOutput"
            }
        },
        "jobs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer"
                    },
                    "label": {
                        "type": "string"
                    }
                }
            }
        }
    }
}

schemas["Job"] = {
    "type": "object",
    "properties": {
        "id": {
            "type": "integer",
        },
        "label": {
            "type": "string",
        },
        "status": {
            "type": "string",
        },
        "log": {
            "type": "string",
        },
        "flow": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer"
                },
                "label": {
                    "type": "string"
                }
            }
        },
        "measurement": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer"
                },
                "label": {
                    "type": "string"
                }
            }
        },
        "date": {
            "type": "string",
            "format": "date-time"
        },
        "input": {
            "type": "array",
            "items": {
                "type": "string",
            }
        },
        "output": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "reports": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    }
}

swagger_template = {
    "openapi": "3.0.0",
    "info": {
        "title": "Analysis Web",
        "description": "This is an API for the Analysis Web platform, "
                       "providing resources to manipulate measurements, analyses and jobs",
        "version": "0.0.1",
        "contact": {
            "email": "samuel.genheden@combine.se"
        }
    },
    "tags" : [
        {"name": "measurements"},
        {"name": "flows"},
        {"name": "jobs"}
    ],
    "components": {
        "schemas": schemas
    }
}
