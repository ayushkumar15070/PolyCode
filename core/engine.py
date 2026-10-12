
from core.parser import parse_code
from core.executor import execute_block
from core.runtime import Runtime


class PolyCodeEngine:
    def __init__(self):
        self.runtime = Runtime()

    def run(self, code):
        self.runtime.clear()

        blocks = parse_code(code)
        output_parts = []

        if not blocks:
            return "PolyCode: No supported language blocks found."

        for index, block in enumerate(blocks, start=1):
            language = block["language"]
            source = block["code"]

            stdout, stderr, variables = execute_block(
                language,
                source,
                self.runtime.get_all_variables()
            )

            if stdout:
                output_parts.append(stdout.rstrip())

            if stderr:
                output_parts.append(
                    f"[{language.upper()} DIAGNOSTICS]\n{stderr.rstrip()}"
                )
                break

            self.runtime.load_variables(variables)

        return "\n".join(part for part in output_parts if part)
