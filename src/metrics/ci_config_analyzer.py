"""CI/CD configuration analyzer orchestrator.

Coordinates detection and parsing of CI configurations across multiple platforms.
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Set

from src.metrics.ci_parsers.circleci_parser import CircleCIParser
from src.metrics.ci_parsers.github_actions_parser import GitHubActionsParser
from src.metrics.ci_parsers.gitlab_ci_parser import GitLabCIParser
from src.metrics.ci_parsers.jenkins_parser import JenkinsParser
from src.metrics.ci_parsers.travis_parser import TravisParser
from src.metrics.models.ci_config import CIConfigResult, TestStepInfo
from src.metrics.pattern_matchers.coverage_tool_matcher import CoverageToolMatcher


class CIConfigAnalyzer:
    """Analyzer for CI/CD configurations across multiple platforms."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.coverage_matcher = CoverageToolMatcher()

        # Platform parsers
        self.parsers = {
            'github_actions': GitHubActionsParser(),
            'gitlab_ci': GitLabCIParser(),
            'circleci': CircleCIParser(),
            'travis_ci': TravisParser(),
            'jenkins': JenkinsParser(),
        }

    def analyze_ci_config(self, repo_path: Path) -> CIConfigResult:
        """Analyze CI/CD configuration in repository.

        Args:
            repo_path: Path to cloned repository root

        Returns:
            CIConfigResult with platform detection and scoring
        """
        # Start timing (FR-027: detailed level)
        start_time = time.time()

        if not repo_path.exists() or not repo_path.is_dir():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        self.logger.debug(f"Starting CI configuration analysis for: {repo_path}")

        # Detect CI platforms
        detected_platforms = self._detect_ci_platforms(repo_path)

        if not detected_platforms:
            # No CI configuration found
            self.logger.info("No CI configuration detected")
            return CIConfigResult(
                platform=None,
                config_file_path=None,
                has_test_steps=False,
                test_commands=[],
                has_coverage_upload=False,
                coverage_tools=[],
                test_job_count=0,
                calculated_score=0,
                parse_errors=[]
            )

        # Log detected platforms (standard level)
        platform_names = ', '.join(detected_platforms.keys())
        self.logger.info(f"Detected CI platforms: {platform_names}")

        # Parse all detected platforms
        platform_results = {}
        for platform_name, config_path in detected_platforms.items():
            self.logger.debug(f"Parsing workflow file: {config_path}")
            parser = self.parsers[platform_name]
            try:
                test_steps = parser.parse(config_path)
                if test_steps is not None:
                    platform_results[platform_name] = {
                        'config_path': config_path,
                        'test_steps': test_steps
                    }
                    self.logger.debug(f"Successfully parsed {platform_name}: {len(test_steps)} test steps found")
            except Exception as e:
                # Parse error (minimal level - WARNING)
                self.logger.warning(f"Parse error in {config_path}: {e}")

        if not platform_results:
            # All parsers failed
            return CIConfigResult(
                platform=list(detected_platforms.keys())[0],
                config_file_path=str(list(detected_platforms.values())[0]),
                has_test_steps=False,
                test_commands=[],
                has_coverage_upload=False,
                coverage_tools=[],
                test_job_count=0,
                calculated_score=0,
                parse_errors=["All CI parsers failed"]
            )

        # Use platform with highest score (per research.md)
        best_platform, best_result = max(
            platform_results.items(),
            key=lambda x: self._calculate_platform_score(x[1]['test_steps'])
        )

        test_steps = best_result['test_steps']
        config_path = best_result['config_path']

        # Aggregate data
        test_commands = [step.command for step in test_steps]
        test_job_names = set(step.job_name for step in test_steps)
        test_job_count = len(test_job_names)

        # Detect coverage tools from all commands
        all_commands = []
        for platform_data in platform_results.values():
            for step in platform_data['test_steps']:
                all_commands.append(step.command)

        coverage_tools = self.coverage_matcher.detect_coverage_tools(all_commands)

        # Also check if any test step has coverage flag
        has_coverage_flag = any(step.has_coverage_flag for step in test_steps)

        # Calculate score
        score = 0
        has_test_steps = len(test_steps) > 0
        has_coverage_upload = len(coverage_tools) > 0 or has_coverage_flag

        if has_test_steps:
            score += 5
        if has_coverage_upload:
            score += 5
        if test_job_count >= 2:
            score += 3

        final_score = min(score, 13)

        # Log analysis results (standard level)
        self.logger.info(
            f"CI analysis complete: platform={best_platform}, "
            f"test_steps={len(test_steps)}, coverage_tools={len(coverage_tools)}, "
            f"test_jobs={test_job_count}, score={final_score}"
        )

        # Log execution time (detailed level)
        execution_time = time.time() - start_time
        self.logger.debug(f"CI analysis execution time: {execution_time:.3f} seconds")

        result = CIConfigResult(
            platform=best_platform,
            config_file_path=str(config_path.relative_to(repo_path)),
            has_test_steps=has_test_steps,
            test_commands=test_commands,
            has_coverage_upload=has_coverage_upload,
            coverage_tools=coverage_tools,
            test_job_count=test_job_count,
            calculated_score=final_score,
            parse_errors=[]
        )

        # Log final score (minimal level - always visible as INFO in standard mode)
        self.logger.info(f"Final CI score: {final_score}/13")

        return result

    def _detect_ci_platforms(self, repo_path: Path) -> Dict[str, Path]:
        """Detect CI platforms by checking for config files."""
        detected = {}

        # GitHub Actions
        gh_workflows = repo_path / '.github' / 'workflows'
        if gh_workflows.exists():
            yml_files = list(gh_workflows.glob('*.yml')) + list(gh_workflows.glob('*.yaml'))
            if yml_files:
                detected['github_actions'] = yml_files[0]

        # GitLab CI
        gitlab_ci = repo_path / '.gitlab-ci.yml'
        if gitlab_ci.exists():
            detected['gitlab_ci'] = gitlab_ci

        # CircleCI
        circleci_config = repo_path / '.circleci' / 'config.yml'
        if circleci_config.exists():
            detected['circleci'] = circleci_config

        # Travis CI
        travis_yml = repo_path / '.travis.yml'
        if travis_yml.exists():
            detected['travis_ci'] = travis_yml

        # Jenkins
        jenkinsfile = repo_path / 'Jenkinsfile'
        if jenkinsfile.exists():
            detected['jenkins'] = jenkinsfile

        return detected

    def _calculate_platform_score(self, test_steps: List[TestStepInfo]) -> int:
        """Calculate score for a platform (for comparison)."""
        if not test_steps:
            return 0

        test_job_count = len(set(step.job_name for step in test_steps))
        coverage_flags = any(step.has_coverage_flag for step in test_steps)

        score = 5  # Has test steps
        if coverage_flags:
            score += 5
        if test_job_count >= 2:
            score += 3
        return score
