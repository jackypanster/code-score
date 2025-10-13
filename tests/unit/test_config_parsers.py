"""Unit tests for configuration file parsers.

These tests validate that config parsers correctly verify the presence of
required sections/keys in test framework and coverage configuration files.

Test Coverage:
- TOML Parser: Python configs (FR-005, FR-006)
- JSON Parser: JavaScript configs (FR-005, FR-006)
- Makefile Parser: Go coverage (FR-006)
- XML Parser: Java configs (FR-005, FR-006)

Expected Status: FAIL until config parsers are implemented (T017-T020).
"""

import tempfile
from pathlib import Path

import pytest


@pytest.mark.unit
class TestTomlParser:
    """Unit tests for TOML parser (Python configs - FR-005, FR-006)."""

    def test_verify_pytest_section_in_pyproject_toml(self, tmp_path: Path):
        """Test that parser detects [tool.pytest] section in pyproject.toml (FR-005)."""
        from src.metrics.config_parsers.toml_parser import verify_pytest_section

        # Create valid pyproject.toml with [tool.pytest] section
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "test-project"

[tool.pytest.ini_options]
testpaths = ["tests"]
"""
        )

        verified, message = verify_pytest_section(pyproject)
        assert verified is True, "Should detect [tool.pytest] section"
        assert "pytest" in message.lower()

    def test_missing_pytest_section_returns_false(self, tmp_path: Path):
        """Test that parser returns False for pyproject.toml without [tool.pytest] (FR-005a)."""
        from src.metrics.config_parsers.toml_parser import verify_pytest_section

        # Create pyproject.toml WITHOUT [tool.pytest] section
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "test-project"
"""
        )

        verified, message = verify_pytest_section(pyproject)
        assert verified is False, "Should return False when [tool.pytest] missing"
        assert "missing" in message.lower() or "not found" in message.lower()

    def test_malformed_toml_returns_false(self, tmp_path: Path):
        """Test that parser fails fast on malformed TOML (FR-005a, KISS fail-fast)."""
        from src.metrics.config_parsers.toml_parser import verify_pytest_section

        # Create malformed TOML
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project
name = "test-project"
"""
        )  # Missing closing bracket

        verified, message = verify_pytest_section(pyproject)
        assert verified is False, "Should return False for malformed TOML"
        assert "parse" in message.lower() or "error" in message.lower()

    def test_verify_coverage_section_in_pyproject_toml(self, tmp_path: Path):
        """Test that parser detects [tool.coverage] section (FR-006)."""
        from src.metrics.config_parsers.toml_parser import verify_coverage_section

        # Create valid pyproject.toml with [tool.coverage] section
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[tool.coverage.run]
source = ["src"]
"""
        )

        verified, message = verify_coverage_section(pyproject)
        assert verified is True, "Should detect [tool.coverage] section"

    def test_missing_coverage_section_returns_false(self, tmp_path: Path):
        """Test that parser returns False when [tool.coverage] missing (FR-006a)."""
        from src.metrics.config_parsers.toml_parser import verify_coverage_section

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[project]
name = "test-project"
"""
        )

        verified, message = verify_coverage_section(pyproject)
        assert verified is False, "Should return False when [tool.coverage] missing"


@pytest.mark.unit
class TestJsonParser:
    """Unit tests for JSON parser (JavaScript configs - FR-005, FR-006)."""

    def test_verify_test_script_in_package_json(self, tmp_path: Path):
        """Test that parser detects scripts.test key in package.json (FR-005)."""
        from src.metrics.config_parsers.json_parser import verify_test_script

        # Create valid package.json with scripts.test
        package_json = tmp_path / "package.json"
        package_json.write_text(
            """
{
  "name": "test-project",
  "scripts": {
    "test": "jest"
  }
}
"""
        )

        verified, message = verify_test_script(package_json)
        assert verified is True, "Should detect scripts.test key"
        assert "test" in message.lower()

    def test_missing_test_script_returns_false(self, tmp_path: Path):
        """Test that parser returns False when scripts.test missing (FR-005a)."""
        from src.metrics.config_parsers.json_parser import verify_test_script

        # Create package.json WITHOUT scripts.test
        package_json = tmp_path / "package.json"
        package_json.write_text(
            """
{
  "name": "test-project",
  "scripts": {
    "build": "webpack"
  }
}
"""
        )

        verified, message = verify_test_script(package_json)
        assert verified is False, "Should return False when scripts.test missing"

    def test_malformed_json_returns_false(self, tmp_path: Path):
        """Test that parser fails fast on malformed JSON (FR-005a)."""
        from src.metrics.config_parsers.json_parser import verify_test_script

        # Create malformed JSON
        package_json = tmp_path / "package.json"
        package_json.write_text(
            """
{
  "name": "test-project",
  "scripts": {
    "test": "jest"
  }
"""
        )  # Missing closing brace

        verified, message = verify_test_script(package_json)
        assert verified is False, "Should return False for malformed JSON"

    def test_verify_coverage_threshold_in_jest_config(self, tmp_path: Path):
        """Test that parser detects coverageThreshold in jest.config.js (FR-006)."""
        from src.metrics.config_parsers.json_parser import verify_coverage_threshold

        # Create jest.config.json with coverageThreshold
        jest_config = tmp_path / "jest.config.json"
        jest_config.write_text(
            """
{
  "coverageThreshold": {
    "global": {
      "branches": 80,
      "functions": 80,
      "lines": 80
    }
  }
}
"""
        )

        verified, message = verify_coverage_threshold(jest_config)
        assert verified is True, "Should detect coverageThreshold key"

    def test_missing_coverage_threshold_returns_false(self, tmp_path: Path):
        """Test that parser returns False when coverageThreshold missing (FR-006a)."""
        from src.metrics.config_parsers.json_parser import verify_coverage_threshold

        jest_config = tmp_path / "jest.config.json"
        jest_config.write_text(
            """
{
  "testMatch": ["**/*.test.js"]
}
"""
        )

        verified, message = verify_coverage_threshold(jest_config)
        assert verified is False, "Should return False when coverageThreshold missing"


@pytest.mark.unit
class TestMakefileParser:
    """Unit tests for Makefile parser (Go coverage - FR-006)."""

    def test_detects_cover_flag(self, tmp_path: Path):
        """Test that parser detects -cover flag in Makefile (FR-006)."""
        from src.metrics.config_parsers.makefile_parser import verify_coverage_flags

        # Create Makefile with -cover flag
        makefile = tmp_path / "Makefile"
        makefile.write_text(
            """
test:
\tgo test -cover ./...
"""
        )

        verified, message = verify_coverage_flags(makefile)
        assert verified is True, "Should detect -cover flag"
        assert "cover" in message.lower()

    def test_detects_coverage_keyword(self, tmp_path: Path):
        """Test that parser detects 'coverage' keyword in Makefile (FR-006)."""
        from src.metrics.config_parsers.makefile_parser import verify_coverage_flags

        # Create Makefile with coverage target
        makefile = tmp_path / "Makefile"
        makefile.write_text(
            """
coverage:
\tgo test -coverprofile=coverage.out ./...
\tgo tool cover -html=coverage.out
"""
        )

        verified, message = verify_coverage_flags(makefile)
        assert verified is True, "Should detect coverage keyword"

    def test_no_coverage_references_returns_false(self, tmp_path: Path):
        """Test that parser returns False when no coverage references (FR-006a)."""
        from src.metrics.config_parsers.makefile_parser import verify_coverage_flags

        # Create Makefile WITHOUT coverage
        makefile = tmp_path / "Makefile"
        makefile.write_text(
            """
test:
\tgo test ./...
"""
        )

        verified, message = verify_coverage_flags(makefile)
        assert verified is False, "Should return False when no coverage references"


@pytest.mark.unit
class TestXmlParser:
    """Unit tests for XML parser (Java configs - FR-005, FR-006)."""

    def test_verify_surefire_plugin_in_pom_xml(self, tmp_path: Path):
        """Test that parser detects surefire plugin in pom.xml (FR-005)."""
        from src.metrics.config_parsers.xml_parser import verify_surefire_plugin

        # Create valid pom.xml with surefire plugin
        pom_xml = tmp_path / "pom.xml"
        pom_xml.write_text(
            """
<project>
  <build>
    <plugins>
      <plugin>
        <artifactId>maven-surefire-plugin</artifactId>
        <version>2.22.2</version>
      </plugin>
    </plugins>
  </build>
</project>
"""
        )

        verified, message = verify_surefire_plugin(pom_xml)
        assert verified is True, "Should detect surefire plugin"
        assert "surefire" in message.lower()

    def test_missing_surefire_plugin_returns_false(self, tmp_path: Path):
        """Test that parser returns False when surefire plugin missing (FR-005a)."""
        from src.metrics.config_parsers.xml_parser import verify_surefire_plugin

        # Create pom.xml WITHOUT surefire plugin
        pom_xml = tmp_path / "pom.xml"
        pom_xml.write_text(
            """
<project>
  <build>
    <plugins>
    </plugins>
  </build>
</project>
"""
        )

        verified, message = verify_surefire_plugin(pom_xml)
        assert verified is False, "Should return False when surefire missing"

    def test_malformed_xml_returns_false(self, tmp_path: Path):
        """Test that parser fails fast on malformed XML (FR-005a)."""
        from src.metrics.config_parsers.xml_parser import verify_surefire_plugin

        # Create malformed XML
        pom_xml = tmp_path / "pom.xml"
        pom_xml.write_text(
            """
<project>
  <build>
    <plugins
      <plugin>
      </plugin>
    </plugins>
  </build>
</project>
"""
        )  # Missing closing bracket on <plugins>

        verified, message = verify_surefire_plugin(pom_xml)
        assert verified is False, "Should return False for malformed XML"

    def test_verify_jacoco_plugin_in_pom_xml(self, tmp_path: Path):
        """Test that parser detects jacoco plugin for coverage (FR-006)."""
        from src.metrics.config_parsers.xml_parser import verify_jacoco_plugin

        # Create valid pom.xml with jacoco plugin
        pom_xml = tmp_path / "pom.xml"
        pom_xml.write_text(
            """
<project>
  <build>
    <plugins>
      <plugin>
        <groupId>org.jacoco</groupId>
        <artifactId>jacoco-maven-plugin</artifactId>
        <version>0.8.7</version>
      </plugin>
    </plugins>
  </build>
</project>
"""
        )

        verified, message = verify_jacoco_plugin(pom_xml)
        assert verified is True, "Should detect jacoco plugin"
        assert "jacoco" in message.lower()

    def test_missing_jacoco_plugin_returns_false(self, tmp_path: Path):
        """Test that parser returns False when jacoco plugin missing (FR-006a)."""
        from src.metrics.config_parsers.xml_parser import verify_jacoco_plugin

        pom_xml = tmp_path / "pom.xml"
        pom_xml.write_text(
            """
<project>
  <build>
    <plugins>
    </plugins>
  </build>
</project>
"""
        )

        verified, message = verify_jacoco_plugin(pom_xml)
        assert verified is False, "Should return False when jacoco missing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
