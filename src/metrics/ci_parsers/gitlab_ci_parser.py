"""GitLab CI configuration parser for test evidence extraction.

This module provides a parser for GitLab CI configuration files (.gitlab-ci.yml)
to extract test execution steps from script sections.

Constitutional Compliance:
- Principle II (KISS): Simple YAML parsing with yaml.safe_load()
- Principle III (Transparency): Clear error logging and step extraction
"""

from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml

from src.metrics.ci_parsers.base import CIParser
from src.metrics.models.ci_config import TestStepInfo
from src.metrics.pattern_matchers.test_command_matcher import TestCommandMatcher


class GitLabCIParser(CIParser):
    """Parser for GitLab CI configuration files.

    Parses .gitlab-ci.yml files to extract test execution evidence.
    Supports GitLab CI syntax including:
    - Job definitions (top-level keys)
    - script: lists (test execution)
    - after_script: lists (cleanup/coverage)
    - stages: for organization

    Example GitLab CI structure:
        unit_tests:
          stage: test
          script:
            - pip install -r requirements.txt
            - pytest --cov=src tests/unit
          after_script:
            - codecov upload

    Example:
        >>> parser = GitLabCIParser()
        >>> test_steps = parser.parse(Path(".gitlab-ci.yml"))
        >>> if test_steps:
        ...     print(f"Found {len(test_steps)} test steps")
    """

    # Reserved GitLab CI keywords that are not job definitions
    RESERVED_KEYWORDS = {
        'image', 'services', 'stages', 'variables', 'cache', 'before_script',
        'after_script', 'artifacts', 'retry', 'timeout', 'parallel', 'trigger',
        'include', 'extends', 'pages', 'workflow', 'default', 'inherit'
    }

    def __init__(self):
        """Initialize parser with test command matcher."""
        super().__init__()
        self.test_matcher = TestCommandMatcher()

    def parse(self, config_path: Path) -> Optional[List[TestStepInfo]]:
        """Parse GitLab CI configuration file to extract test steps.

        Extracts test commands from job script sections. GitLab CI uses
        a flat structure where most top-level keys are job definitions.

        Args:
            config_path: Path to .gitlab-ci.yml file.

        Returns:
            List[TestStepInfo] if config valid and test steps found.
            Empty list [] if config valid but no test steps.
            None if config malformed (YAML parse error).

        Raises:
            FileNotFoundError: If config_path does not exist.

        Example:
            >>> parser = GitLabCIParser()
            >>> steps = parser.parse(Path(".gitlab-ci.yml"))
            >>> for step in steps:
            ...     print(f"{step.job_name}: {step.command}")
        """
        # Check if file exists
        if not config_path.exists():
            raise FileNotFoundError(f"GitLab CI config not found: {config_path}")

        try:
            # Parse YAML configuration file
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Validate config structure
            if not config or not isinstance(config, dict):
                self.logger.warning(f"Invalid GitLab CI config structure in {config_path}")
                return None

            # Extract test steps from all jobs
            test_steps = []
            for job_name, job_config in config.items():
                # Skip reserved keywords and non-job entries
                if job_name in self.RESERVED_KEYWORDS or job_name.startswith('.'):
                    continue

                # Skip if not a valid job definition
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
            job_name: Name of the job (e.g., "unit_tests")
            job_config: Job configuration dictionary

        Returns:
            List of TestStepInfo for test commands found in this job.
        """
        test_steps = []

        # Extract commands from script section
        script = job_config.get('script')
        if script:
            commands = self._normalize_script_to_list(script)
            for command in commands:
                if self.test_matcher.is_test_command(command):
                    test_step_info = TestStepInfo(
                        job_name=job_name,
                        command=command,
                        framework=self.test_matcher.infer_framework(command),
                        has_coverage_flag=self.test_matcher.has_coverage_flag(command)
                    )
                    test_steps.append(test_step_info)

        # Also check after_script (sometimes contains test commands or coverage uploads)
        after_script = job_config.get('after_script')
        if after_script:
            commands = self._normalize_script_to_list(after_script)
            for command in commands:
                if self.test_matcher.is_test_command(command):
                    test_step_info = TestStepInfo(
                        job_name=f"{job_name} (after_script)",
                        command=command,
                        framework=self.test_matcher.infer_framework(command),
                        has_coverage_flag=self.test_matcher.has_coverage_flag(command)
                    )
                    test_steps.append(test_step_info)

        return test_steps

    def _normalize_script_to_list(self, script: Union[str, List[str]]) -> List[str]:
        """Normalize script to list of commands.

        GitLab CI script can be either a string or a list of strings.

        Args:
            script: Script value from YAML (string or list)

        Returns:
            List of command strings
        """
        if isinstance(script, str):
            # Single command as string
            return [script]
        elif isinstance(script, list):
            # List of commands - flatten and strip
            commands = []
            for item in script:
                if isinstance(item, str):
                    commands.append(item.strip())
            return commands
        else:
            return []
