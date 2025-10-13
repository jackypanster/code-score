"""XML parser for Java test framework and coverage configurations.

This module provides functions to verify the presence of required plugins
in Java build configuration files (pom.xml, build.gradle).

Constitutional Compliance:
- Principle II (KISS): Simple XML parsing with ElementTree, fail-fast
- Principle III (Transparency): Clear return values and error messages
"""

import xml.etree.ElementTree as ET
from pathlib import Path


def verify_surefire_plugin(file_path: Path) -> tuple[bool, str]:
    """Verify that pom.xml contains maven-surefire-plugin (FR-005).

    Args:
        file_path: Path to pom.xml file

    Returns:
        Tuple of (verified: bool, message: str)
        - verified: True if surefire plugin found, False otherwise
        - message: Human-readable explanation of result

    Examples:
        >>> verify_surefire_plugin(Path("pom.xml"))
        (True, "Found maven-surefire-plugin in pom.xml")

    Note:
        - Searches for <artifactId>maven-surefire-plugin</artifactId>
        - For build.gradle, checks for "test" task keyword
        - Malformed XML returns (False, "parse error message")
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    # Handle build.gradle (Gradle build files)
    if file_path.name == "build.gradle":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for "test" task in Gradle
            if "test {" in content or "test{" in content or "task test" in content:
                return True, "Found test task in build.gradle"
            else:
                return False, "No test task found in build.gradle"

        except Exception as e:
            return False, f"Error reading file: {str(e)}"

    # Handle pom.xml (Maven build files)
    if file_path.name == "pom.xml":
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Maven uses namespaces, need to handle both with and without
            # Search for maven-surefire-plugin in artifactId tags
            for elem in root.iter():
                if elem.tag.endswith("artifactId") and "surefire" in elem.text:
                    return True, "Found maven-surefire-plugin in pom.xml"

            return False, "No maven-surefire-plugin found in pom.xml"

        except ET.ParseError as e:
            # Fail-fast on parsing errors (KISS principle)
            return False, f"XML parse error: {str(e)}"
        except Exception as e:
            return False, f"Error reading file: {str(e)}"

    return False, f"Unexpected file type: {file_path.name}"


def verify_jacoco_plugin(file_path: Path) -> tuple[bool, str]:
    """Verify that pom.xml or build.gradle contains jacoco plugin (FR-006).

    Args:
        file_path: Path to pom.xml or build.gradle file

    Returns:
        Tuple of (verified: bool, message: str)
        - verified: True if jacoco plugin found, False otherwise
        - message: Human-readable explanation of result

    Examples:
        >>> verify_jacoco_plugin(Path("pom.xml"))
        (True, "Found jacoco-maven-plugin in pom.xml")

    Note:
        - For pom.xml: searches for jacoco-maven-plugin
        - For build.gradle: searches for jacoco plugin reference
        - Malformed XML returns (False, "parse error message")
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    # Handle build.gradle (Gradle build files)
    if file_path.name == "build.gradle":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for jacoco plugin in Gradle
            if "jacoco" in content.lower():
                return True, "Found jacoco plugin in build.gradle"
            else:
                return False, "No jacoco plugin found in build.gradle"

        except Exception as e:
            return False, f"Error reading file: {str(e)}"

    # Handle pom.xml (Maven build files)
    if file_path.name == "pom.xml":
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Search for jacoco plugin in artifactId or groupId tags
            for elem in root.iter():
                if (elem.tag.endswith("artifactId") or elem.tag.endswith("groupId")) and elem.text:
                    if "jacoco" in elem.text.lower():
                        return True, "Found jacoco-maven-plugin in pom.xml"

            return False, "No jacoco plugin found in pom.xml"

        except ET.ParseError as e:
            # Fail-fast on parsing errors (KISS principle)
            return False, f"XML parse error: {str(e)}"
        except Exception as e:
            return False, f"Error reading file: {str(e)}"

    return False, f"Unexpected file type: {file_path.name}"
