
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MARKER = "__POLYCODE_VARS__"
TIMEOUT = 10


def _extract_variables(stdout):
    variables = {}

    lines = stdout.splitlines()
    clean_lines = []

    for line in lines:
        if line.startswith(MARKER):
            try:
                variables.update(
                    json.loads(line[len(MARKER):])
                )
            except json.JSONDecodeError:
                pass
        else:
            clean_lines.append(line)

    return "\n".join(clean_lines), variables


def _run(command, cwd, timeout=TIMEOUT):
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        return "", f"Execution timed out after {timeout} seconds."

    except OSError as error:
        return "", f"Could not start process: {error}"


def _python_value(value):
    if isinstance(value, (int, float, bool, str, list, dict)):
        return repr(value)

    return "None"


def execute_python(code, variables):
    with tempfile.TemporaryDirectory(prefix="polycode_") as folder:
        folder = Path(folder)

        source = folder / "program.py"
        runner = folder / "runner.py"

        injected = "\n".join(
            f"{name} = {_python_value(value)}"
            for name, value in variables.items()
            if re.fullmatch(r"[A-Za-z_]\w*", name)
            and not name.startswith("__")
        )

        source.write_text(
            injected + "\n" + code,
            encoding="utf-8"
        )

        runner.write_text(
            """
import json
import runpy
import sys

MARKER = "__POLYCODE_VARS__"
namespace = runpy.run_path(sys.argv[1])

def supported(value):
    return (
        value is None
        or isinstance(value, (bool, int, float, str, list, dict))
    )

exported = {
    key: value
    for key, value in namespace.items()
    if not key.startswith("_") and supported(value)
}

print(MARKER + json.dumps(exported))
""",
            encoding="utf-8"
        )

        stdout, stderr = _run(
            [sys.executable, str(runner), str(source)],
            str(folder)
        )

        stdout, found = _extract_variables(stdout)

        return stdout, stderr, found


def _cpp_literal(value):
    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, (int, float)):
        return repr(value)

    return None



def execute_cpp(code, variables):
    compiler = shutil.which("g++")

    if not compiler:
        return "", "g++ compiler not found.", {}

    with tempfile.TemporaryDirectory(prefix="polycode_") as folder:
        folder = Path(folder)

        source = folder / "program.cpp"
        executable = folder / (
            "program.exe" if os.name == "nt" else "program"
        )

        declared = set(
            re.findall(
                r"\b(?:int|float|double|long|bool|char)\s+([A-Za-z_]\w*)",
                code
            )
        )

        injected = []

        for name, value in variables.items():
            if not re.fullmatch(r"[A-Za-z_]\w*", name):
                continue

            if name in declared:
                continue

            literal = _cpp_literal(value)

            if literal is not None:
                injected.append(f"auto {name} = {literal};")

        has_main = bool(re.search(r"\bmain\s*\(", code))

        if has_main:
            final_code = (
                "#include <iostream>\n"
                "#include <string>\n"
                "using namespace std;\n"
                + "\n".join(injected)
                + "\n"
                + code
            )
        else:
            declarations = re.findall(
                r"\b(?:int|float|double|long|bool)\s+([A-Za-z_]\w*)\s*=",
                code
            )

            capture = []

            for name in dict.fromkeys(declarations):
                capture.append(
                    f'cout << endl << "{MARKER}" '
                    f'<< "{{\\"{name}\\":" << {name} '
                    f'<< "}}" << endl;'
                )

            final_code = (
                "#include <iostream>\n"
                "#include <string>\n"
                "using namespace std;\n"
                "int main() {\n"
                + "\n".join(injected)
                + "\n"
                + code
                + "\n"
                + "\n".join(capture)
                + "\nreturn 0;\n}\n"
            )

        source.write_text(final_code, encoding="utf-8")

        stdout, stderr = _run(
            [compiler, str(source), "-o", str(executable)],
            str(folder),
            timeout=30
        )

        if stderr and not executable.exists():
            return "", stderr, {}

        if not executable.exists():
            return "", "C++ compilation failed.", {}

        run_stdout, run_stderr = _run(
            [str(executable)],
            str(folder)
        )

        clean_stdout, found = _extract_variables(run_stdout)

        return clean_stdout, stderr + run_stderr, found




def execute_javascript(code, variables):
    node = shutil.which("node")

    if not node:
        return "", "Node.js runtime not found.", {}

    with tempfile.TemporaryDirectory(prefix="polycode_") as folder:
        folder = Path(folder)

        source = folder / "program.js"
        runner = folder / "runner.js"

        source.write_text(code, encoding="utf-8")

        runner.write_text(
            """
const fs = require("fs");
const vm = require("vm");

const MARKER = "__POLYCODE_VARS__";
const initial = JSON.parse(process.argv[3]);
const context = { ...initial, console };

try {
    vm.runInContext(
        fs.readFileSync(process.argv[2], "utf8"),
        vm.createContext(context),
        { timeout: 10000 }
    );

    const exported = {};

    for (const [key, value] of Object.entries(context)) {
        if (key === "console") continue;

        if (
            value === null ||
            ["string", "number", "boolean"].includes(typeof value) ||
            Array.isArray(value) ||
            (typeof value === "object" && value !== null)
        ) {
            try {
                JSON.stringify(value);
                exported[key] = value;
            } catch {}
        }
    }

    console.log(MARKER + JSON.stringify(exported));
} catch (error) {
    console.error(error.stack || String(error));
    process.exitCode = 1;
}
""",
            encoding="utf-8"
        )

        stdout, stderr = _run(
            [
                node,
                str(runner),
                str(source),
                json.dumps(variables)
            ],
            str(folder)
        )

        stdout, found = _extract_variables(stdout)

        return stdout, stderr, found

    
def execute_block(language, code, variables=None):
    variables = variables or {}

    executors = {
        "python": execute_python,
        "cpp": execute_cpp,
        "javascript": execute_javascript
    }

    executor = executors.get(language.lower())

    if executor is None:
        return "", f"Unsupported language: {language}", {}

    return executor(code, variables)
