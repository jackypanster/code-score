"""GitHub Actions workflow parser for test evidence extraction.

This module provides a parser for GitHub Actions workflow files (.yml/.yaml)
to extract test execution steps and coverage upload actions.

Constitutional Compliance:
- Principle II (KISS): Simple YAML parsing with yaml.safe_load()
- Principle III (Transparency): Clear error logging and step extraction
"""

from pathlib import Path
from typing import Dict, List, Optional

import yaml

from src.metrics.ci_parsers.base import CIParser
from src.metrics.models.ci_config import TestStepInfo
from src.metrics.pattern_matchers.test_command_matcher import TestCommandMatcher


class GitHubActionsParser(CIParser):
    """Parser for GitHub Actions workflow files.

    Parses .github/workflows/*.yml files to extract test execution evidence.
    Supports GitHub Actions workflow syntax including:
    - jobs → steps structure
    - run: commands (test execution)
    - uses: actions (coverage upload detection)

    Example workflow structure:
        jobs:
          test-job:
            runs-on: ubuntu-latest
            steps:
              - name: Run tests
                run: pytest --cov=src tests/
              - uses: codecov/codecov-action@v3

    Example:
        >>> parser = GitHubActionsParser()
        >>> test_steps = parser.parse(Path(".github/workflows/test.yml"))
        >>> if test_steps:
        ...     print(f"Found {len(test_steps)} test steps")
    """

    def __init__(self):
        """Initialize parser with test command matcher."""
        super().__init__()
        self.test_matcher = TestCommandMatcher()

    def parse(self, config_path: Path) -> Optional[List[TestStepInfo]]:
        """Parse GitHub Actions workflow file to extract test steps.

        Extracts test commands from workflow jobs and steps. Handles both
        simple and complex run commands (single line and multi-line).

        Args:
            config_path: Path to workflow YAML file
                (e.g., .github/workflows/test.yml)

        Returns:
            List[TestStepInfo] if workflow valid and test steps found.
            Empty list [] if workflow valid but no test steps.
            None if workflow malformed (YAML parse error).

        Raises:
            FileNotFoundError: If config_path does not exist.

        Example:
            >>> parser = GitHubActionsParser()
            >>> steps = parser.parse(Path(".github/workflows/test.yml"))
            >>> for step in steps:
            ...     print(f"{step.job_name}: {step.command}")
        """
        # Check if file exists
        if not config_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {config_path}")

        try:
            # Parse YAML workflow file
            with open(config_path, 'r', encoding='utf-8') as f:
                workflow = yaml.safe_load(f)

            # Validate workflow structure
            if not workflow or not isinstance(workflow, dict):
                self.logger.warning(f"Invalid workflow structure in {config_path}")
                return None

            # Extract jobs
            jobs = workflow.get('jobs', {})
            if not jobs or not isinstance(jobs, dict):
                # Valid workflow but no jobs
                return []

            # Extract test steps from all jobs
            test_steps = []
            for job_name, job_config in jobs.items():
                if not isinstance(job_config, dict):
                    continue

                job_test_steps = self._extract_test_steps_from_job(
                    job_name, job_config
                )
                test_steps.extend(job_test_steps)

            return test_steps

        except yaml.YAMLError as e:
            self._log_parse_error(e, config_path)
            return None
        except Exception as e:
            self._log_parse_error(e, config_path)
            return None

    def _extract_test_steps_from_job(
        self, job_name: str, job_config: Dict
    ) -> List[TestStepInfo]:
        """Extract test steps from a single job.

        Args:
            job_name: Name of the job (e.g., "unit-tests")
            job_config: Job configuration dictionary

        Returns:
            List of TestStepInfo for test commands found in this job.
        """
        test_steps = []

        steps = job_config.get('steps', [])
        if not isinstance(steps, list):
            return test_steps

        for step in steps:
            if not isinstance(step, dict):
                continue

            # Extract run commands (test execution)
            run_command = step.get('run')
            if run_command and isinstance(run_command, str):
                # Handle multi-line commands (split and check each line)
                for line in run_command.split('\n'):
                    line = line.strip()
                    if line and self.test_matcher.is_test_command(line):
                        test_step_info = TestStepInfo(
                            job_name=job_name,
                            command=line,
                            framework=self.test_matcher.infer_framework(line),
                            has_coverage_flag=self.test_matcher.has_coverage_flag(line)
                        )
                        test_steps.append(test_step_info)

        return test_steps
