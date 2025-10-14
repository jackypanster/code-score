"""Travis CI configuration parser for test evidence extraction."""

from pathlib import Path
from typing import List, Optional, Union
import yaml
from src.metrics.ci_parsers.base import CIParser
from src.metrics.models.ci_config import TestStepInfo
from src.metrics.pattern_matchers.test_command_matcher import TestCommandMatcher


class TravisParser(CIParser):
    """Parser for Travis CI configuration files (.travis.yml)."""

    def __init__(self):
        super().__init__()
        self.test_matcher = TestCommandMatcher()

    def parse(self, config_path: Path) -> Optional[List[TestStepInfo]]:
        if not config_path.exists():
            raise FileNotFoundError(f"Travis CI config not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            if not config or not isinstance(config, dict):
                self.logger.warning(f"Invalid Travis CI config in {config_path}")
                return None

            test_steps = []

            # Extract from script section (main test execution)
            script = config.get('script')
            if script:
                commands = self._normalize_to_list(script)
                for cmd in commands:
                    if self.test_matcher.is_test_command(cmd):
                        test_steps.append(TestStepInfo(
                            job_name="travis_script",
                            command=cmd,
                            framework=self.test_matcher.infer_framework(cmd),
                            has_coverage_flag=self.test_matcher.has_coverage_flag(cmd)
                        ))

            # Check after_success for coverage uploads
            after_success = config.get('after_success')
            if after_success:
                commands = self._normalize_to_list(after_success)
                for cmd in commands:
                    if self.test_matcher.is_test_command(cmd):
                        test_steps.append(TestStepInfo(
                            job_name="travis_after_success",
                            command=cmd,
                            framework=self.test_matcher.infer_framework(cmd),
                            has_coverage_flag=self.test_matcher.has_coverage_flag(cmd)
                        ))

            return test_steps

        except yaml.YAMLError as e:
            self._log_parse_error(e, config_path)
            return None
        except Exception as e:
            self._log_parse_error(e, config_path)
            return None

    def _normalize_to_list(self, value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, str):
            return [value]
        elif isinstance(value, list):
            return [str(item).strip() for item in value if item]
        return []
