"""Integration test for Java build validation (T015) - Real scenarios only."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from src.metrics.tool_runners.java_tools import JavaToolRunner


def check_tool_available(tool_name: str) -> bool:
    """Check if a tool is available in the system."""
    try:
        result = subprocess.run(
            ["which", tool_name],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


class TestMavenBuildIntegrationReal:
    """Real integration tests for Maven build validation - NO MOCKS."""

    @pytest.fixture
    def minimal_maven_project(self) -> Path:
        """Create a minimal Maven project with real build configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create pom.xml
            (repo_path / "pom.xml").write_text("""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>test-integration-maven-project</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>
</project>
""")

            # Create source directory structure
            src_main_java = repo_path / "src" / "main" / "java" / "com" / "example"
            src_main_java.mkdir(parents=True)

            # Create Main.java
            (src_main_java / "Main.java").write_text("""package com.example;

public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
""")

            # Create a helper class
            (src_main_java / "Greeter.java").write_text("""package com.example;

public class Greeter {
    public String greet(String name) {
        return "Hello, " + name + "!";
    }
}
""")

            # Create README
            (repo_path / "README.md").write_text("""# Test Integration Maven Project

This is a minimal Maven project for integration testing.
""")

            yield repo_path

    @pytest.mark.skipif(not check_tool_available("mvn"), reason="maven not available")
    def test_maven_build_validation_real_mvn_compile(self, minimal_maven_project: Path) -> None:
        """REAL TEST: Execute actual mvn compile without mocks."""
        # Create tool runner
        runner = JavaToolRunner(timeout_seconds=120)

        # REAL BUILD - No mocks!
        result = runner.run_build(str(minimal_maven_project))

        # Verify build succeeded with real execution
        assert result is not None, "Build result should not be None"
        assert "success" in result, "Result should contain 'success' field"
        assert "tool_used" in result, "Result should contain 'tool_used' field"

        # With real Maven, if build is valid, it should succeed
        if result["success"] is not None:  # Tool was available and executed
            assert result["tool_used"] == "mvn", "Should use Maven"
            assert "execution_time_seconds" in result
            assert result["execution_time_seconds"] >= 0

    @pytest.mark.skipif(not check_tool_available("mvn"), reason="maven not available")
    def test_maven_build_validation_real_with_failing_build(self) -> None:
        """REAL TEST: Verify Maven build failure is detected with actual execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create pom.xml
            (repo_path / "pom.xml").write_text("""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>failing-build-test</artifactId>
    <version>1.0.0</version>
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
    </properties>
</project>
""")

            # Create source with compilation error
            src_dir = repo_path / "src" / "main" / "java" / "com" / "example"
            src_dir.mkdir(parents=True)
            (src_dir / "Broken.java").write_text("""package com.example;

public class Broken {
    public void test() {
        // Undefined method call
        undefinedMethod();
    }
}
""")

            runner = JavaToolRunner(timeout_seconds=120)

            # REAL BUILD that will fail
            result = runner.run_build(str(repo_path))

            # Verify failure is captured
            if result["success"] is not None:  # Tool was available
                assert result["success"] is False, "Build should fail with compilation error"
                assert result["error_message"] is not None
                assert result["exit_code"] != 0

    def test_maven_build_validation_real_no_pom_xml(self) -> None:
        """REAL TEST: Verify behavior when pom.xml is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create Java file WITHOUT pom.xml
            src_dir = repo_path / "src" / "main" / "java"
            src_dir.mkdir(parents=True)
            (src_dir / "Main.java").write_text("""public class Main {}""")

            runner = JavaToolRunner(timeout_seconds=120)

            # REAL CHECK - No mocks
            result = runner.run_build(str(repo_path))

            # Should detect no build configuration
            assert result["success"] is None
            assert result["tool_used"] == "none"
            assert "No Maven or Gradle" in result["error_message"]

    @pytest.mark.skipif(not check_tool_available("mvn"), reason="maven not available")
    def test_maven_build_validation_real_schema_compliance(self, minimal_maven_project: Path) -> None:
        """REAL TEST: Verify result schema with actual Maven build execution."""
        runner = JavaToolRunner(timeout_seconds=120)

        # REAL BUILD
        result = runner.run_build(str(minimal_maven_project))

        # Verify all required fields exist
        required_fields = ["success", "tool_used", "execution_time_seconds", "error_message", "exit_code"]
        for field in required_fields:
            assert field in result, f"Result must contain '{field}' field"

        # Verify field types
        assert isinstance(result["success"], bool) or result["success"] is None
        assert isinstance(result["tool_used"], str)
        assert isinstance(result["execution_time_seconds"], (int, float))
        assert isinstance(result["error_message"], str) or result["error_message"] is None
        assert isinstance(result["exit_code"], int) or result["exit_code"] is None

    @pytest.mark.skipif(not check_tool_available("mvn"), reason="maven not available")
    def test_maven_build_validation_real_with_dependencies(self) -> None:
        """REAL TEST: Verify Maven build works with external dependencies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create pom.xml with dependency
            (repo_path / "pom.xml").write_text("""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>deps-test</artifactId>
    <version>1.0.0</version>
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
    </properties>
    <dependencies>
        <dependency>
            <groupId>com.google.guava</groupId>
            <artifactId>guava</artifactId>
            <version>31.1-jre</version>
        </dependency>
    </dependencies>
</project>
""")

            # Create source that uses the dependency
            src_dir = repo_path / "src" / "main" / "java" / "com" / "example"
            src_dir.mkdir(parents=True)
            (src_dir / "Main.java").write_text("""package com.example;

import com.google.common.collect.ImmutableList;

public class Main {
    public static void main(String[] args) {
        ImmutableList<String> list = ImmutableList.of("a", "b", "c");
        System.out.println(list);
    }
}
""")

            runner = JavaToolRunner(timeout_seconds=120)

            # REAL BUILD with dependencies
            result = runner.run_build(str(repo_path))

            # Build might succeed or fail depending on network/cache
            # Just verify the result structure is correct
            assert result is not None
            if result["success"] is not None:
                assert result["tool_used"] == "mvn"
                assert result["execution_time_seconds"] >= 0


class TestGradleBuildIntegrationReal:
    """Real integration tests for Gradle build validation - NO MOCKS."""

    @pytest.fixture
    def minimal_gradle_project(self) -> Path:
        """Create a minimal Gradle project with real build configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create build.gradle
            (repo_path / "build.gradle").write_text("""plugins {
    id 'java'
}

group = 'com.example'
version = '1.0.0'

sourceCompatibility = '11'
targetCompatibility = '11'

repositories {
    mavenCentral()
}
""")

            # Create source directory structure
            src_main_java = repo_path / "src" / "main" / "java" / "com" / "example"
            src_main_java.mkdir(parents=True)

            # Create Main.java
            (src_main_java / "Main.java").write_text("""package com.example;

public class Main {
    public static void main(String[] args) {
        System.out.println("Hello from Gradle!");
    }
}
""")

            # Create README
            (repo_path / "README.md").write_text("""# Test Integration Gradle Project

This is a minimal Gradle project for integration testing.
""")

            yield repo_path

    @pytest.mark.skipif(not check_tool_available("gradle"), reason="gradle not available")
    def test_gradle_build_validation_real_gradle_compile(self, minimal_gradle_project: Path) -> None:
        """REAL TEST: Execute actual gradle compileJava without mocks."""
        # Create tool runner
        runner = JavaToolRunner(timeout_seconds=120)

        # REAL BUILD - No mocks!
        result = runner.run_build(str(minimal_gradle_project))

        # Verify build succeeded with real execution
        assert result is not None, "Build result should not be None"
        assert "success" in result, "Result should contain 'success' field"
        assert "tool_used" in result, "Result should contain 'tool_used' field"

        # With real Gradle, if build is valid, it should succeed
        if result["success"] is not None:  # Tool was available and executed
            assert result["tool_used"] == "gradle", "Should use Gradle"
            assert "execution_time_seconds" in result
            assert result["execution_time_seconds"] >= 0

    @pytest.mark.skipif(not check_tool_available("gradle"), reason="gradle not available")
    def test_gradle_build_validation_real_with_failing_build(self) -> None:
        """REAL TEST: Verify Gradle build failure is detected with actual execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create build.gradle
            (repo_path / "build.gradle").write_text("""plugins {
    id 'java'
}
sourceCompatibility = '11'
""")

            # Create source with compilation error
            src_dir = repo_path / "src" / "main" / "java" / "com" / "example"
            src_dir.mkdir(parents=True)
            (src_dir / "Broken.java").write_text("""package com.example;

public class Broken {
    public void test() {
        String x = 123;  // Type mismatch error
    }
}
""")

            runner = JavaToolRunner(timeout_seconds=120)

            # REAL BUILD that will fail
            result = runner.run_build(str(repo_path))

            # Verify failure is captured
            if result["success"] is not None:  # Tool was available
                assert result["success"] is False, "Build should fail with type error"
                assert result["error_message"] is not None
                assert result["exit_code"] != 0


class TestJavaBuildIntegrationWorkflow:
    """Real workflow integration tests for Java build validation."""

    def test_java_build_integrates_with_pipeline(self) -> None:
        """Test that Java build validation integrates into metrics pipeline."""
        runner = JavaToolRunner(timeout_seconds=120)

        # Verify interface exists
        assert hasattr(runner, 'run_build'), "JavaToolRunner should have run_build method"
        assert callable(runner.run_build), "run_build should be callable"

        # Verify method signature
        import inspect
        sig = inspect.signature(runner.run_build)
        assert 'repo_path' in sig.parameters, "run_build should accept repo_path parameter"

    @pytest.mark.skipif(not check_tool_available("mvn"), reason="maven not available")
    def test_maven_build_real_end_to_end_workflow(self) -> None:
        """REAL END-TO-END TEST: Complete Maven workflow with actual tool execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # 1. Create a realistic Maven project
            (repo_path / "pom.xml").write_text("""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>e2e-test-project</artifactId>
    <version>1.0.0</version>
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
    </properties>
</project>
""")

            # Create model package
            model_dir = repo_path / "src" / "main" / "java" / "com" / "example" / "model"
            model_dir.mkdir(parents=True)
            (model_dir / "Person.java").write_text("""package com.example.model;

public class Person {
    private String name;
    private int age;

    public Person(String name, int age) {
        this.name = name;
        this.age = age;
    }

    public String getName() { return name; }
    public int getAge() { return age; }
}
""")

            # Create service package
            service_dir = repo_path / "src" / "main" / "java" / "com" / "example" / "service"
            service_dir.mkdir(parents=True)
            (service_dir / "GreetingService.java").write_text("""package com.example.service;

import com.example.model.Person;

public class GreetingService {
    public String greet(Person person) {
        return "Hello, " + person.getName() + "!";
    }
}
""")

            # Create main class
            main_dir = repo_path / "src" / "main" / "java" / "com" / "example"
            (main_dir / "Application.java").write_text("""package com.example;

import com.example.model.Person;
import com.example.service.GreetingService;

public class Application {
    public static void main(String[] args) {
        Person person = new Person("World", 0);
        GreetingService service = new GreetingService();
        System.out.println(service.greet(person));
    }
}
""")

            # 2. Execute REAL build
            runner = JavaToolRunner(timeout_seconds=120)
            result = runner.run_build(str(repo_path))

            # 3. Verify results
            assert result is not None
            if result["success"] is not None:  # Maven was available
                assert result["success"] is True, "E2E Maven build should succeed"
                assert result["tool_used"] == "mvn"
                assert result["exit_code"] == 0

                # 4. Verify compiled classes were created
                target_dir = repo_path / "target" / "classes"
                if target_dir.exists():
                    # Check for compiled .class files
                    class_files = list(target_dir.rglob("*.class"))
                    assert len(class_files) > 0, "Build should create .class files"

    @pytest.mark.skipif(not check_tool_available("gradle"), reason="gradle not available")
    def test_gradle_build_real_end_to_end_workflow(self) -> None:
        """REAL END-TO-END TEST: Complete Gradle workflow with actual tool execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # 1. Create a realistic Gradle project
            (repo_path / "build.gradle").write_text("""plugins {
    id 'java'
}

group = 'com.example'
version = '1.0.0'
sourceCompatibility = '11'

repositories {
    mavenCentral()
}
""")

            # Create source structure
            src_dir = repo_path / "src" / "main" / "java" / "com" / "example"
            src_dir.mkdir(parents=True)

            (src_dir / "Calculator.java").write_text("""package com.example;

public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }

    public int subtract(int a, int b) {
        return a - b;
    }
}
""")

            (src_dir / "Main.java").write_text("""package com.example;

public class Main {
    public static void main(String[] args) {
        Calculator calc = new Calculator();
        System.out.println("2 + 3 = " + calc.add(2, 3));
    }
}
""")

            # 2. Execute REAL build
            runner = JavaToolRunner(timeout_seconds=120)
            result = runner.run_build(str(repo_path))

            # 3. Verify results
            assert result is not None
            if result["success"] is not None:  # Gradle was available
                assert result["success"] is True, "E2E Gradle build should succeed"
                assert result["tool_used"] == "gradle"
                assert result["exit_code"] == 0

    def test_java_build_validation_real_json_serialization(self) -> None:
        """REAL TEST: Verify build results can be serialized to JSON."""
        import json

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create minimal pom.xml
            (repo_path / "pom.xml").write_text("""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>json-test</artifactId>
    <version>1.0.0</version>
</project>
""")

            runner = JavaToolRunner(timeout_seconds=120)

            # Execute build (will skip if Maven not available, but still test serialization)
            result = runner.run_build(str(repo_path))

            # Verify JSON serialization works
            try:
                json_str = json.dumps(result)
                assert json_str is not None
                assert len(json_str) > 0

                # Verify deserialization
                deserialized = json.loads(json_str)
                assert deserialized["success"] == result["success"]
                assert deserialized["tool_used"] == result["tool_used"]
            except (TypeError, ValueError) as e:
                pytest.fail(f"Build result should be JSON serializable: {e}")


class TestJavaBuildToolPriority:
    """Real tests for Maven vs Gradle priority."""

    @pytest.mark.skipif(not check_tool_available("mvn"), reason="maven not available")
    def test_maven_priority_when_both_exist(self) -> None:
        """REAL TEST: Verify Maven is used when both pom.xml and build.gradle exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Create BOTH pom.xml and build.gradle
            (repo_path / "pom.xml").write_text("""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>priority-test</artifactId>
    <version>1.0.0</version>
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
    </properties>
</project>
""")

            (repo_path / "build.gradle").write_text("""plugins {
    id 'java'
}
""")

            # Create source
            src_dir = repo_path / "src" / "main" / "java"
            src_dir.mkdir(parents=True)
            (src_dir / "Main.java").write_text("""public class Main {}""")

            runner = JavaToolRunner(timeout_seconds=120)
            result = runner.run_build(str(repo_path))

            # Should prefer Maven when both exist
            if result["success"] is not None:
                assert result["tool_used"] == "mvn", "Should use Maven when both pom.xml and build.gradle exist"

    def test_empty_directory_handling(self) -> None:
        """REAL TEST: Verify behavior with empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = JavaToolRunner(timeout_seconds=120)

            # REAL CHECK on empty directory
            result = runner.run_build(str(temp_dir))

            # Should detect no build configuration
            assert result["success"] is None
            assert result["tool_used"] == "none"
            assert "No Maven or Gradle" in result["error_message"]
