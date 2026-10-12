LANGUAGE_MARKERS = {
    "@python": "python",
    "@cpp": "cpp",
    "@javascript": "javascript",
}


def parse_code(code):
    """
    Parse a PolyCode program into separate language blocks.

    Returns:
        list of dictionaries containing:
        - language
        - code
    """

    lines = code.splitlines()

    blocks = []
    current_language = None
    current_code = []

    for line in lines:
        stripped_line = line.strip()

        # Check whether this line starts a new language block
        if stripped_line in LANGUAGE_MARKERS:

            # Save the previous block
            if current_language is not None:
                blocks.append({
                    "language": current_language,
                    "code": "\n".join(current_code).strip()
                })

            # Start the new block
            current_language = LANGUAGE_MARKERS[stripped_line]
            current_code = []

        else:
            # Add normal code to the current block
            if current_language is not None:
                current_code.append(line)

    # Save the final block
    if current_language is not None:
        blocks.append({
            "language": current_language,
            "code": "\n".join(current_code).strip()
        })

    return blocks