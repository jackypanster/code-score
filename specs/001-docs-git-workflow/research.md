# Research: Parameterized Git Repository Metrics Collection

## Research Areas

### Language Detection Strategies

**Decision**: Use file extension analysis with GitHub Linguist patterns
**Rationale**: Simple, reliable, and matches industry standards. Most repositories have clear primary languages.
**Alternatives considered**:
- AST parsing (too complex, violates KISS)
- Manual configuration (defeats automation purpose)
- Machine learning models (overkill for this use case)

### Tool Selection by Language

**Decision**: Use mature, widely-adopted tools with minimal configuration
**Rationale**: Ensures compatibility across different projects and reduces setup overhead

#### Python Tools
- **Linting**: Ruff (fast, comprehensive) or Flake8 (fallback)
- **Testing**: pytest with coverage plugin
- **Security**: pip-audit for dependency scanning
- **Formatting**: Black (if present in project)

#### TypeScript/JavaScript Tools
- **Linting**: ESLint with standard configuration
- **Testing**: Jest, Mocha, or npm test script
- **Security**: npm audit
- **Formatting**: Prettier (if configured)

#### Java Tools
- **Linting**: Checkstyle or SpotBugs
- **Testing**: Maven test or Gradle test
- **Security**: OWASP dependency-check
- **Build**: Maven compile or Gradle build

#### Golang Tools
- **Linting**: golangci-lint
- **Testing**: go test with coverage
- **Security**: osv-scanner
- **Formatting**: gofmt (built-in)

### Git Operations Strategy

**Decision**: Use command-line git with temporary directories
**Rationale**: Simple, reliable, handles authentication naturally through system git config
**Alternatives considered**:
- GitPython library (adds complexity, dependency management issues)
- GitHub API (limited to GitHub, doesn't handle arbitrary git repos)

### Output Format Design

**Decision**: Structured JSON with optional Markdown summary
**Rationale**: Machine-readable for automated processing, human-readable summary for review
**Format**:
```json
{
  "repository": {
    "url": "...",
    "commit": "...",
    "language": "...",
    "timestamp": "..."
  },
  "metrics": {
    "code_quality": {
      "lint_results": {...},
      "build_success": boolean,
      "security_issues": [...]
    },
    "testing": {
      "test_results": {...},
      "coverage": {...}
    },
    "documentation": {
      "readme_present": boolean,
      "api_docs": boolean
    }
  },
  "execution": {
    "tools_used": [...],
    "errors": [...],
    "duration_seconds": number
  }
}
```

### Error Handling and Graceful Degradation

**Decision**: Fail fast on critical errors, continue with warnings on tool-specific failures
**Rationale**: Aligns with constitutional KISS principle while maximizing useful output
**Critical failures**: Repository access, git operations, output generation
**Degradable failures**: Individual tool execution, specific metric collection

### Temporary Directory Management

**Decision**: Use Python tempfile with automatic cleanup
**Rationale**: OS-agnostic, secure, automatic cleanup prevents disk space issues
**Pattern**: Context managers for resource cleanup

### Dependency Installation Strategy

**Decision**: Document required tools, provide optional auto-installation for Python tools
**Rationale**: Balance between automation and system integrity
**Approach**:
- Check for tool availability first
- Provide clear error messages with installation instructions
- Auto-install only Python tools via uv when safe

## Technology Integration Patterns

### CLI Interface Pattern
```bash
./scripts/run_metrics.sh <repo_url> [commit_sha] [--output-dir] [--format json|markdown|both]
```

### Workflow Pattern
1. Validate inputs and check dependencies
2. Clone repository to temporary directory
3. Detect primary programming language
4. Execute applicable analysis tools
5. Collect and format results
6. Clean up temporary resources
7. Output results to specified location

### Testing Strategy
- **Contract tests**: Validate output JSON schema
- **Integration tests**: Test with known repositories (code-walker)
- **Unit tests**: Test individual components in isolation
- **Regression tests**: Ensure consistent results across runs

## Performance Considerations

### Repository Size Limits
- Target: Repositories under 100MB
- Timeout: 5-minute maximum execution per repository
- Disk space: Clean up immediately after analysis

### Concurrent Processing
- Support batch processing of multiple repositories
- Implement simple queue-based execution
- Respect system resource limits

## Security Considerations

### Repository Trust
- Only analyze public repositories
- Use read-only operations
- No execution of repository code
- Sandbox analysis when possible

### Tool Security
- Use official, verified tool distributions
- Regular security updates for analysis tools
- Minimal privilege execution

## Validation Plan

### Regression Testing Repository
- **Primary**: git@github.com:AIGCInnovatorSpace/code-walker.git
- **Secondary**: Create test repositories for each supported language
- **Validation criteria**: Consistent output format, expected metrics collected, error handling verification