"""Output generation for JSON and Markdown formats."""

import json
import jsonschema
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from .models.metrics_collection import MetricsCollection
from .models.repository import Repository


class OutputFormat:
    """Handles standardized output formatting for metrics results."""

    def __init__(self, schema_path: str = None) -> None:
        """Initialize output formatter with optional schema validation."""
        self.schema_path = schema_path
        self.schema = None

        if schema_path and Path(schema_path).exists():
            with open(schema_path) as f:
                self.schema = json.load(f)

    def validate_schema(self, data: Dict[str, Any]) -> bool:
        """Validate data against JSON schema."""
        if not self.schema:
            return True  # No schema available, assume valid

        try:
            jsonschema.validate(data, self.schema)
            return True
        except jsonschema.ValidationError:
            return False

    def export_json(self, repository: Repository, metrics: MetricsCollection) -> str:
        """Export metrics to JSON format."""
        output_data = self._create_output_structure(repository, metrics)

        return json.dumps(output_data, indent=2, default=self._json_serializer)

    def export_markdown(self, repository: Repository, metrics: MetricsCollection) -> str:
        """Export metrics to Markdown format."""
        output_data = self._create_output_structure(repository, metrics)

        md_content = []

        # Header
        md_content.append(f"# Code Analysis Report")
        md_content.append(f"**Generated**: {datetime.utcnow().isoformat()}Z")
        md_content.append("")

        # Repository Info
        md_content.append("## Repository Information")
        md_content.append(f"- **URL**: {output_data['repository']['url']}")
        md_content.append(f"- **Commit**: `{output_data['repository']['commit']}`")
        md_content.append(f"- **Language**: {output_data['repository']['language']}")
        md_content.append(f"- **Size**: {output_data['repository'].get('size_mb', 'Unknown')} MB")
        md_content.append("")

        # Code Quality
        md_content.append("## Code Quality")
        code_quality = output_data['metrics']['code_quality']

        if code_quality.get('lint_results'):
            lint = code_quality['lint_results']
            status = "✅ Passed" if lint.get('passed') else "❌ Failed"
            md_content.append(f"- **Linting ({lint.get('tool_used', 'Unknown')})**: {status}")
            md_content.append(f"  - Issues found: {lint.get('issues_count', 0)}")

        if code_quality.get('build_success') is not None:
            status = "✅ Success" if code_quality['build_success'] else "❌ Failed"
            md_content.append(f"- **Build**: {status}")

        if code_quality.get('security_issues') is not None:
            issues_count = len(code_quality['security_issues'])
            md_content.append(f"- **Security Issues**: {issues_count}")

        md_content.append("")

        # Testing
        md_content.append("## Testing")
        testing = output_data['metrics']['testing']

        if testing.get('test_execution'):
            test_exec = testing['test_execution']
            md_content.append(f"- **Framework**: {test_exec.get('framework', 'Unknown')}")
            md_content.append(f"- **Tests Run**: {test_exec.get('tests_run', 0)}")
            md_content.append(f"- **Tests Passed**: {test_exec.get('tests_passed', 0)}")
            md_content.append(f"- **Tests Failed**: {test_exec.get('tests_failed', 0)}")

        if testing.get('coverage_report'):
            coverage = testing['coverage_report']
            md_content.append(f"- **Line Coverage**: {coverage.get('line_coverage', 0):.1f}%")

        md_content.append("")

        # Documentation
        md_content.append("## Documentation")
        docs = output_data['metrics']['documentation']

        readme_status = "✅ Present" if docs.get('readme_present') else "❌ Missing"
        md_content.append(f"- **README**: {readme_status}")

        if docs.get('readme_quality_score') is not None:
            score = docs['readme_quality_score'] * 100
            md_content.append(f"- **README Quality**: {score:.0f}/100")

        setup_status = "✅ Yes" if docs.get('setup_instructions') else "❌ No"
        md_content.append(f"- **Setup Instructions**: {setup_status}")

        examples_status = "✅ Yes" if docs.get('usage_examples') else "❌ No"
        md_content.append(f"- **Usage Examples**: {examples_status}")

        md_content.append("")

        # Execution Summary
        md_content.append("## Execution Summary")
        execution = output_data['execution']
        md_content.append(f"- **Tools Used**: {', '.join(execution.get('tools_used', []))}")
        md_content.append(f"- **Duration**: {execution.get('duration_seconds', 0):.1f} seconds")

        if execution.get('errors'):
            md_content.append(f"- **Errors**: {len(execution['errors'])}")
            for error in execution['errors'][:3]:  # Show first 3 errors
                md_content.append(f"  - {error}")

        if execution.get('warnings'):
            md_content.append(f"- **Warnings**: {len(execution['warnings'])}")

        md_content.append("")
        md_content.append("---")
        md_content.append("*Generated by Code Score*")

        return "\n".join(md_content)

    def _create_output_structure(self, repository: Repository, metrics: MetricsCollection) -> Dict[str, Any]:
        """Create standardized output structure."""
        return {
            "schema_version": "1.0.0",
            "repository": {
                "url": repository.url,
                "commit": repository.commit_sha or "unknown",
                "language": repository.detected_language or "unknown",
                "timestamp": repository.clone_timestamp.isoformat() if repository.clone_timestamp else datetime.utcnow().isoformat(),
                "size_mb": repository.size_mb
            },
            "metrics": {
                "code_quality": {
                    "lint_results": metrics.code_quality.lint_results,
                    "build_success": metrics.code_quality.build_success,
                    "security_issues": [
                        {
                            "severity": issue.severity,
                            "title": issue.title,
                            "description": issue.description,
                            "cve_id": issue.cve_id,
                            "affected_package": issue.affected_package
                        }
                        for issue in metrics.code_quality.security_issues
                    ],
                    "dependency_audit": metrics.code_quality.dependency_audit
                },
                "testing": {
                    "test_execution": metrics.testing_metrics.test_execution,
                    "coverage_report": metrics.testing_metrics.coverage_report
                },
                "documentation": {
                    "readme_present": metrics.documentation_metrics.readme_present,
                    "readme_quality_score": metrics.documentation_metrics.readme_quality_score,
                    "api_documentation": metrics.documentation_metrics.api_documentation,
                    "setup_instructions": metrics.documentation_metrics.setup_instructions,
                    "usage_examples": metrics.documentation_metrics.usage_examples
                }
            },
            "execution": {
                "tools_used": metrics.execution_metadata.tools_used,
                "errors": metrics.execution_metadata.errors,
                "warnings": metrics.execution_metadata.warnings,
                "duration_seconds": metrics.execution_metadata.duration_seconds,
                "timestamp": metrics.execution_metadata.timestamp.isoformat()
            }
        }

    def _json_serializer(self, obj):
        """JSON serializer for non-standard types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class OutputManager:
    """Manages output file generation and organization."""

    def __init__(self, output_dir: str = "./output") -> None:
        """Initialize output manager."""
        self.output_dir = Path(output_dir)
        self.metrics_dir = self.output_dir / "metrics"

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

    def save_results(self, repository: Repository, metrics: MetricsCollection,
                    format_type: str = "both") -> List[str]:
        """Save analysis results in specified format(s)."""
        formatter = OutputFormat()
        saved_files = []

        # Generate timestamp for unique filenames
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Extract repo name from URL
        repo_name = self._extract_repo_name(repository.url)
        base_filename = f"{repo_name}_{timestamp}"

        if format_type in ["json", "both"]:
            # Save detailed metrics
            json_content = formatter.export_json(repository, metrics)
            json_file = self.metrics_dir / f"{base_filename}.json"

            with open(json_file, 'w') as f:
                f.write(json_content)
            saved_files.append(str(json_file))

            # Save consolidated submission.json
            submission_file = self.output_dir / "submission.json"
            with open(submission_file, 'w') as f:
                f.write(json_content)
            saved_files.append(str(submission_file))

        if format_type in ["markdown", "both"]:
            # Save markdown summary
            md_content = formatter.export_markdown(repository, metrics)
            md_file = self.metrics_dir / f"{base_filename}.md"

            with open(md_file, 'w') as f:
                f.write(md_content)
            saved_files.append(str(md_file))

        return saved_files

    def _extract_repo_name(self, url: str) -> str:
        """Extract repository name from URL."""
        try:
            # Handle both HTTPS and SSH URLs
            if url.endswith('.git'):
                url = url[:-4]

            parts = url.replace(':', '/').split('/')
            return parts[-1] if parts else "unknown"

        except Exception:
            return "unknown"