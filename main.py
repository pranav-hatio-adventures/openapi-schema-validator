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


@app.route("/", methods=["GET", "POST"])
def index():
    errors = []
    result = None

    if request.method == "POST":
        # Get the JSON data from the form
        json_data = request.form["json_data"]

        try:
            # Convert the input string to a Python dictionary
            instance = json.loads(json_data)

            # Validate the JSON instance against the schema
            errors = v.validate_openapi_schema(
                schema=add_additional_properties_false(
                    schema=register_response_schema
                ),
                instance=instance,
            )

            if len(errors) == 0:
                result = "JSON is valid!"

        except json.JSONDecodeError:
            errors = [
                "Invalid JSON format. Please ensure the input is a valid JSON string."
            ]

    return render_template("index.html", errors=errors, result=result)


if __name__ == "__main__":
    app.run(debug=True)
