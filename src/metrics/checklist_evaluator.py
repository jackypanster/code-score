"""ChecklistEvaluator class for processing submission.json against checklist."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .models.checklist_item import ChecklistItem
from .models.evaluation_result import EvaluationMetadata, EvaluationResult, RepositoryInfo
from .models.evidence_reference import EvidenceReference


class ChecklistEvaluator:
    """Core evaluation logic that processes submission.json against checklist."""

    def __init__(self, checklist_config_path: str | None = None):
        """Initialize evaluator with checklist configuration."""
        if checklist_config_path is None:
            # Default to the checklist mapping in the contracts directory
            base_path = Path(__file__).parent.parent.parent / "specs" / "contracts"
            checklist_config_path = str(base_path / "checklist_mapping.yaml")

        self.checklist_config_path = checklist_config_path
        self.checklist_config = self._load_checklist_config()
        self.evaluator_version = "1.0.0"

    def _load_checklist_config(self) -> dict[str, Any]:
        """Load checklist configuration from YAML file."""
        try:
            with open(self.checklist_config_path) as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Checklist configuration not found at {self.checklist_config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in checklist configuration: {e}")

    def _extract_value_from_path(self, data: dict[str, Any], json_path: str) -> Any:
        """Extract value from JSON data using JSONPath-like syntax."""
        # Simple JSONPath implementation for our needs
        # Supports paths like "$.metrics.code_quality.lint_results.passed"
        path_parts = json_path.replace("$.", "").split(".")

        current = data
        for part in path_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def _evaluate_criteria(self, criteria: dict[str, list[str]], submission_data: dict[str, Any], metrics_mapping: dict[str, Any]) -> tuple[str, float, list[EvidenceReference]]:
        """Evaluate criteria against submission data and return status, confidence, and evidence."""
        evidence_refs = []

        # Check 'met' criteria first
        if self._check_criteria_group(criteria.get("met", []), submission_data, evidence_refs, metrics_mapping):
            return "met", 0.95, evidence_refs

        # Check 'partial' criteria
        if self._check_criteria_group(criteria.get("partial", []), submission_data, evidence_refs, metrics_mapping):
            return "partial", 0.8, evidence_refs

        # Default to 'unmet'
        self._add_unmet_evidence(criteria, submission_data, evidence_refs)
        return "unmet", 0.9, evidence_refs

    def _check_criteria_group(self, criteria_list: list[str], submission_data: dict[str, Any], evidence_refs: list[EvidenceReference], metrics_mapping: dict[str, Any]) -> bool:
        """Check if all criteria in a group are satisfied."""
        if not criteria_list:
            return False

        for criterion in criteria_list:
            if not self._evaluate_single_criterion(criterion, submission_data, evidence_refs, metrics_mapping):
                return False

        return True

    def _build_field_path(self, left_field: str, base_path: str) -> str:
        """Build the correct JSON path for a field, avoiding duplication."""
        # Handle special cases for non-metrics paths
        if left_field in ["errors", "warnings"]:
            return f"$.execution.{left_field}"

        # Handle execution.* fields directly
        if left_field.startswith("execution."):
            return f"$.{left_field}"

        # Check if base_path already points to the leaf value (no field name needed)
        # This happens when source_path is like "$.metrics.code_quality.build_success"
        # and the field being checked is just "build_success"
        if base_path.endswith(f".{left_field}"):
            return base_path

        # If the field already contains a dotted path that overlaps with base_path,
        # we need to be smart about combining them
        if "." in left_field:
            # Split the field into parts
            field_parts = left_field.split(".")

            # Extract the relevant part of base_path after "$.metrics"
            if base_path.startswith("$.metrics."):
                base_parts = base_path[10:].split(".")  # Remove "$.metrics." prefix
            else:
                base_parts = base_path.split(".")

            # Check if the first part of field overlaps with the last part of base
            # e.g., base="$.metrics.code_quality.lint_results", field="lint_results.tool_used"
            if field_parts[0] in base_parts:
                # Find where the overlap starts and avoid duplication
                try:
                    overlap_index = base_parts.index(field_parts[0])
                    # Use base path up to overlap, then add the remaining field parts
                    if overlap_index < len(base_parts) - 1:
                        # There are parts after the overlap in base_path
                        remaining_base = ".".join(base_parts[:overlap_index + 1])
                        remaining_field = ".".join(field_parts[1:])
                        return f"$.metrics.{remaining_base}.{remaining_field}" if remaining_field else f"$.metrics.{remaining_base}"
                    else:
                        # The overlap is at the end of base_path
                        remaining_field = ".".join(field_parts[1:])
                        return f"{base_path}.{remaining_field}" if remaining_field else base_path
                except ValueError:
                    # No overlap found, proceed with normal concatenation
                    pass

        # Default behavior: simple concatenation
        if base_path.startswith("$."):
            return f"{base_path}.{left_field}"
        else:
            return f"$.{base_path}.{left_field}"

    def _preprocess_criterion(self, criterion: str) -> str:
        """Preprocess criterion to handle complex expressions."""
        # Convert "BUT" to "AND" for proper logical evaluation
        # "A BUT B" means "A AND B" - both conditions must be true
        if " BUT " in criterion:
            criterion = criterion.replace(" BUT ", " AND ")

        # Do NOT remove parentheses - they're critical for logical precedence
        return criterion.strip()

    def _evaluate_logical_expression(self, expression: str, submission_data: dict[str, Any], evidence_refs: list[EvidenceReference], metrics_mapping: dict[str, Any]) -> bool:
        """Evaluate logical expression with proper parentheses and operator precedence."""
        expression = expression.strip()

        # Handle parentheses first (highest precedence)
        while "(" in expression:
            # Find the innermost parentheses
            start = -1
            for i, char in enumerate(expression):
                if char == "(":
                    start = i
                elif char == ")" and start != -1:
                    # Found matching closing parenthesis
                    inner_expr = expression[start + 1:i]
                    inner_result = self._evaluate_logical_expression(inner_expr, submission_data, evidence_refs, metrics_mapping)

                    # Replace the parenthetical expression with its result
                    expression = expression[:start] + str(inner_result) + expression[i + 1:]
                    break
            else:
                # No matching closing parenthesis found
                break

        # Now handle OR (lowest precedence) - split on OR first
        if " OR " in expression:
            parts = expression.split(" OR ")
            results = []
            for part in parts:
                part = part.strip()
                if part.lower() == "true":
                    results.append(True)
                elif part.lower() == "false":
                    results.append(False)
                else:
                    results.append(self._evaluate_logical_expression(part, submission_data, evidence_refs, metrics_mapping))
            return any(results)

        # Then handle AND (higher precedence than OR)
        if " AND " in expression:
            parts = expression.split(" AND ")
            results = []
            for part in parts:
                part = part.strip()
                if part.lower() == "true":
                    results.append(True)
                elif part.lower() == "false":
                    results.append(False)
                else:
                    results.append(self._evaluate_single_criterion(part, submission_data, evidence_refs, metrics_mapping))
            return all(results)

        # No logical operators, evaluate as single criterion
        if expression.lower() == "true":
            return True
        elif expression.lower() == "false":
            return False
        else:
            return self._evaluate_single_criterion(expression, submission_data, evidence_refs, metrics_mapping)

    def _handle_length_expression(self, left_field: str, operator: str, expected_value: Any, submission_data: dict[str, Any], base_path: str) -> tuple[bool, str]:
        """Handle expressions with .length by checking list/array length."""
        # Extract the field without .length
        actual_field = left_field.replace(".length", "")

        # Build path for the actual array/list
        full_path = self._build_field_path(actual_field, base_path)
        actual_value = self._extract_value_from_path(submission_data, full_path)

        # Check if it's a list and get its length
        if isinstance(actual_value, list):
            length = len(actual_value)
        elif actual_value is None:
            length = 0
        else:
            # Not a list, treat as 1 if exists, 0 if not
            length = 1 if actual_value else 0

        # Perform the comparison
        try:
            expected_num = float(expected_value)
            if operator == "==":
                result = length == expected_num
            elif operator == "!=":
                result = length != expected_num
            elif operator == ">=":
                result = length >= expected_num
            elif operator == ">":
                result = length > expected_num
            elif operator == "<=":
                result = length <= expected_num
            elif operator == "<":
                result = length < expected_num
            else:
                result = False

            description = f"Checked {actual_field}.length: expected {operator} {expected_value}, got {length}"
            return result, description
        except (ValueError, TypeError):
            return False, f"Invalid length comparison: {left_field} {operator} {expected_value}"

    def _evaluate_single_criterion(self, criterion: str, submission_data: dict[str, Any], evidence_refs: list[EvidenceReference], metrics_mapping: dict[str, Any]) -> bool:
        """Evaluate a single criterion expression."""
        # Get base path from metrics mapping
        base_path = metrics_mapping.get("source_path", "$.metrics")

        # Handle complex expressions with BUT, parentheses, etc.
        criterion = self._preprocess_criterion(criterion)

        # Handle logical expressions with proper precedence and parentheses
        if " OR " in criterion or " AND " in criterion or "(" in criterion:
            return self._evaluate_logical_expression(criterion, submission_data, evidence_refs, metrics_mapping)

        # Now check for arithmetic/comparison operators
        if " == " in criterion:
            left, right = criterion.split(" == ", 1)
            left_field = left.strip()
            expected_value = self._parse_expected_value(right.strip())

            # Handle .length expressions specially
            if ".length" in left_field:
                result, description = self._handle_length_expression(left_field, "==", expected_value, submission_data, base_path)
                full_path = self._build_field_path(left_field.replace(".length", ""), base_path)
            else:
                # Build full path using smart path building
                full_path = self._build_field_path(left_field, base_path)
                actual_value = self._extract_value_from_path(submission_data, full_path)
                result = actual_value == expected_value
                description = f"Checked {left_field}: expected {expected_value}, got {actual_value}"

            # Add evidence
            evidence_refs.append(EvidenceReference(
                source_type="file_check",
                source_path=full_path,
                description=description,
                confidence=0.95 if result else 0.85,
                raw_data=str(self._extract_value_from_path(submission_data, full_path)) if ".length" not in left_field else f"length={len(self._extract_value_from_path(submission_data, full_path)) if isinstance(self._extract_value_from_path(submission_data, full_path), list) else 0}"
            ))

            return result

        elif " != " in criterion:
            left, right = criterion.split(" != ", 1)
            left_field = left.strip()
            expected_value = self._parse_expected_value(right.strip())

            # Handle .length expressions specially
            if ".length" in left_field:
                result, description = self._handle_length_expression(left_field, "!=", expected_value, submission_data, base_path)
                full_path = self._build_field_path(left_field.replace(".length", ""), base_path)
            else:
                full_path = self._build_field_path(left_field, base_path)
                actual_value = self._extract_value_from_path(submission_data, full_path)
                result = actual_value != expected_value
                description = f"Checked {left_field}: should not be {expected_value}, got {actual_value}"

            evidence_refs.append(EvidenceReference(
                source_type="file_check",
                source_path=full_path,
                description=description,
                confidence=0.95 if result else 0.85,
                raw_data=str(self._extract_value_from_path(submission_data, full_path)) if ".length" not in left_field else f"length={len(self._extract_value_from_path(submission_data, full_path)) if isinstance(self._extract_value_from_path(submission_data, full_path), list) else 0}"
            ))

            return result

        elif " >= " in criterion:
            left, right = criterion.split(" >= ", 1)
            left_field = left.strip()
            expected_value = self._parse_expected_value(right.strip())

            # Handle .length expressions specially
            if ".length" in left_field:
                result, description = self._handle_length_expression(left_field, ">=", expected_value, submission_data, base_path)
                full_path = self._build_field_path(left_field.replace(".length", ""), base_path)
                evidence_refs.append(EvidenceReference(
                    source_type="file_check",
                    source_path=full_path,
                    description=description,
                    confidence=0.95 if result else 0.85,
                    raw_data=f"length={len(self._extract_value_from_path(submission_data, full_path)) if isinstance(self._extract_value_from_path(submission_data, full_path), list) else 0}"
                ))
                return result

            full_path = self._build_field_path(left_field, base_path)
            actual_value = self._extract_value_from_path(submission_data, full_path)

            if actual_value is None or expected_value is None:
                return False

            try:
                result = float(actual_value) >= float(expected_value)
                evidence_refs.append(EvidenceReference(
                    source_type="file_check",
                    source_path=full_path,
                    description=f"Checked {left_field}: expected >= {expected_value}, got {actual_value}",
                    confidence=0.95 if result else 0.85,
                    raw_data=str(actual_value)
                ))
                return result
            except (ValueError, TypeError):
                return False

        elif " > " in criterion:
            left, right = criterion.split(" > ", 1)
            left_field = left.strip()
            expected_value = self._parse_expected_value(right.strip())

            # Handle .length expressions specially
            if ".length" in left_field:
                result, description = self._handle_length_expression(left_field, ">", expected_value, submission_data, base_path)
                full_path = self._build_field_path(left_field.replace(".length", ""), base_path)
                evidence_refs.append(EvidenceReference(
                    source_type="file_check",
                    source_path=full_path,
                    description=description,
                    confidence=0.95 if result else 0.85,
                    raw_data=f"length={len(self._extract_value_from_path(submission_data, full_path)) if isinstance(self._extract_value_from_path(submission_data, full_path), list) else 0}"
                ))
                return result

            full_path = self._build_field_path(left_field, base_path)
            actual_value = self._extract_value_from_path(submission_data, full_path)

            if actual_value is None or expected_value is None:
                return False

            try:
                result = float(actual_value) > float(expected_value)
                evidence_refs.append(EvidenceReference(
                    source_type="file_check",
                    source_path=full_path,
                    description=f"Checked {left_field}: expected > {expected_value}, got {actual_value}",
                    confidence=0.95 if result else 0.85,
                    raw_data=str(actual_value)
                ))
                return result
            except (ValueError, TypeError):
                return False

        # If no operators found, treat as existence check
        if base_path.startswith("$."):
            full_path = f"{base_path}.{criterion.strip()}"
        else:
            full_path = f"$.{base_path}.{criterion.strip()}"

        actual_value = self._extract_value_from_path(submission_data, full_path)
        result = actual_value is not None

        evidence_refs.append(EvidenceReference(
            source_type="file_check",
            source_path=full_path,
            description=f"Checked existence of {criterion.strip()}",
            confidence=0.9,
            raw_data=str(actual_value) if actual_value is not None else "null"
        ))

        return result

    def _parse_expected_value(self, value_str: str) -> Any:
        """Parse expected value from string."""
        import json

        value_str = value_str.strip()

        if value_str.lower() == "true":
            return True
        elif value_str.lower() == "false":
            return False
        elif value_str.lower() == "null":
            return None
        elif value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]  # Remove quotes
        elif value_str.startswith('[') and value_str.endswith(']'):
            # Handle array literals like [], [1, 2, 3], ["a", "b"]
            try:
                return json.loads(value_str)
            except json.JSONDecodeError:
                # Fallback to string if not valid JSON
                return value_str
        elif value_str.startswith('{') and value_str.endswith('}'):
            # Handle object literals like {}, {"key": "value"}
            try:
                return json.loads(value_str)
            except json.JSONDecodeError:
                # Fallback to string if not valid JSON
                return value_str
        elif value_str.isdigit():
            return int(value_str)
        else:
            try:
                return float(value_str)
            except ValueError:
                return value_str

    def _add_unmet_evidence(self, criteria: dict[str, list[str]], submission_data: dict[str, Any], evidence_refs: list[EvidenceReference]) -> None:
        """Add evidence explaining why criteria were not met."""
        evidence_refs.append(EvidenceReference(
            source_type="file_check",
            source_path="$.metrics",
            description="Criteria not satisfied for 'met' or 'partial' status",
            confidence=0.8,
            raw_data="Evaluation criteria failed"
        ))

    def _create_checklist_item(self, item_config: dict[str, Any], submission_data: dict[str, Any]) -> ChecklistItem:
        """Create a ChecklistItem from configuration and evaluation."""
        start_time = datetime.now()

        # Evaluate criteria
        evaluation_status, confidence, evidence_refs = self._evaluate_criteria(
            item_config["evaluation_criteria"],
            submission_data,
            item_config.get("metrics_mapping", {})
        )

        # Create checklist item
        item = ChecklistItem(
            id=item_config["id"],
            name=item_config["name"],
            dimension=item_config["dimension"],
            max_points=item_config["max_points"],
            description=item_config["description"],
            evaluation_status=evaluation_status,
            evidence_references=evidence_refs
        )

        # Calculate score based on status
        item.score = item.calculate_score_from_status()

        return item

    def _create_repository_info(self, submission_data: dict[str, Any], submission_path: str) -> RepositoryInfo:
        """Create RepositoryInfo from submission data."""
        repo_data = submission_data.get("repository", {})

        return RepositoryInfo(
            url=repo_data.get("url", "unknown"),
            commit_sha=repo_data.get("commit", "unknown"),
            primary_language=repo_data.get("language", "unknown"),
            analysis_timestamp=datetime.fromisoformat(repo_data.get("timestamp", datetime.now().isoformat()).replace('Z', '+00:00')),
            metrics_source=submission_path
        )

    def _create_evaluation_metadata(self, start_time: datetime, warnings: list[str], submission_data: dict[str, Any]) -> EvaluationMetadata:
        """Create EvaluationMetadata from evaluation process."""
        processing_duration = (datetime.now() - start_time).total_seconds()

        # Calculate metrics completeness
        metrics_completeness = self._calculate_metrics_completeness(submission_data)

        return EvaluationMetadata(
            evaluator_version=self.evaluator_version,
            processing_duration=processing_duration,
            warnings=warnings,
            metrics_completeness=metrics_completeness
        )

    def _calculate_metrics_completeness(self, submission_data: dict[str, Any]) -> float:
        """Calculate what percentage of expected metrics are present."""
        expected_sections = ["code_quality", "testing", "documentation"]
        present_sections = 0

        metrics = submission_data.get("metrics", {})
        for section in expected_sections:
            if section in metrics and metrics[section]:
                present_sections += 1

        return (present_sections / len(expected_sections)) * 100.0

    def evaluate_from_file(self, submission_path: str) -> EvaluationResult:
        """Evaluate checklist from submission.json file."""
        try:
            with open(submission_path) as f:
                submission_data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Submission file not found: {submission_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in submission file: {e}")

        return self.evaluate_from_dict(submission_data, submission_path)

    def evaluate_from_string(self, submission_json: str) -> EvaluationResult:
        """Evaluate checklist from JSON string."""
        try:
            submission_data = json.loads(submission_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {e}")

        return self.evaluate_from_dict(submission_data, "<string>")

    def evaluate_from_dict(self, submission_data: dict[str, Any], submission_path: str = "<dict>") -> EvaluationResult:
        """Evaluate checklist from submission data dictionary."""
        start_time = datetime.now()
        warnings = []

        # Validate basic structure
        if "metrics" not in submission_data:
            warnings.append("No 'metrics' section found in submission data")
            submission_data["metrics"] = {}

        if "repository" not in submission_data:
            warnings.append("No 'repository' section found in submission data")
            submission_data["repository"] = {}

        # Create checklist items
        checklist_items = []
        for item_config in self.checklist_config["checklist_items"]:
            try:
                item = self._create_checklist_item(item_config, submission_data)
                checklist_items.append(item)
            except Exception as e:
                warnings.append(f"Error evaluating {item_config['id']}: {str(e)}")
                # Create unmet item as fallback
                item = ChecklistItem(
                    id=item_config["id"],
                    name=item_config["name"],
                    dimension=item_config["dimension"],
                    max_points=item_config["max_points"],
                    description=item_config["description"],
                    evaluation_status="unmet"
                )
                item.score = 0.0
                checklist_items.append(item)

        # Create repository info
        repository_info = self._create_repository_info(submission_data, submission_path)

        # Create evaluation metadata
        evaluation_metadata = self._create_evaluation_metadata(start_time, warnings, submission_data)

        # Calculate totals
        total_score = sum(item.score for item in checklist_items)
        score_percentage = (total_score / 100.0) * 100.0 if total_score > 0 else 0.0

        # Calculate category breakdowns
        from .models.category_breakdown import CategoryBreakdown
        category_breakdowns = {}
        for dimension in ["code_quality", "testing", "documentation"]:
            items = [item for item in checklist_items if item.dimension == dimension]

            max_points = sum(item.max_points for item in items) if items else 0
            actual_points = sum(item.score for item in items) if items else 0.0
            percentage = (actual_points / max_points * 100.0) if max_points > 0 else 0.0

            category_breakdowns[dimension] = CategoryBreakdown(
                dimension=dimension,
                items_count=len(items),
                max_points=max_points,
                actual_points=actual_points,
                percentage=percentage
            )

        # Create evaluation result
        evaluation_result = EvaluationResult(
            checklist_items=checklist_items,
            total_score=total_score,
            max_possible_score=100,
            score_percentage=score_percentage,
            category_breakdowns=category_breakdowns,
            evaluation_metadata=evaluation_metadata,
            evidence_summary=self._generate_evidence_summary(checklist_items)
        )

        return evaluation_result

    def _generate_evidence_summary(self, checklist_items: list[ChecklistItem]) -> list[str]:
        """Generate summary of key evidence points."""
        summary = []

        for item in checklist_items:
            if item.evaluation_status == "met":
                summary.append(f"✅ {item.name}: {item.description}")
            elif item.evaluation_status == "partial":
                summary.append(f"⚠️ {item.name}: Partially satisfied - {item.description}")
            elif item.evaluation_status == "unmet":
                summary.append(f"❌ {item.name}: Not satisfied - {item.description}")

        return summary
