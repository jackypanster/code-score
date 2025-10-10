# Build Validation Known Issues

_Last updated: October 10, 2025_

## Python build fallback breaks on non-`python3` interpreters
- **Location**: `src/metrics/tool_runners/python_tools.py:352`
- **Problem**: The fallback path calls `python3 -m build --no-isolation`. On environments where only `python` (or a custom interpreter name) exists—such as Windows GitHub Actions runners or local virtualenvs without a `python3` shim—the command raises `FileNotFoundError`.
- **Impact**: Build validation incorrectly returns `success=None` with “Neither uv nor python build module available,” preventing Python projects from earning the Build/Package Success score even when the build tool is present.
- **Suggested fix**: Invoke the fallback using `sys.executable` (with `-m build`) or dynamically resolve the active interpreter instead of hard-coding `python3`.

## JavaScript build tool detection fails on platforms without `which`
- **Location**: `src/metrics/tool_runners/javascript_tools.py:347`
- **Problem**: `_check_tool_available` shells out to `which npm` / `which yarn`. On Windows or constrained shells that lack `which`, the call raises and the helper caches `available=False`.
- **Impact**: The runner returns “npm/yarn not available in PATH,” skips execution, and leaves `build_success=None`, even though `npm`/`yarn` is installed. This blocks Build/Package Success scoring for JavaScript/TypeScript repositories on those platforms.
- **Suggested fix**: Detect tooling using a cross-platform approach (`shutil.which`, `node -p`, or direct command execution with graceful fallback) to avoid relying on `which`.
