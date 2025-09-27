# Data Model: Git Repository Metrics Collection

## Core Entities

### Repository
Represents the target Git repository being analyzed.

**Attributes**:
- `url`: String - Git repository URL (required)
- `commit_sha`: String - Specific commit to analyze (optional, defaults to HEAD)
- `local_path`: String - Temporary local clone path
- `detected_language`: String - Primary programming language detected
- `clone_timestamp`: DateTime - When repository was cloned
- `size_mb`: Float - Repository size in megabytes

**Validation Rules**:
- URL must be valid Git repository format
- commit_sha must be valid SHA-1 hash if provided
- detected_language must be one of supported languages

**State Transitions**:
1. `initialized` → `cloning` → `cloned` → `analyzed` → `cleaned`
2. Error states: `clone_failed`, `analysis_failed`

### MetricsCollection
Container for all collected quality metrics from repository analysis.

**Attributes**:
- `repository_id`: String - Reference to analyzed repository
- `collection_timestamp`: DateTime - When metrics were collected
- `code_quality`: CodeQualityMetrics - Static analysis results
- `testing_metrics`: TestingMetrics - Test execution and coverage results
- `documentation_metrics`: DocumentationMetrics - Documentation quality assessment
- `execution_metadata`: ExecutionMetadata - Tool execution details

**Relationships**:
- Has one Repository
- Contains multiple metric categories

### CodeQualityMetrics
Static code analysis results including linting, security, and build verification.

**Attributes**:
- `lint_results`: LintResults - Linting tool output
- `build_success`: Boolean - Whether code builds successfully
- `security_issues`: List[SecurityIssue] - Security vulnerability findings
- `dependency_audit`: DependencyAudit - Dependency security scan results
- `formatting_compliance`: Boolean - Code formatting adherence

**Validation Rules**:
- At least one analysis tool must execute successfully
- Security issues must include severity classification

### TestingMetrics
Testing execution results and coverage analysis.

**Attributes**:
- `test_execution`: TestExecution - Test run results
- `coverage_report`: CoverageReport - Code coverage analysis
- `test_files_found`: Integer - Number of test files detected
- `test_framework`: String - Detected testing framework

**Validation Rules**:
- Coverage percentage must be between 0-100
- Test execution status must be valid enum value

### DocumentationMetrics
Documentation quality and completeness assessment.

**Attributes**:
- `readme_present`: Boolean - README file exists
- `readme_quality_score`: Float - README completeness score (0-1)
- `api_documentation`: Boolean - API docs present
- `setup_instructions`: Boolean - Setup/installation instructions present
- `usage_examples`: Boolean - Usage examples provided

### LanguageDetector
Component responsible for identifying repository's primary programming language.

**Attributes**:
- `detection_strategy`: String - Method used for detection
- `confidence_score`: Float - Detection confidence (0-1)
- `file_extensions`: List[String] - File extensions analyzed
- `detected_languages`: Dict - All languages found with percentages

**Methods**:
- `detect_primary_language(repository_path)` → String
- `get_language_statistics(repository_path)` → Dict

### ToolExecutor
Executes language-specific analysis tools and captures results.

**Attributes**:
- `tool_name`: String - Name of executed tool
- `tool_version`: String - Version of tool used
- `execution_command`: String - Command executed
- `exit_code`: Integer - Tool exit status
- `stdout`: String - Standard output from tool
- `stderr`: String - Standard error from tool
- `execution_time_seconds`: Float - Tool execution duration

**State Transitions**:
1. `pending` → `running` → `completed`
2. Error states: `failed`, `timeout`, `not_found`

### OutputFormat
Standardized structure for metrics results output.

**Attributes**:
- `format_type`: String - Output format (json, markdown, both)
- `schema_version`: String - Output schema version
- `generated_timestamp`: DateTime - When output was generated
- `file_paths`: List[String] - Generated output file paths
- `validation_status`: Boolean - Schema validation passed

**Methods**:
- `validate_schema()` → Boolean
- `export_json(metrics_collection)` → String
- `export_markdown(metrics_collection)` → String

## Entity Relationships

```
Repository (1) ←→ (1) MetricsCollection
    ↓
LanguageDetector (1) ←→ (*) ToolExecutor
    ↓
MetricsCollection (1) → (1) CodeQualityMetrics
                     → (1) TestingMetrics
                     → (1) DocumentationMetrics
                     → (1) ExecutionMetadata
    ↓
OutputFormat (1) ← (*) MetricsCollection
```

## Data Flow

1. **Input**: Repository URL + optional commit SHA
2. **Clone**: Repository → local temporary directory
3. **Detect**: LanguageDetector → primary programming language
4. **Execute**: ToolExecutor → language-specific analysis tools
5. **Collect**: Individual tool results → MetricsCollection
6. **Format**: MetricsCollection → OutputFormat (JSON/Markdown)
7. **Cleanup**: Remove temporary files and directories

## Validation Constraints

### Business Rules
- Repository must be publicly accessible
- At least one metric category must be successfully collected
- Output must conform to defined JSON schema
- Temporary files must be cleaned up after processing

### Data Integrity
- All timestamps in UTC format
- File sizes in consistent units (MB)
- Percentage values between 0-100
- Boolean flags for binary conditions

### Error Handling
- Invalid repository URLs → immediate failure
- Network timeouts → retry with exponential backoff
- Tool execution failures → log error, continue with other tools
- Schema validation failures → fail entire operation