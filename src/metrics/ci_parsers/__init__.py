"""CI/CD configuration parsers for test evidence extraction.

This package provides parsers for multiple CI/CD platforms to extract
test execution evidence from configuration files.

Supported Platforms:
- GitHub Actions (.github/workflows/*.yml)
- GitLab CI (.gitlab-ci.yml)
- CircleCI (.circleci/config.yml)
- Travis CI (.travis.yml)
- Jenkins (Jenkinsfile)

Constitutional Compliance:
- Principle II (KISS): Simple YAML parsing, no complex DSL interpretation
- Principle III (Transparency): Clear parse errors and logging
"""

from src.metrics.ci_parsers.base import CIParser
from src.metrics.ci_parsers.github_actions_parser import GitHubActionsParser
from src.metrics.ci_parsers.gitlab_ci_parser import GitLabCIParser

__all__ = ["CIParser", "GitHubActionsParser", "GitLabCIParser"]
