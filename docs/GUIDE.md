# Code Score Documentation Guide

Quick navigation to all project documentation.

## For Users

**Getting Started**
- Installation and basic usage: [README.md](../README.md)
- Output files and formats: [README.md#output-files](../README.md#output-files)
- AI report generation: [README.md#ai-report-generation](../README.md#ai-report-generation)
- Troubleshooting: [README.md#troubleshooting](../README.md#troubleshooting)

**Advanced Usage**
- Custom templates: [README.md#custom-templates-jinja2](../README.md#custom-templates-jinja2)
- Template field reference: [../specs/prompts/template_docs.md](../specs/prompts/template_docs.md)
- Default template example: [../specs/prompts/llm_report.md](../specs/prompts/llm_report.md)

## For Developers

**Development Guide**
- Architecture overview: [CLAUDE.md#core-architecture](../CLAUDE.md#core-architecture)
- Development workflow: [CLAUDE.md#common-commands](../CLAUDE.md#common-commands)
- Testing strategy: [CLAUDE.md#testing-architecture](../CLAUDE.md#testing-architecture)
- Adding language support: [CLAUDE.md#adding-new-language-support](../CLAUDE.md#adding-new-language-support)

**Project Principles**
- Constitutional principles: [.specify/memory/constitution.md](../.specify/memory/constitution.md)
- UV-based dependency management
- KISS principle (Keep It Simple, Stupid)
- Transparent communication

## For API Users

**Python API**
- Complete API reference: [api-reference.md](./api-reference.md)
- Metrics collection API: [api-reference.md#core-components](./api-reference.md#core-components)
- LLM report generation API: [api-reference.md#llm-report-generation](./api-reference.md#llm-report-generation)
- Data models: [../specs/data-models.md](../specs/data-models.md)

**Configuration**
- Checklist configuration: [../specs/contracts/checklist_mapping.yaml](../specs/contracts/checklist_mapping.yaml)
- Environment variables: [README.md#configuration](../README.md#configuration)

## Documentation Structure

```
code-score/
├── README.md              # Main user documentation
├── CLAUDE.md              # Developer guide
├── docs/
│   ├── GUIDE.md          # This file - documentation navigator
│   └── api-reference.md  # Python API documentation
└── specs/
    ├── data-models.md    # Data model specifications
    ├── contracts/        # Schemas and configuration
    │   └── checklist_mapping.yaml
    └── prompts/          # LLM template documentation
        ├── llm_report.md
        └── template_docs.md
```

## Quick Reference

| I want to... | See |
|--------------|-----|
| Install and run the tool | [README.md](../README.md) |
| Generate AI reports | [README.md#ai-report-generation](../README.md#ai-report-generation) |
| Understand the architecture | [CLAUDE.md](../CLAUDE.md) |
| Use the Python API | [api-reference.md](./api-reference.md) |
| Customize evaluation criteria | [checklist_mapping.yaml](../specs/contracts/checklist_mapping.yaml) |
| Create custom templates | [template_docs.md](../specs/prompts/template_docs.md) |
| Contribute to the project | [README.md#contributing](../README.md#contributing) |
| Debug issues | [CLAUDE.md#debugging-and-troubleshooting](../CLAUDE.md#debugging-and-troubleshooting) |

## Getting Help

- **General questions**: Review [README.md](../README.md)
- **Development issues**: Check [CLAUDE.md](../CLAUDE.md)
- **API integration**: See [api-reference.md](./api-reference.md)
- **Bug reports**: [GitHub Issues](https://github.com/your-org/code-score/issues)
