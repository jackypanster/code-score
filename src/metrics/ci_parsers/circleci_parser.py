"""CircleCI configuration parser for test evidence extraction.

This module provides a parser for CircleCI configuration files (.circleci/config.yml)
to extract test execution steps from job definitions.

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


class CircleCIParser(CIParser):
    """Parser for CircleCI configuration files.

    Parses .circleci/config.yml files to extract test execution evidence.
    Supports CircleCI 2.x syntax including:
    - jobs: section with job definitions
    - steps: lists within jobs
    - run: commands (test execution)

    Example CircleCI structure:
        version: 2.1
        jobs:
          test-job:
            steps:
              - checkout
              - run:
                  name: Run tests
                  command: pytest --cov=src tests/
              - run: npm test

    Example:
        >>> parser = CircleCIParser()
        >>> test_steps = parser.parse(Path(".circleci/config.yml"))
        >>> if test_steps:
        ...     print(f"Found {len(test_steps)} test steps")
    """

    def __init__(self):
        """Initialize parser with test command matcher."""
        super().__init__()
        self.test_matcher = TestCommandMatcher()

    def parse(self, config_path: Path) -> Optional[List[TestStepInfo]]:
        """Parse CircleCI configuration file to extract test steps.

        Extracts test commands from job steps. Supports both simple and
        complex run command formats.

        Args:
            config_path: Path to .circleci/config.yml file.

        Returns:
            List[TestStepInfo] if config valid and test steps found.
            Empty list [] if config valid but no test steps.
            None if config malformed (YAML parse error).

        Raises:
            FileNotFoundError: If config_path does not exist.

        Example:
            >>> parser = CircleCIParser()
            >>> steps = parser.parse(Path(".circleci/config.yml"))
            >>> for step in steps:
            ...     print(f"{step.job_name}: {step.command}")
        """
        # Check if file exists
        if not config_path.exists():
            raise FileNotFoundError(f"CircleCI config not found: {config_path}")

        try:
            # Parse YAML configuration file
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Validate config structure
            if not config or not isinstance(config, dict):
                self.logger.warning(f"Invalid CircleCI config structure in {config_path}")
                return None

            # Extract jobs section
            jobs = config.get('jobs', {})
            if not jobs or not isinstance(jobs, dict):
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
            # Handle different step formats
            if isinstance(step, dict) and 'run' in step:
                run_config = step['run']

                # Extract command from run step
                if isinstance(run_config, str):
                    # Simple format: run: "command"
                    command = run_config
                elif isinstance(run_config, dict):
                    # Complex format: run: { name: "...", command: "..." }
                    command = run_config.get('command', '')
                else:
                    continue

                # Check if it's a test command
                if command and self.test_matcher.is_test_command(command):
                    test_step_info = TestStepInfo(
                        job_name=job_name,
                        command=command,
                        framework=self.test_matcher.infer_framework(command),
                        has_coverage_flag=self.test_matcher.has_coverage_flag(command)
                    )
                    test_steps.append(test_step_info)

        return test_steps
