import os
import json
import subprocess
import pathlib
import re
import tempfile
from multiprocessing import Pool, Manager

# 配置参数
model_name = "deepseek-v3.1-250821"
api_base = "https://qianfan.baidubce.com/v2"
provider = "openai"  # custom_llm_provider for mini-swe-agent
num_processes = 10  # 并发进程数 K

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

def run_mini_agent(prompt, model_name=None, api_base=None, provider=None):
    """使用 mini-swe-agent 调用执行任务，实时显示输出"""
    print(f"\n[调用 Mini-SWE-Agent] Model: {model_name}, API: {api_base}")

    # 创建临时文件来传递 prompt（避免 shell 参数长度限制和特殊字符问题）
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        # 构建 mini 命令，使用 -t 参数传递任务
        shell_cmd = f"cd . && MSWEA_COST_TRACKING=ignore_errors /root/codes/baidu_personal-code_self-verify-rl/baidu/personal-code/self-verify-rl/venv/bin/mini --model openai/{model_name} -y --exit-immediately -t \"{prompt_file}\" --custom-llm-provider litellm --api-base https://qianfan.baidubce.com/v2"

        # 使用 Popen 来实时输出
        process = subprocess.Popen(
            shell_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # 实时输出 stdout
        while True:
            line = process.stdout.readline()
            if not line:
                break
            # 实时打印输出
            print(line, end='', flush=True)

        # 等待进程结束
        process.wait()

        # 获取剩余的 stderr（如果有）
        stderr_output = process.stderr.read()

        if process.returncode != 0:
            print(f"\n❌ Mini-SWE-Agent 执行失败 (返回码: {process.returncode})")
            if stderr_output:
                print(f"STDERR: {stderr_output}")
            return False, f"执行失败 (返回码 {process.returncode}): {stderr_output}"

        print(f"\n✅ Mini-SWE-Agent 执行成功")

        return True, None

    except Exception as e:
        print(f"\n❌ Mini-SWE-Agent 执行异常: {e}")
        return False, f"执行异常: {e}"
    finally:
        # 清理临时文件
        try:
            os.unlink(prompt_file)
        except:
            pass

def run_command(cmd):
    """运行 shell 命令，捕获输出、错误流和退出码"""
    try:
        # 设置 check=False 允许捕获非零退出码而不抛出异常
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

def process_single_file(task_info):
    """处理单个文件的函数，供多进程调用"""
    py_path, relative_path, dataset_root, output_base, model_name, api_base, provider, python_to_js_mapping, max_retries = task_info

    # 获取进程 ID
    pid = os.getpid()
    prefix = f"[进程 {pid}] "

    js_output_path = os.path.join(output_base, "testfiles", relative_path.replace(".py", ".mjs"))
    test_cases_path = os.path.join(output_base, "test_cases", relative_path.replace(".py", ".json"))

    os.makedirs(os.path.dirname(js_output_path), exist_ok=True)
    os.makedirs(os.path.dirname(test_cases_path), exist_ok=True)

    print(f"{prefix}正在处理: {relative_path}")

    with open(py_path, "r", encoding="utf-8") as f:
        py_code = f.read()

    python_package = py_path.split('/')[-2]

    # 构建完整的 Prompt
    full_prompt = f"""
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
            - 请在 `./output_loop_mini/{model_name}_retry{max_retries}/packages/{relative_path.replace(".py","_pkg")}` 中生成库文件。
            - **层次化组织**：库必须按功能拆分为多个模块，通过 `export` 暴露接口。
            - **注意**：在 ESM 中，`import` 语句必须包含完整的文件后缀（例如：`import {{ x }} from './utils.mjs'`）。
            - **路径处理**：你的工作区是./output_loop_mini/{model_name}_retry{max_retries}，你可以在这个工作区中执行任何操作，但一定要将结果保存为固定形式。

            6. **黑盒实现**：
            - 你不能查看 Python 原生包的内部源码，只能通过接口行为用 JS 重新实现逻辑。
            - 严禁调用或提及 `{python_to_js_mapping.get(python_package, 'Unknown Python Package')}` 的任何接口。

            提示：请先输出库文件的分层代码（使用 .mjs），最后输出入口测试文件 `{js_output_path.replace(".cjs", ".mjs")}` 的代码。
            """

    # --- 第一步: Test Generator Agent 生成测试样例 ---
    gen_test_prompt = f"""
            你是一个测试工程师。请阅读以下 Python 代码，并生成 5 组不同的命令行参数来测试其逻辑。
            要求覆盖：常规输入、边界值、可能的异常输入。

            源代码内容:
            {py_code}

            请直接输出一个 JSON 格式的字符串数组，例如: ["--input 1", "--input 10 --verbose", ""]
            不要输出任何解释，只需 JSON 数组, 不需要输出output，只需要输入input的参数。
            """
    print(f"{prefix}正在生成测试用例...")
    run_mini_agent(f"阅读代码并生成测试参数存入 {test_cases_path}，格式为JSON数组：\n{gen_test_prompt}", model_name, api_base, provider)

    # 加载生成的测试用例
    try:
        with open(test_cases_path, "r") as f:
            test_cases = json.load(f)
    except:
        test_cases = [""]  # 降级方案：空参数运行

    # --- 第二步: 迭代优化循环 (Solver Loop) ---
    fail_reason = ""
    for attempt in range(max_retries):
        print(f"{prefix}尝试第 {attempt + 1} 次生成/修复 JS 代码...")

        # 调用 Solver Agent
        if attempt == 0:
            solver_prompt = full_prompt
        else:
            solver_prompt = f"""
                    {full_prompt}

                    【重要提示】你不需要重新写，在现有基础上修改即可。
                    当前路径: {js_output_path}
                    库路径: ./output_loop_mini/{model_name}_retry{max_retries}/packages/{relative_path.replace(".py","_pkg")}
                    上次尝试失败反馈:
                    {fail_reason}
                    """
        run_mini_agent(solver_prompt, model_name, api_base, provider)

        # --- 第三步: 验证逻辑 (Evaluator) ---
        all_passed = True
        fail_reason = ""

        for args in test_cases:
            # 1. 首先运行 Python 文件获取基准
            py_res = run_command(f"python3 {py_path} {args}")

            # 2. 检查 Python 是否运行成功
            if py_res["exit_code"] != 0:
                print(f"{prefix}   [Skip] 测试用例 '{args}' 在 Python 中执行出错，已忽略。")
                continue

            # 3. 只有 Python 运行成功，才运行 JS 并比对
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
                fail_reason = f"参数 '{args}' 退出码不一致 (Py:{py_res['exit_code']}, JS:{js_res['exit_code']})"
                break

        if all_passed:
            print(f"{prefix}✅ 验证通过: {relative_path}")
            return {"relative_path": relative_path, "status": "success", "error": None}
        else:
            print(f"{prefix}❌ 验证失败: {fail_reason}")
            # 反馈给下一次循环的 Solver
            py_code += f"\n\n# 上次尝试失败反馈:\n# {fail_reason}"

    # 达到最大重试次数仍未成功
    print(f"{prefix}⚠️ 在 {max_retries} 次尝试后仍未完全对齐: {relative_path}")
    return {"relative_path": relative_path, "status": "failed", "error": fail_reason}

def collect_tasks(dataset_root, output_base, model_name, api_base, provider, python_to_js_mapping, max_retries):
    """收集所有待处理的任务"""
    tasks = []
    for root, dirs, files in os.walk(dataset_root):
        files = sorted(files)
        for file in files:
            if file.endswith(".py"):
                py_path = os.path.join(root, file)
                relative_path = os.path.relpath(py_path, dataset_root)

                js_output_path = os.path.join(output_base, "testfiles", relative_path.replace(".py", ".mjs"))

                # 跳过已处理的文件
                if os.path.exists(js_output_path):
                    print(f"跳过已处理: {relative_path}")
                    continue

                os.makedirs(os.path.dirname(js_output_path), exist_ok=True)

                tasks.append((
                    py_path,
                    relative_path,
                    dataset_root,
                    output_base,
                    model_name,
                    api_base,
                    provider,
                    python_to_js_mapping,
                    max_retries
                ))

    return tasks

def main():
    dataset_root = "./dataset"
    max_retries = 2
    output_base = f"./output_loop_mini/{model_name}_retry{max_retries}"

    print("="*60)
    print("🚀 开始使用 Mini-SWE-Agent 进行代码转换（并行模式）")
    print("="*60)
    print(f"Model: {model_name}")
    print(f"API Base: {api_base}")
    print(f"Provider: {provider}")
    print(f"并发进程数 (K): {num_processes}")
    print(f"最大重试次数: {max_retries}")
    print("="*60)

    # 收集所有待处理任务
    print("\n正在扫描数据集...")
    tasks = collect_tasks(dataset_root, output_base, model_name, api_base, provider, python_to_js_mapping, max_retries)
    print(f"共发现 {len(tasks)} 个待处理任务")

    if len(tasks) == 0:
        print("没有待处理的任务，退出。")
        return

    # 使用进程池并行处理
    print(f"\n开始并行处理（{num_processes} 个进程）...\n")

    success_count = 0
    failed_count = 0
    failed_tasks = []

    with Pool(processes=num_processes) as pool:
        results = pool.map(process_single_file, tasks)

    # 统计结果
    for result in results:
        if result["status"] == "success":
            success_count += 1
        else:
            failed_count += 1
            failed_tasks.append(result)

    # 打印总统计
    print("\n" + "="*60)
    print("📊 处理统计")
    print("="*60)
    print(f"总任务数: {len(tasks)}")
    print(f"成功: {success_count}")
    print(f"失败: {failed_count}")
    print("="*60)

    if failed_tasks:
        print("\n❌ 失败的任务列表：")
        for task in failed_tasks:
            print(f"  - {task['relative_path']}: {task['error'][:100]}..." if len(task['error']) > 100 else f"  - {task['relative_path']}: {task['error']}")

if __name__ == "__main__":
    main()