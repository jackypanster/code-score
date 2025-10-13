"""Configuration file parsers for test infrastructure analysis.

This module provides parsers for various test framework and coverage
configuration files across multiple programming languages:

- TOML Parser: Python configs (pyproject.toml, pytest.ini)
- JSON Parser: JavaScript configs (package.json, jest.config.js)
- Makefile Parser: Go coverage flags (Makefile)
- XML Parser: Java configs (pom.xml, build.gradle)

All parsers follow a fail-fast approach: parsing errors immediately
return False without attempting recovery (KISS principle).

Constitutional Compliance:
- Principle II (KISS): Simple parsing, no complex error recovery
- Principle III (Transparency): Clear docstrings and error messages
"""

__all__ = [
    "toml_parser",
    "json_parser",
    "makefile_parser",
    "xml_parser",
]
