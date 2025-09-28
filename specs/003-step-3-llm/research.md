# Research: LLM-Generated Code Review Reports

**Phase 0 Output** | **Date**: 2025-09-27

## Technology Decisions

### Template Engine Selection

**Decision**: Jinja2 for template rendering
**Rationale**:
- Industry standard with excellent Python integration
- Supports complex control structures (loops, conditionals) needed for dynamic content
- Safe by default (auto-escaping prevents injection attacks)
- Mature ecosystem with extensive documentation
- Already used in many Python CLI tools

**Alternatives considered**:
- String.format(): Too basic for complex templating needs
- Mako: More complex, unnecessary features for this use case
- Custom templating: Violates KISS principle, unnecessary engineering

### LLM Integration Approach

**Decision**: Subprocess calls to external CLI tools (starting with Gemini CLI)
**Rationale**:
- Avoids API key management complexity in codebase
- CLI tools handle authentication, rate limiting, and error handling
- Easy to swap LLM providers without code changes
- Follows existing project pattern of calling external tools (git, linters)
- Fail-fast approach - immediate error if CLI tool unavailable

**Alternatives considered**:
- Direct API calls: Requires API key management, HTTP client dependency
- Python SDK integration: Tight coupling to specific providers
- Cloud function proxies: Unnecessary complexity for CLI tool

### Data Handling Strategy

**Decision**: Reuse existing Pydantic models, add minimal new structures
**Rationale**:
- ScoreInput model already exists and validated
- Type safety and validation handled automatically
- Consistent with existing codebase patterns
- No new dependencies required

**Alternatives considered**:
- Raw JSON manipulation: Error-prone, no validation
- Custom data classes: Duplicates existing functionality
- Dataclasses: Less validation than Pydantic

### Error Handling Philosophy

**Decision**: Fail-fast with detailed error messages
**Rationale**:
- Aligns with project constitution (KISS principle)
- LLM service failures should be immediately visible to users
- No complex retry logic - users can re-run command if needed
- Clear error messages help with debugging external dependencies

**Alternatives considered**:
- Retry mechanisms: Adds complexity, may hang pipeline
- Graceful degradation: Could hide important issues
- Silent failures: Violates transparency principle

## Best Practices Research

### CLI Integration Patterns

**Finding**: Click command groups provide clean subcommand structure
**Application**:
- Add `llm-report` subcommand to existing CLI
- Use consistent parameter patterns with existing commands
- Leverage Click's built-in help and validation

### Template Security

**Finding**: Jinja2 sandboxed environment prevents code execution
**Application**:
- Use SandboxedEnvironment for user-provided templates
- Validate template syntax before LLM generation
- Limit available functions and filters

### Context Length Management

**Finding**: Modern LLMs have 128k+ context limits but cost increases with length
**Application**:
- Truncate evidence to top 3 highest-confidence items per category
- Summarize large metric collections
- Provide user warning when truncation occurs

### Subprocess Best Practices

**Finding**: Proper timeout handling and error capture essential
**Application**:
- Use subprocess.run with timeout parameter
- Capture both stdout and stderr for debugging
- Check return codes and raise CalledProcessError
- Use text mode for proper encoding handling

## Integration Patterns

### Existing Pipeline Integration

**Pattern**: Optional pipeline step with feature flags
**Implementation**:
- Add `--generate-llm-report` flag to main analysis command
- Check for score_input.json existence before attempting generation
- Log clear messages about LLM generation progress
- Maintain backward compatibility (default: disabled)

### Testing Strategies

**Pattern**: Mock external dependencies for unit tests
**Implementation**:
- Mock subprocess.run calls in unit tests
- Use temporary files for integration tests
- Validate generated content structure without LLM calls
- Test error conditions (missing files, CLI failures)

### Configuration Management

**Pattern**: File-based configuration with CLI overrides
**Implementation**:
- Default template in specs/prompts/llm_report.md
- Support custom template paths via CLI argument
- Environment variable for default LLM provider
- Validate template structure on load

## Dependencies Analysis

### Required New Dependencies

1. **jinja2** (2.11+)
   - Mature, stable template engine
   - No security vulnerabilities in recent versions
   - Compatible with Python 3.11+
   - MIT license (compatible with project)

### External Tool Requirements

1. **Gemini CLI** (initial implementation)
   - User-installed dependency (documented in README)
   - Version detection via `--version` flag
   - Clear error messages when unavailable
   - Future extensibility for other providers

## Performance Considerations

### Template Rendering Performance

**Finding**: Jinja2 template compilation is one-time cost
**Application**:
- Cache compiled templates in memory
- Pre-compile templates during module import
- Template rendering typically <10ms for report size

### LLM API Performance

**Finding**: External API calls dominate execution time
**Application**:
- Set reasonable timeouts (30 seconds default)
- Provide progress indicators for user feedback
- Consider async patterns for future multi-report generation

### Memory Usage

**Finding**: Template and JSON data easily fit in memory
**Application**:
- No need for streaming or chunking
- Peak memory usage <50MB for largest expected inputs
- Cleanup temporary data after generation

## Future Extensibility

### Multi-Provider Support

**Strategy**: Plugin-like architecture for LLM providers
**Implementation**:
- Abstract LLMProvider base class
- Provider-specific CLI command configurations
- Runtime provider selection via configuration

### Report Format Variations

**Strategy**: Template-based customization
**Implementation**:
- Support multiple template files
- Context-specific templates (hackathon vs code review)
- Custom field definitions in template metadata

### Batch Processing

**Strategy**: Design for future batch report generation
**Implementation**:
- Stateless report generation functions
- Parallel processing capability
- Progress tracking for multiple repositories

---

**Research Complete**: All NEEDS CLARIFICATION items resolved
**Next Phase**: Design data models and contracts