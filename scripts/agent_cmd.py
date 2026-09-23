#!/usr/bin/env python3
"""Generic `--agent-cmd` wrapper for model CLIs.

    python harness.py universe run --agent-cmd \
      "python scripts/agent_cmd.py --prompt {prompt} --output {output} -- claude -p"

Runs the model command with the prompt on stdin. If the model wrote `--output`
itself (CLIs with file tools), nothing else happens. Otherwise the last JSON
object in its stdout (a ```json fenced block, or the outermost {...}) is written
to `--output`. The wrapper never edits the JSON: the harness validates it next
with `harness.py validate`, and a malformed report fails the ticker, not the batch.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def extract_json(text):
    """The last parsable JSON object in model output, or None."""
    for block in reversed(re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.S)):
        try:
            return json.loads(block)
        except ValueError:
            continue
    start = text.find('{')
    end = text.rfind('}')
    while start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except ValueError:
            start = text.find('{', start + 1)
    return None


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--prompt', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--timeout', type=float, default=3600)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('give the model command after --')
    output = Path(args.output)
    before = digest(output)
    prompt = Path(args.prompt).read_text(encoding='utf-8')
    done = subprocess.run(command, input=prompt, capture_output=True, text=True, encoding='utf-8',
                          errors='replace', timeout=args.timeout)
    sys.stderr.write(done.stderr[-4000:])
    if done.returncode != 0:
        print(f'model command exited {done.returncode}', file=sys.stderr)
        return done.returncode
    if digest(output) not in (None, before):
        return 0                                   # the model wrote the file itself
    report = extract_json(done.stdout)
    if report is None:
        print('no JSON object found in model output', file=sys.stderr)
        return 3
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_name(f'.{output.name}.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, output)
    return 0


if __name__ == '__main__':
    sys.exit(main())
