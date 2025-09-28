#!/bin/bash

# Code Score - Git Repository Metrics Collection
# Entry point script for analyzing Git repositories

set -e  # Exit on any error (following constitutional KISS principle)

# Default values
OUTPUT_DIR="./output"
FORMAT="both"
TIMEOUT=300
VERBOSE=false
ENABLE_CHECKLIST=true
GENERATE_LLM_REPORT=false
LLM_PROVIDER="gemini"
LLM_TEMPLATE=""

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Usage function
show_usage() {
    cat << EOF
Usage: $0 <repository_url> [commit_sha] [options]

Arguments:
    repository_url    Git repository URL to analyze (required)
    commit_sha        Specific commit to analyze (optional)

Options:
    --output-dir DIR         Output directory (default: ./output)
    --format FORMAT          Output format: json, markdown, both (default: both)
    --timeout SECONDS        Analysis timeout in seconds (default: 300)
    --verbose               Enable verbose logging
    --enable-checklist      Enable checklist evaluation (default: enabled)
    --disable-checklist     Disable checklist evaluation
    --generate-llm-report   Generate human-readable LLM report
    --llm-provider PROVIDER LLM provider: gemini, openai, claude (default: gemini)
    --llm-template PATH     Path to custom LLM prompt template
    --help                  Show this help message

Examples:
    $0 https://github.com/user/repo.git
    $0 git@github.com:user/repo.git a1b2c3d4e5f6
    $0 https://github.com/user/repo.git --format json --verbose
    $0 https://github.com/user/repo.git main --output-dir ./results
    $0 https://github.com/user/repo.git --generate-llm-report
    $0 https://github.com/user/repo.git --generate-llm-report --llm-provider openai

Environment Variables:
    METRICS_OUTPUT_DIR   Default output directory
    METRICS_TOOL_TIMEOUT Default timeout in seconds
EOF
}

# Parse command line arguments
REPOSITORY_URL=""
COMMIT_SHA=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_usage
            exit 0
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --format)
            FORMAT="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --enable-checklist)
            ENABLE_CHECKLIST=true
            shift
            ;;
        --disable-checklist)
            ENABLE_CHECKLIST=false
            shift
            ;;
        --generate-llm-report)
            GENERATE_LLM_REPORT=true
            shift
            ;;
        --llm-provider)
            LLM_PROVIDER="$2"
            shift 2
            ;;
        --llm-template)
            LLM_TEMPLATE="$2"
            shift 2
            ;;
        --*)
            echo "Error: Unknown option $1" >&2
            show_usage >&2
            exit 1
            ;;
        *)
            if [[ -z "$REPOSITORY_URL" ]]; then
                REPOSITORY_URL="$1"
            elif [[ -z "$COMMIT_SHA" ]]; then
                COMMIT_SHA="$1"
            else
                echo "Error: Too many arguments" >&2
                show_usage >&2
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate required arguments
if [[ -z "$REPOSITORY_URL" ]]; then
    echo "Error: Repository URL is required" >&2
    show_usage >&2
    exit 1
fi

# Apply environment variable defaults
if [[ -n "$METRICS_OUTPUT_DIR" ]]; then
    OUTPUT_DIR="${METRICS_OUTPUT_DIR}"
fi

if [[ -n "$METRICS_TOOL_TIMEOUT" ]]; then
    TIMEOUT="${METRICS_TOOL_TIMEOUT}"
fi

# Validate format
case "$FORMAT" in
    json|markdown|both)
        ;;
    *)
        echo "Error: Invalid format '$FORMAT'. Must be json, markdown, or both" >&2
        exit 1
        ;;
esac

# Validate timeout
if ! [[ "$TIMEOUT" =~ ^[0-9]+$ ]] || [[ "$TIMEOUT" -lt 1 ]] || [[ "$TIMEOUT" -gt 1800 ]]; then
    echo "Error: Timeout must be between 1 and 1800 seconds" >&2
    exit 1
fi

# Validate LLM provider
case "$LLM_PROVIDER" in
    gemini|openai|claude)
        ;;
    *)
        echo "Error: Invalid LLM provider '$LLM_PROVIDER'. Must be gemini, openai, or claude" >&2
        exit 1
        ;;
esac

# Validate LLM template path if provided
if [[ -n "$LLM_TEMPLATE" ]] && [[ ! -f "$LLM_TEMPLATE" ]]; then
    echo "Error: LLM template file not found: $LLM_TEMPLATE" >&2
    exit 1
fi

# Check if uv is available (constitutional requirement)
if ! command -v uv &> /dev/null; then
    echo "Error: uv is required but not installed" >&2
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

# Change to project directory
cd "$PROJECT_ROOT"

# Verbose output
if [[ "$VERBOSE" == "true" ]]; then
    echo "Code Score - Git Repository Metrics Collection"
    echo "Repository: $REPOSITORY_URL"
    if [[ -n "$COMMIT_SHA" ]]; then
        echo "Commit: $COMMIT_SHA"
    fi
    echo "Output directory: $OUTPUT_DIR"
    echo "Output format: $FORMAT"
    echo "Timeout: $TIMEOUT seconds"
    echo "Checklist evaluation: $ENABLE_CHECKLIST"
    if [[ "$GENERATE_LLM_REPORT" == "true" ]]; then
        echo "LLM report generation: enabled"
        echo "LLM provider: $LLM_PROVIDER"
        if [[ -n "$LLM_TEMPLATE" ]]; then
            echo "LLM template: $LLM_TEMPLATE"
        fi
    else
        echo "LLM report generation: disabled"
    fi
    echo ""
fi

# Build command arguments
CMD_ARGS=("$REPOSITORY_URL")

if [[ -n "$COMMIT_SHA" ]]; then
    CMD_ARGS+=("$COMMIT_SHA")
fi

CMD_ARGS+=("--output-dir" "$OUTPUT_DIR")
CMD_ARGS+=("--format" "$FORMAT")
CMD_ARGS+=("--timeout" "$TIMEOUT")

if [[ "$VERBOSE" == "true" ]]; then
    CMD_ARGS+=("--verbose")
fi

# Add checklist evaluation option
if [[ "$ENABLE_CHECKLIST" == "true" ]]; then
    CMD_ARGS+=("--enable-checklist=true")
else
    CMD_ARGS+=("--enable-checklist=false")
fi

# Add LLM report generation options
if [[ "$GENERATE_LLM_REPORT" == "true" ]]; then
    CMD_ARGS+=("--generate-llm-report")
    CMD_ARGS+=("--llm-provider" "$LLM_PROVIDER")

    if [[ -n "$LLM_TEMPLATE" ]]; then
        CMD_ARGS+=("--llm-template" "$LLM_TEMPLATE")
    fi
fi

# Execute the Python CLI with error handling
if [[ "$VERBOSE" == "true" ]]; then
    echo "Executing: uv run python -m src.cli.main ${CMD_ARGS[*]}"
    echo ""
fi

# Run the analysis
# Temporarily disable exit-on-error to handle errors gracefully
set +e
uv run python -m src.cli.main "${CMD_ARGS[@]}"
exit_code=$?
set -e

if [ $exit_code -ne 0 ]; then
    echo "" >&2
    echo "Analysis failed with exit code $exit_code" >&2

    # Provide helpful error context
    case $exit_code in
        1)
            echo "This typically indicates a configuration or execution error." >&2
            echo "Run with --verbose for more details." >&2
            ;;
        130)
            echo "Analysis was interrupted by the user." >&2
            ;;
        *)
            echo "An unexpected error occurred." >&2
            ;;
    esac

    exit $exit_code
fi

# Success
if [[ "$VERBOSE" == "true" ]]; then
    echo ""
    echo "Analysis completed successfully!"
fi

exit 0