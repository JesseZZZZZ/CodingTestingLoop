# CodingTestingLoop

This repository contains the implementation of the coding-testing loop used for repository-level code generation from scratch in RepoZero. The workflow follows the Agentic Code-Test Evolution (ACE) idea from the paper: a coding agent first generates a target repository, a testing agent generates executable test inputs, the source repository is executed as the oracle, and any mismatch is fed back to the coding agent for iterative refinement.

Authors: Zhaoxi Zhang, Aidi Lin, Junhan Gong

## Overview

RepoZero evaluates whether LLM agents can synthesize complete repositories rather than isolated functions or single-file patches. In the Py2JS setting, the agent receives Python source files and is asked to reimplement their behavior in Node.js with strict output equivalence. The code in `src/` provides the runnable implementation of this loop:

- `src/run_terminal_agent.py`: a lightweight terminal-style agent wrapper over the Qianfan/OpenAI-compatible chat API. It supports tool calling through `execute_shell`, tracks token usage, and restricts direct imports of external npm packages when executing commands.
- `src/run_all_loop.py`: the OpenHands-bash-style ACE runner for RepoZero-Py2JS. It builds Python-to-JavaScript generation prompts, asks the model to synthesize test arguments, runs Python and Node.js programs on the same generated cases, and retries refinement when outputs differ.
- `src/run_all_loop_mini.py`: the Mini-SWE-Agent variant of the same coding-testing-refining workflow. It invokes a local `mini` executable, runs multiple files in parallel, stores generated `.mjs` outputs, and reports success/failure statistics.

## Dataset

The `data/` directory should be mounted from the RepoZero benchmark repository:

```bash
git clone https://github.com/jessezzzzz/RepoZero data
```

The scripts expect RepoZero-style Python test files under the dataset root. In `src/run_all_loop_mini.py`, the default path is:

```text
./dataset
```

In `src/run_all_loop.py`, the default path is:

```text
/home/work/RepoArena/dataset
```

Adjust `dataset_root` in the corresponding script, or mount/link the RepoZero data to the expected path before running. For example:

```bash
ln -s data/Py2JS dataset
```

The generated JavaScript repositories and test cases are written to `output_loop/` or `output_loop_mini/`, depending on the runner.

## Installation

Install the Python dependencies used by the agent wrappers:

```bash
pip install openai anthropic
```

The Py2JS evaluation also requires:

- Python 3
- Node.js with ES module support
- Access to the configured Qianfan/OpenAI-compatible API endpoint
- Mini-SWE-Agent, if using `src/run_all_loop_mini.py`

Before running, configure the model endpoint and credentials in the runner you use:

- `API_URL` and `API_KEY` in `src/run_terminal_agent.py`
- `model_name`, `api_base`, and `provider` in `src/run_all_loop_mini.py`
- `model_name` and `max_retries` in `src/run_all_loop.py`

## Running

Run the direct coding-testing loop:

```bash
python src/run_all_loop.py 10
```

The numeric argument controls the number of concurrent worker processes. If omitted, `src/run_all_loop.py` defaults to 2 workers. You can also set:

```bash
NUM_PROCESSES=10 python src/run_all_loop.py
```

Run the Mini-SWE-Agent version:

```bash
python src/run_all_loop_mini.py
```

The Mini-SWE-Agent runner currently uses `num_processes = 10` in the script. Edit that value if you need a different concurrency level.

## ACE Workflow Implemented Here

For each Python file in the RepoZero Py2JS dataset, the runner performs the following steps:

1. Read the source Python file and construct a prompt requiring pure Node.js/ESM output.
2. Ask a testing agent to generate command-line arguments that cover normal, boundary, and error-like inputs.
3. Execute the Python source file on each generated input to obtain oracle outputs.
4. Execute the generated JavaScript `.mjs` file on the same inputs.
5. Compare stdout and exit codes exactly.
6. If the outputs differ, feed the failure message back to the coding agent and retry.

This mirrors the paper's central observation: executable, source-oracle-based test-time feedback improves repository-level synthesis by targeting corner cases that are difficult to solve in a single generation pass.

## Output Layout

The direct runner writes to:

```text
output_loop/<model_name>_retry<max_retries>/
  packages/      # generated library modules
  testfiles/     # generated .mjs entry files
  test_cases/    # generated ACE test arguments
```

The Mini-SWE-Agent runner writes to:

```text
output_loop_mini/<model_name>_retry<max_retries>/
  packages/
  testfiles/
  test_cases/
```

## Notes

The implementation is intentionally strict about cross-language integrity: generated solutions should not call back into Python, should not use external npm dependencies, and should match the source repository's observable command-line behavior at string level. This is aligned with RepoZero's black-box evaluation protocol and its focus on semantic correctness rather than mere runnability.
