import cv2
import numpy as np
from pathlib import Path

from src.template import Template
from src.defaults import CONFIG_DEFAULTS
from src.utils.parsing import get_concatenated_response


def process_image_bytes(
    image_bytes: bytes,
    filename: str,
    template_path: Path,
):
    np_arr = np.frombuffer(image_bytes, np.uint8)
    in_omr = cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)

    if in_omr is None:
        raise ValueError("Invalid image file")

    tuning_config = CONFIG_DEFAULTS
    template = Template(template_path, tuning_config)

    in_omr = template.image_instance_ops.apply_preprocessors(
        filename, in_omr, template
    )

    if in_omr is None:
        raise RuntimeError("Preprocessing failed")

    response_dict, _, multi_marked, _ = template.image_instance_ops.read_omr_response(
        template=template,
        image=in_omr,
        name=filename,
        save_dir=None,
    )

    omr_response = get_concatenated_response(response_dict, template)

    return {
        "responses": omr_response,
        "columns": template.output_columns,
        "multi_marked": multi_marked,
    }

def result_to_json(result: dict):
    questions = []
    roll_digits = []

    for col in result["columns"]:
        value = result["responses"].get(col, "")

        if col.startswith("q"):
            questions.append({
                "qno": int(col[1:]),
                "ans": value
            })

        elif col.startswith("roll"):
            roll_digits.append((int(col[4:]), value))

    # Sort roll digits correctly
    roll_digits.sort(key=lambda x: x[0])

    shifted_digits = []
    for _, d in roll_digits:
        if d == "":
            shifted_digits.append("/")  # missing bubble
        else:
            shifted_digits.append(str((int(d) + 1) % 10))

    roll_number = "".join(shifted_digits)

    return {
        "questions": sorted(questions, key=lambda x: x["qno"]),
        "roll_number": roll_number,
        "multi_marked": result.get("multi_marked", False)
    }

