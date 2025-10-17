"""
真实调用 llm CLI 验证 DeepSeek 模型的关键能力：
- 多轮对话（llm chat）
- 从文件读取大体量提示（--file/--fragment）
- 默认流式输出管道
"""

from __future__ import annotations

import functools
import subprocess
import time
from pathlib import Path

import pytest

MODEL_ALIAS = "deepseek-coder"
PROMPT_TIMEOUT = 120
STREAM_TIMEOUT = 120
pytestmark = pytest.mark.integration


@functools.lru_cache(maxsize=1)
def _is_llm_cli_ready() -> bool:
    """检测 llm CLI、DeepSeek 插件与 API key 是否可用。"""
    try:
        which = subprocess.run(
            ["which", "llm"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if which.returncode != 0:
            return False

        plugins = subprocess.run(
            ["llm", "plugins"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if plugins.returncode != 0 or "llm-deepseek" not in plugins.stdout:
            return False

        keys = subprocess.run(
            ["llm", "keys", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return keys.returncode == 0 and "deepseek" in keys.stdout.lower()
    except Exception:
        return False


def _require_llm() -> pytest.mark:
    return pytest.mark.skipif(
        not _is_llm_cli_ready(),
        reason="llm CLI / DeepSeek 插件或密钥未配置",
    )


@functools.lru_cache(maxsize=1)
def _resolve_file_flag() -> str:
    """根据当前 llm 版本选择 --file 或 --fragment。"""
    try:
        help_output = subprocess.run(
            ["llm", "prompt", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout
    except Exception:
        help_output = ""

    if "--file" in help_output:
        return "--file"
    return "--fragment"


@_require_llm()
def test_llm_chat_supports_multi_turn() -> None:
    """确保 llm chat 可处理多轮输入并返回对应响应。"""
    conversation = "第一轮：请回答“步骤一”。\n第二轮：请回答“步骤二”。\nexit\n"
    result = subprocess.run(
        ["llm", "chat", "-m", MODEL_ALIAS, "--no-stream"],
        input=conversation,
        capture_output=True,
        text=True,
        timeout=PROMPT_TIMEOUT,
    )

    assert result.returncode == 0, result.stderr

    responses = [
        line
        for line in result.stdout.splitlines()
        if line.strip().startswith(">")
    ]
    assert len(responses) >= 2, f"输出不足以证明多轮对话：{result.stdout}"


@_require_llm()
def test_llm_prompt_accepts_long_file(tmp_path: Path) -> None:
    """验证通过 --file/--fragment 读取长提示文本。"""
    long_prompt = "\n".join(
        [
            f"段落 {i}: 这是长提示的内容。"  # 保留中文上下文，便于后续报告
            for i in range(1, 81)
        ]
    )
    long_prompt += "\n请仅输出“长提示已处理”。"

    prompt_file = tmp_path / "long_prompt.txt"
    prompt_file.write_text(long_prompt, encoding="utf-8")

    file_flag = _resolve_file_flag()
    command = [
        "llm",
        "prompt",
        "-m",
        MODEL_ALIAS,
        file_flag,
        str(prompt_file),
        "--no-stream",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=PROMPT_TIMEOUT,
    )

    assert result.returncode == 0, result.stderr
    assert "长提示" in long_prompt
    assert result.stdout.strip(), "长提示调用未返回结果"


@_require_llm()
def test_llm_prompt_streams_output() -> None:
    """验证默认流式输出可逐步读取。"""
    prompt = (
        "请分三步输出内容，每步单独换行：第一行写“开始”，"
        "第二行写数字 1,2,3（每个独占一行），第三行写“结束”。"
    )

    process = subprocess.Popen(
        ["llm", "-m", MODEL_ALIAS, prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    streamed_lines: list[tuple[float, str, int | None]] = []
    start = time.monotonic()

    try:
        while True:
            if time.monotonic() - start > STREAM_TIMEOUT:
                raise TimeoutError("读取流式输出超时")

            line = process.stdout.readline() if process.stdout else ""
            if line:
                streamed_lines.append((time.monotonic(), line, process.poll()))

            if process.poll() is not None:
                if process.stdout:
                    remainder = process.stdout.read()
                    if remainder:
                        streamed_lines.append((time.monotonic(), remainder, process.poll()))
                break

        stderr_output = process.stderr.read() if process.stderr else ""
    finally:
        process.stdout and process.stdout.close()
        process.stderr and process.stderr.close()

    assert process.returncode == 0, stderr_output
    assert streamed_lines, "未捕获到任何输出"
    assert any(status is None for _, _, status in streamed_lines[:-1]), streamed_lines
    assert any("开始" in chunk for _, chunk, _ in streamed_lines)
    assert any("结束" in chunk for _, chunk, _ in streamed_lines)
