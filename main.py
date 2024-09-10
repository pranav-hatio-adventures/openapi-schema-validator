from flask import Flask, render_template, request
import json
from schemas.check_device_status_response_schema import (
    check_device_status_response_schema,
)
from utils.validationUtils import ValidationUtils as v
from schemas.reverify_servergen_id_response_schema import (
    reverify_servergen_id_response_schema,
)
from schemas.user_bank_account_list_response_schema import (
    user_bank_account_list_response_schema,
)
from schemas.check_vpa_response_schema import check_vpa_response_schema
from schemas.register_response_schema import register_response_schema

app = Flask(__name__)


def add_additional_properties_false(schema):

    if isinstance(schema, dict):
        if schema.get("type") == "object" and "additionalProperties" not in schema:
            schema["additionalProperties"] = False

        for key, value in schema.items():
            add_additional_properties_false(value)

    elif isinstance(schema, list):
        for item in schema:
            add_additional_properties_false(item)

    return schema


def extract_schema_for_method(schema, path, method):
    """Extract request and response schemas for a specific path and method."""
    path_item = schema.get("paths", {}).get(path, {})
    method_item = path_item.get(method.lower(), {})

    # Extract request body schema
    request_body = (
        method_item.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", None)
    )

    # Extract response schema (assuming we want 200 OK responses)
    response_body = (
        method_item.get("responses", {})
        .get("200", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", None)
    )

    # Dereference the schemas
    if request_body:
        request_body = dereference_schema(schema, request_body)

    if response_body:
        response_body = dereference_schema(schema, response_body)

    return {"request_schema": request_body, "response_schema": response_body}


def dereference_schema(root_schema, schema):
    """Recursively dereference $ref in the schema, handling oneOf, allOf, anyOf, and not."""
    if isinstance(schema, dict) and "$ref" in schema:
        # Dereference the $ref
        ref_path = schema["$ref"]
        ref_parts = ref_path.split("/")
        ref_section = ref_parts[1]  # "components"
        ref_type = ref_parts[2]      # "schemas"
        ref_name = ref_parts[3]      # "SomeSchema"

        # Get the actual referenced schema
        referenced_schema = root_schema.get(ref_section, {}).get(ref_type, {}).get(ref_name, {})

        # Recursively dereference the referenced schema
        return dereference_schema(root_schema, referenced_schema)

    # Handle combinators (oneOf, allOf, anyOf, not)
    if isinstance(schema, dict):
        if "oneOf" in schema:
            # Replace oneOf with the first schema in the list, and dereference it
            first_schema = schema["oneOf"][0]
            return dereference_schema(root_schema, first_schema)
        
        if "allOf" in schema:
            # Recursively dereference each schema in allOf and merge them
            first_schema = schema["allOf"][0]
            return dereference_schema(root_schema, first_schema)
        
        if "anyOf" in schema:
            # Recursively dereference each schema in anyOf
            schema["anyOf"] = [dereference_schema(root_schema, sub_schema) for sub_schema in schema["anyOf"]]
        
        if "not" in schema:
            # Recursively dereference the schema in not
            schema["not"] = dereference_schema(root_schema, schema["not"])

        # Recursively process other fields (for nested schemas)
        return {key: dereference_schema(root_schema, value) for key, value in schema.items()}
    
    elif isinstance(schema, list):
        return [dereference_schema(root_schema, item) for item in schema]
    
    return schema


@app.route("/", methods=["GET", "POST"])
def index():
    openapi_schema = None
    api_info = []
    selected_schema = None
    selected_path = None
    selected_method = None

    if request.method == "POST":
        # Get the OpenAPI schema from the user input
        schema_data = request.form.get("openapi_schema", "")
        selected_path = request.form.get("selected_path")
        selected_method = request.form.get("selected_method")

        try:
            # Parse the input schema as JSON
            openapi_schema = json.loads(schema_data)
            paths = openapi_schema.get("paths", {})

            # Extract available paths and methods for selection
            api_info = [
                {"path": path, "methods": list(methods.keys())}
                for path, methods in paths.items()
            ]

            # If the user has selected a path and method, extract the relevant schema
            if selected_path and selected_method:
                selected_schema = extract_schema_for_method(
                    openapi_schema, selected_path, selected_method
                )
        except json.JSONDecodeError:
            # Handle JSON parse error
            openapi_schema = None

    return render_template(
        "index.html",
        api_info=api_info,
        selected_schema=selected_schema,
        selected_path=selected_path,
        selected_method=selected_method,
    )


if __name__ == "__main__":
    app.run(debug=True)
