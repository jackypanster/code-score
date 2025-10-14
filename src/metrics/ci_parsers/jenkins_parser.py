"""Jenkins configuration parser for test evidence extraction."""

import re
from pathlib import Path
from typing import List, Optional
from src.metrics.ci_parsers.base import CIParser
from src.metrics.models.ci_config import TestStepInfo
from src.metrics.pattern_matchers.test_command_matcher import TestCommandMatcher


class JenkinsParser(CIParser):
    """Parser for Jenkinsfile using regex extraction (no full Groovy parsing)."""

    def __init__(self):
        super().__init__()
        self.test_matcher = TestCommandMatcher()

    def parse(self, config_path: Path) -> Optional[List[TestStepInfo]]:
        if not config_path.exists():
            raise FileNotFoundError(f"Jenkinsfile not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()

            test_steps = []

            # Regex patterns for sh/bat commands (case-insensitive, capture any test command)
            sh_pattern = r"sh\s+['\"]([^'\"]+)['\"]"
            bat_pattern = r"bat\s+['\"]([^'\"]+)['\"]"

            # Extract sh commands
            for match in re.finditer(sh_pattern, content, re.IGNORECASE):
                command = match.group(1)
                if self.test_matcher.is_test_command(command):
                    test_steps.append(TestStepInfo(
                        job_name="jenkins_pipeline",
                        command=command,
                        framework=self.test_matcher.infer_framework(command),
                        has_coverage_flag=self.test_matcher.has_coverage_flag(command)
                    ))

            # Extract bat commands
            for match in re.finditer(bat_pattern, content, re.IGNORECASE):
                command = match.group(1)
                if self.test_matcher.is_test_command(command):
                    test_steps.append(TestStepInfo(
                        job_name="jenkins_pipeline",
                        command=command,
                        framework=self.test_matcher.infer_framework(command),
                        has_coverage_flag=self.test_matcher.has_coverage_flag(command)
                    ))

            return test_steps if test_steps else []

        except Exception as e:
            self._log_parse_error(e, config_path)
            return None
