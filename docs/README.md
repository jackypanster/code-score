# Code Score Documentation

This directory contains technical documentation for the Code Score system.

## Documentation Structure

### Primary Documentation (in project root)
- **[README.md](../README.md)** - Main project documentation with installation, usage, and examples
- **[CLAUDE.md](../CLAUDE.md)** - Development guidelines and project constitution
- **[Quickstart Guide](../specs/002-git-log-docs/quickstart.md)** - Step-by-step tutorial with real examples

### Technical Reference
- **[API Reference](./api-reference.md)** - Complete API documentation for programmatic usage

### Specifications (specs directory)
- **[Feature Specs](../specs/002-git-log-docs/)** - Detailed technical specifications
  - `tasks.md` - Implementation task tracking
  - `research.md` - Technical research and decisions
  - `data-model.md` - Data model documentation
  - `contracts/` - JSON schemas and configuration files

## Quick Navigation

### For Users
- Want to get started? → [README.md](../README.md#usage)
- Need working examples? → [Quickstart Guide](../specs/002-git-log-docs/quickstart.md)
- Looking for CLI help? → `uv run python -m src.cli.main --help`

### For Developers
- Want to contribute? → [CLAUDE.md](../CLAUDE.md)
- Need API reference? → [API Reference](./api-reference.md)
- Understanding architecture? → [Technical Specs](../specs/002-git-log-docs/)

### For Integrators
- Programmatic usage? → [API Reference](./api-reference.md#examples)
- Custom checklist? → [Checklist Configuration](./api-reference.md#configuration)
- Pipeline integration? → [Pipeline API](./api-reference.md#pipeline-integration)

## System Overview

The Code Score system provides:

1. **Metrics Collection** - Automated analysis of Git repositories
2. **Checklist Evaluation** - 11-item quality assessment with evidence tracking
3. **Structured Output** - JSON/Markdown reports for human and LLM consumption
4. **CLI Tools** - Complete command-line interface
5. **API Access** - Programmatic access to all functionality

## Features

- ✅ **Multi-language support** (Python, JavaScript, Java, Go)
- ✅ **Evidence-based evaluation** with confidence tracking
- ✅ **Schema validation** for all input/output
- ✅ **Performance optimized** (<0.1s evaluation time)
- ✅ **Comprehensive testing** (contract, integration, unit)
- ✅ **Production ready** with error handling and cleanup

For detailed usage instructions, see the [main README](../README.md).