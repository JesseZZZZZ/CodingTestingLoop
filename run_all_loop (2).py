from run_terminal_agent import run_reasoning_agent
import os
import sys
import json
import subprocess
import pathlib
import re
import multiprocessing

model_name = "deepseek-v3.1-250821"
max_retries = 4
valid_ids = ['boltons/test10.py', 'fractions/test14.py', 'deepdiff/test16.py', 'bech32/test4.py', 'idna/test13.py', 'base58/test6.py', 'bech32/test12.py', 'canonicaljson/test20.py', 'idna/test6.py', 'jsonschema/test7.py', 'schedule/test9.py', 'bidict/test5.py', 'mpmath/test4.py', 'furl/test5.py', 'furl/test11.py', 'bidict/test13.py', 'bech32/test2.py', 'networkx/test14.py', 'yaml/test16.py', 'bech32/test9.py', 'idna/test9.py', 'base58/test1.py', 'networkx/test5.py', 'moneyed/test6.py', 'bencoder/test7.py', 'pyaes/test10.py', 'markdown/test13.py', 'networkx/test4.py', 'bencoder/test15.py', 'jsonschema/test15.py', 'networkx/test16.py', 'markdown/test19.py', 'base58/test2.py', 'rsa/test15.py', 'construct/test12.py', 'rsa/test19.py', 'whoosh/test2.py', 'moneyed/test17.py', 'networkx/test13.py', 'networkx/test7.py', 'mpmath/test12.py', 'rsa/test8.py', 'canonicaljson/test14.py', 'networkx/test3.py', 'base58/test7.py', 'boltons/test14.py', 'boltons/test3.py', 'idna/test4.py', 'boltons/test11.py', 'mpmath/test1.py', 'base58/test19.py', 'moneyed/test3.py', 'bech32/test13.py', 'construct/test16.py', 'pyaes/test17.py', 'sqlparse/test4.py', 'jose/test7.py', 'idna/test18.py', 'jose/test13.py', 'whoosh/test7.py', 'bidict/test10.py', 'pyaes/test2.py', 'whoosh/test6.py', 'yaml/test2.py', 'deepdiff/test3.py', 'canonicaljson/test8.py', 'whoosh/test1.py', 'bencoder/test6.py', 'bidict/test17.py', 'moneyed/test15.py', 'pyaes/test12.py', 'idna/test11.py', 'deepdiff/test18.py', 'sqlparse/test2.py', 'rsa/test5.py', 'yaml/test11.py', 'canonicaljson/test11.py', 'schedule/test13.py', 'schedule/test2.py', 'jsonschema/test8.py', 'mpmath/test19.py', 'pyaes/test9.py', 'pyaes/test19.py', 'fractions/test15.py', 'markdown/test11.py', 'bidict/test16.py', 'construct/test20.py', 'yaml/test6.py', 'mpmath/test13.py', 'mpmath/test18.py', 'idna/test12.py', 'bech32/test15.py', 'yaml/test12.py', 'boltons/test15.py', 'deepdiff/test10.py', 'rsa/test16.py', 'boltons/test4.py', 'furl/test12.py', 'moneyed/test12.py', 'whoosh/test20.py', 'schedule/test19.py', 'bidict/test3.py', 'base58/test17.py', 'fractions/test2.py', 'moneyed/test7.py', 'whoosh/test3.py', 'mpmath/test7.py', 'construct/test17.py', 'idna/test15.py', 'mpmath/test17.py', 'markdown/test4.py', 'mpmath/test11.py', 'bech32/test1.py', 'bidict/test12.py', 'bencoder/test5.py', 'mpmath/test16.py', 'jose/test15.py', 'pyaes/test4.py', 'canonicaljson/test1.py', 'bech32/test14.py', 'moneyed/test14.py', 'jsonschema/test9.py', 'fractions/test19.py', 'construct/test19.py', 'yaml/test10.py', 'canonicaljson/test17.py', 'markdown/test7.py', 'schedule/test10.py', 'jsonschema/test10.py', 'mpmath/test15.py', 'bencoder/test8.py', 'bidict/test8.py', 'canonicaljson/test9.py', 'bencoder/test18.py', 'base58/test15.py', 'moneyed/test9.py', 'boltons/test6.py', 'boltons/test5.py', 'fractions/test6.py', 'jose/test9.py', 'yaml/test5.py', 'moneyed/test11.py', 'yaml/test7.py', 'bidict/test14.py', 'fractions/test5.py', 'boltons/test17.py', 'jsonschema/test20.py', 'deepdiff/test4.py', 'construct/test15.py', 'construct/test7.py', 'idna/test17.py', 'networkx/test6.py', 'whoosh/test18.py', 'jsonschema/test14.py', 'fractions/test4.py', 'jose/test10.py', 'rsa/test7.py', 'canonicaljson/test13.py', 'furl/test6.py', 'canonicaljson/test5.py', 'boltons/test7.py', 'yaml/test15.py', 'base58/test13.py', 'bencoder/test3.py', 'pyaes/test11.py', 'pbkdf2/test16.py', 'bech32/test3.py', 'jose/test12.py', 'moneyed/test19.py', 'deepdiff/test1.py', 'boltons/test9.py', 'markdown/test14.py', 'pyaes/test8.py', 'bencoder/test17.py', 'fractions/test1.py', 'schedule/test3.py', 'jose/test1.py', 'idna/test16.py', 'bech32/test11.py', 'jose/test6.py', 'base58/test9.py', 'mpmath/test3.py', 'bencoder/test13.py', 'bidict/test11.py', 'idna/test8.py', 'schedule/test6.py', 'bidict/test7.py', 'pbkdf2/test15.py', 'moneyed/test2.py', 'pbkdf2/test11.py', 'rsa/test11.py', 'jsonschema/test18.py', 'jsonschema/test6.py', 'base58/test12.py', 'yaml/test18.py', 'bencoder/test2.py', 'construct/test5.py', 'furl/test10.py', 'boltons/test1.py', 'deepdiff/test11.py', 'bech32/test8.py', 'furl/test9.py', 'fractions/test16.py', 'whoosh/test9.py', 'schedule/test18.py', 'bech32/test16.py', 'base58/test16.py', 'whoosh/test15.py', 'jsonschema/test2.py', 'schedule/test14.py', 'moneyed/test13.py', 'yaml/test9.py', 'jose/test19.py', 'bidict/test6.py', 'markdown/test12.py', 'base58/test14.py', 'whoosh/test4.py', 'bidict/test1.py', 'pyaes/test13.py', 'idna/test19.py', 'networkx/test15.py', 'idna/test2.py', 'pyaes/test7.py', 'bidict/test18.py', 'whoosh/test17.py', 'bencoder/test10.py', 'yaml/test20.py', 'bidict/test20.py', 'pyaes/test14.py', 'bencoder/test9.py', 'whoosh/test11.py', 'base58/test20.py', 'markdown/test16.py', 'furl/test3.py', 'furl/test2.py', 'yaml/test1.py', 'moneyed/test18.py', 'moneyed/test5.py', 'sqlparse/test9.py', 'whoosh/test14.py', 'schedule/test20.py', 'base58/test8.py', 'sqlparse/test16.py', 'idna/test7.py', 'idna/test20.py', 'pbkdf2/test13.py', 'furl/test4.py', 'construct/test18.py', 'jsonschema/test5.py', 'schedule/test12.py', 'bidict/test19.py', 'furl/test7.py', 'construct/test3.py', 'deepdiff/test15.py', 'markdown/test1.py', 'schedule/test4.py', 'jsonschema/test1.py', 'construct/test10.py', 'schedule/test16.py', 'construct/test14.py', 'bencoder/test11.py', 'schedule/test5.py', 'boltons/test19.py', 'bencoder/test14.py', 'jsonschema/test13.py', 'fractions/test13.py', 'schedule/test1.py', 'base58/test4.py', 'jose/test17.py', 'jsonschema/test19.py', 'bech32/test7.py', 'mpmath/test5.py', 'canonicaljson/test18.py', 'jose/test3.py', 'furl/test13.py', 'base58/test18.py', 'fractions/test20.py', 'jsonschema/test4.py', 'markdown/test15.py', 'markdown/test9.py', 'sqlparse/test3.py', 'boltons/test13.py', 'markdown/test6.py', 'markdown/test3.py', 'rsa/test18.py', 'fractions/test3.py', 'pyaes/test15.py', 'bencoder/test16.py', 'boltons/test2.py', 'fractions/test17.py', 'jose/test2.py', 'canonicaljson/test3.py', 'canonicaljson/test7.py', 'networkx/test2.py', 'pbkdf2/test7.py', 'yaml/test14.py', 'mpmath/test6.py', 'pyaes/test18.py', 'whoosh/test19.py', 'jsonschema/test12.py', 'moneyed/test1.py', 'pbkdf2/test14.py', 'whoosh/test16.py', 'deepdiff/test2.py', 'bencoder/test1.py', 'networkx/test17.py', 'construct/test1.py', 'pyaes/test16.py', 'markdown/test8.py', 'markdown/test17.py', 'canonicaljson/test15.py', 'construct/test6.py', 'jose/test4.py', 'pbkdf2/test8.py', 'bencoder/test12.py', 'rsa/test2.py', 'networkx/test20.py', 'canonicaljson/test16.py', 'construct/test8.py', 'pyaes/test5.py', 'yaml/test8.py', 'sqlparse/test10.py', 'idna/test3.py', 'schedule/test11.py', 'canonicaljson/test10.py', 'markdown/test2.py', 'mpmath/test9.py', 'bidict/test15.py', 'markdown/test5.py', 'canonicaljson/test2.py', 'boltons/test12.py', 'whoosh/test8.py', 'moneyed/test10.py', 'jsonschema/test11.py', 'canonicaljson/test19.py', 'pyaes/test6.py', 'pbkdf2/test1.py', 'pbkdf2/test4.py', 'sqlparse/test7.py', 'bidict/test4.py', 'furl/test1.py', 'markdown/test10.py', 'yaml/test17.py', 'base58/test11.py', 'jose/test8.py', 'rsa/test17.py', 'yaml/test4.py', 'idna/test10.py', 'furl/test8.py', 'construct/test4.py', 'jsonschema/test16.py', 'fractions/test12.py', 'bech32/test10.py', 'canonicaljson/test4.py', 'rsa/test10.py', 'bencoder/test4.py', 'bidict/test9.py', 'construct/test2.py', 'yaml/test19.py', 'pbkdf2/test2.py', 'fractions/test7.py', 'pbkdf2/test10.py', 'whoosh/test10.py', 'mpmath/test14.py', 'bidict/test2.py', 'idna/test1.py', 'networkx/test1.py', 'mpmath/test8.py', 'idna/test14.py', 'jsonschema/test3.py', 'base58/test10.py', 'deepdiff/test6.py', 'idna/test5.py', 'deepdiff/test12.py', 'moneyed/test8.py', 'canonicaljson/test6.py', 'fractions/test8.py', 'jose/test16.py', 'fractions/test9.py', 'mpmath/test10.py', 'networkx/test11.py', 'fractions/test11.py', 'markdown/test20.py', 'markdown/test18.py', 'bencoder/test19.py', 'base58/test3.py', 'yaml/test13.py', 'jose/test11.py', 'pbkdf2/test6.py', 'canonicaljson/test12.py', 'networkx/test10.py', 'schedule/test7.py', 'bech32/test17.py', 'moneyed/test20.py', 'bech32/test6.py', 'mpmath/test2.py', 'whoosh/test5.py', 'bech32/test5.py', 'moneyed/test16.py', 'base58/test5.py']
excluded_ids = ['pyaes', 'yaml', 'idna', 'markdown' ]
output_tests = f"./output_loop/{model_name}_retry{max_retries}/testfiles"
python_to_js_mapping = {
    # 编码与哈希类：映射到原生 Buffer/Uint8Array 或 Web Crypto API
    "base58": "Uint8Array / Buffer (Manual Base58 Encoding Logic)",
    "bech32": "Uint8Array / DataView (Manual Bech32 Encoding Logic)",
    "bencoder": "Uint8Array / ArrayBuffer (Manual Bencode logic)",
    "rlp": "Uint8Array / Buffer (Recursive Length Prefix logic)",
    "canonicaljson": "JSON.stringify (Custom sorting and normalization logic)",

    # 数据结构与位操作：映射到原生二进制处理
    "bidict": "Map (Dual-direction key/value management)",
    "bitarray": "Uint8Array / BigInt / Bitwise Operators",
    "bitstring": "Buffer / Uint8Array / DataView",
    "construct": "DataView / ArrayBuffer (Manual Struct Parsing)",

    # 密码学：统一映射到 crypto 模块，强制其处理原始字节和算法逻辑
    "ecdsa": "node:crypto (SubtleCrypto / createSign / createVerify)",
    "rsa": "node:crypto (KeyObject / publicEncrypt / privateDecrypt)",
    "jose": "node:crypto (JWT/JWE manual construction with HMAC/RSA)",
    "pbkdf2": "node:crypto (crypto.pbkdf2 / crypto.pbkdf2Sync)",
    "pyaes": "node:crypto (Cipher / Decipher / createCipheriv)",

    # 数学与规范类：映射到内置对象或 BigInt
    "fractions": "BigInt / Number (Manual Rational Number logic)",
    "mpmath": "BigInt (Arbitrary-precision arithmetic logic)",
    "moneyed": "Intl.NumberFormat / BigInt",
    "idna": "url (URL class) / punycode (Built-in module)",

    # 解析类：映射到更基础的解析器或正则表达式逻辑
    "markdown": "RegExp / String Manipulation (Manual AST Construction)",
    "sqlparse": "RegExp / String (Manual Lexer/Tokenizer logic)",
    "yaml": "JSON / RegExp (Manual YAML to Object mapping)"
}


def run_command(cmd):
    """运行 shell 命令，捕获输出、错误流和退出码"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "TIMEOUT", "exit_code": -1}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "exit_code": 1}


def build_prompt(dataset_root, relative_path, py_code, js_output_path, max_retries, python_package):
    return f"""
            你是一个资深的跨语言迁移专家（Python 到 Node.js）。请阅读以下 Python 代码：

            --- 源代码 ({os.path.join(dataset_root, relative_path)}) ---
            {py_code}
            ---

            任务要求：
            1. **环境与模块规范**：
            - 必须编写纯 JavaScript 代码，运行环境为 Node.js。
            - **强制使用 ES Modules (ESM) 规范**：你必须使用 `import` 导入模块，使用 `export` 导出模块。**严禁使用 `require()` 或 `module.exports`**。
            - **文件后缀要求**：为了确保 Node.js 正确识别 ESM，生成的库文件和入口测试文件必须使用 **`.mjs`** 后缀（或者确保目标路径为 {js_output_path.replace(".cjs", ".mjs")} 时，其环境已配置为 type: module）。

            2. **命令行参数对齐**：
            - 该 JS 文件必须拥有和上述 Python 文件**完全相同**的命令行传参方式（参数名、默认值、必填项均需一致）。
            - 你需要手动解析 `process.argv`。确保 `node test.mjs --arg val` 的行为与 `python test.py --arg val` 在参数解析逻辑上完全对齐。

            3. **逻辑与输出对齐**：
            - 算法逻辑、数值计算精度、字符串格式化必须与原 Python 文件完全一致。
            - 确保 `console.log` 的输出内容（包括空格、换行）与 Python 的 `print` 结果逐字对应。

            4. **零外部依赖**：
            - **禁止使用任何 npm 外部模块**（如 yargs, argparse 等）。
            - **严禁使用import导入外部模块，只能import导入本地文件**。否则视为无效答案。
            - **禁止内嵌 Python 脚本**。必须使用 Node.js 原生内置模块（如 `node:fs`, `node:path`, `node:url` 等）。

            5. **工程化结构与 ESM 特性**：
            - 请在 `/home/work/RepoArena/output_loop/{model_name}_retry{max_retries}/packages/{relative_path.replace(".py","_pkg")}` 中生成库文件。
            - **层次化组织**：库必须按功能拆分为多个模块，通过 `export` 暴露接口。
            - **注意**：在 ESM 中，`import` 语句必须包含完整的文件后缀（例如：`import {{ x }} from './utils.mjs'`）。
            - **路径处理**：你的工作区是/home/work/RepoArena/output_loop/{model_name}_retry{max_retries}，你可以在这个工作区中执行任何操作，但一定要将结果保存为固定形式。

            6. **黑盒实现**：
            - 你不能查看 Python 原生包的内部源码，只能通过接口行为用 JS 重新实现逻辑。
            - 严禁调用或提及 `{python_to_js_mapping.get(python_package, 'Unknown Python Package')}` 的任何接口。

            提示：请先输出库文件的分层代码（使用 .mjs），最后输出入口测试文件 `{js_output_path.replace(".cjs", ".mjs")}` 的代码。
            """


def generate_test_cases(py_code, test_cases_path):
    gen_test_prompt = f"""
            你是一个测试工程师。请阅读以下 Python 代码，并生成 5 组不同的命令行参数来测试其逻辑。
            要求覆盖：常规输入、边界值、可能的异常输入。
            
            源代码内容:
            {py_code}

            请直接输出一个 JSON 格式的字符串数组，例如: ["--input 1", "--input 10 --verbose", ""]
            不要输出任何解释，只需 JSON 数组, 不需要输出output，只需要输入input的参数。
            """
    print("正在生成测试用例...")
    run_reasoning_agent(f"阅读代码并生成测试参数存入 {test_cases_path}，格式为JSON数组：\n{gen_test_prompt}", model_name)

    try:
        with open(test_cases_path, "r") as f:
            return json.load(f)
    except Exception:
        return [""]


def validate_js_equivalence(py_path, js_output_path, test_cases):
    all_passed = True
    fail_reason = ""

    for args in test_cases:
        py_res = run_command(f"python3 {py_path} {args}")
        if py_res["exit_code"] != 0:
            print(f"   [Skip] 测试用例 '{args}' 在 Python 中执行出错，已忽略。")
            continue

        js_res = run_command(f"node {js_output_path} {args}")
        if py_res["stdout"] != js_res["stdout"]:
            all_passed = False
            fail_reason = (
                f"参数 '{args}' 输出不一致。\n"
                f"Python 标准输出:\n{py_res['stdout']}\n"
                f"JS 标准输出:\n{js_res['stdout']}"
            )
            break
        if py_res["exit_code"] != js_res["exit_code"]:
            all_passed = False
            fail_reason = f"参数 '{args}' 退出码不一致 (Py:{py_res['exit_code']}, JS:{py_res['exit_code']})"
            break

    return all_passed, fail_reason


def process_file(task):
    py_path, relative_path, dataset_root = task
    output_base = f"/home/work/RepoArena/output_loop/{model_name}_retry{max_retries}"
    js_output_path = os.path.join(output_base, "testfiles", relative_path.replace(".py", ".mjs"))
    test_cases_path = os.path.join(output_base, "test_cases", relative_path.replace(".py", ".json"))

    os.makedirs(os.path.dirname(js_output_path), exist_ok=True)
    os.makedirs(os.path.dirname(test_cases_path), exist_ok=True)

    with open(py_path, "r", encoding="utf-8") as f:
        py_code = f.read()

    python_package = py_path.split('/')[-2]
    full_prompt = build_prompt(dataset_root, relative_path, py_code, js_output_path, max_retries, python_package)

    print(f"\n>>> 进程 {os.getpid()} 正在处理: {relative_path}")

    test_cases = generate_test_cases(py_code, test_cases_path)
    fail_reason = ""

    for attempt in range(max_retries):
        print(f"进程 {os.getpid()} 尝试第 {attempt + 1} 次生成/修复 JS 代码...")
        if attempt == 0:
            solver_prompt = full_prompt
        else:
            solver_prompt = f"""
                    {full_prompt}

                    【重要提示】你不需要重新写，在现有基础上修改即可。
                    当前路径: {js_output_path}
                    库路径: /home/work/RepoArena/output_loop/{model_name}_retry{max_retries}/packages/{relative_path.replace(".py","_pkg")}
                    上次尝试失败反馈:
                    {fail_reason}
                    """
        run_reasoning_agent(solver_prompt, model_name)

        all_passed, fail_reason = validate_js_equivalence(py_path, js_output_path, test_cases)
        if all_passed:
            print(f"✅ 验证通过: {relative_path}")
            return {"relative_path": relative_path, "status": "ok", "fail_reason": ""}

        print(f"❌ 验证失败: {fail_reason}")
        py_code += f"\n\n# 上次尝试失败反馈:\n# {fail_reason}"
        full_prompt = build_prompt(dataset_root, relative_path, py_code, js_output_path, max_retries, python_package)

    print(f"⚠️ 在 {max_retries} 次尝试后仍未完全对齐: {relative_path}")
    return {"relative_path": relative_path, "status": "fail", "fail_reason": fail_reason}


def collect_tasks(dataset_root):
    tasks = []
    for root, dirs, files in os.walk(dataset_root):
        for file in sorted(files):
            if not file.endswith(".py"):
                continue
            py_path = os.path.join(root, file)
            
            relative_path = os.path.relpath(py_path, dataset_root)
            if relative_path not in valid_ids:
                continue
            if relative_path.split("/")[0] in excluded_ids:
                continue
            js_path = os.path.join(output_tests, relative_path.replace(".py", ".mjs"))
            if os.path.exists(js_path):
                print(f"js file exists at {js_path}, skip")
                continue
            tasks.append((py_path, relative_path, dataset_root))
    return tasks


def main():
    dataset_root = "/home/work/RepoArena/dataset"
    num_processes = 2
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        num_processes = int(sys.argv[1])
    elif os.environ.get("NUM_PROCESSES"):
        try:
            num_processes = int(os.environ.get("NUM_PROCESSES"))
        except ValueError:
            pass
    num_processes = max(1, num_processes)

    tasks = collect_tasks(dataset_root)
    print(f"使用 {num_processes} 个进程并发处理 {len(tasks)} 个 Python 文件。")

    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(processes=num_processes) as pool:
        for result in pool.imap_unordered(process_file, tasks):
            if result["status"] == "ok":
                print(f"✅ {result['relative_path']} 处理完成")
            else:
                print(f"⚠️ {result['relative_path']} 处理失败: {result['fail_reason']}")


if __name__ == "__main__":
    main()
