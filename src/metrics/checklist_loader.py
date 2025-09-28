"""ChecklistLoader utility for loading and managing checklist configurations."""

from pathlib import Path
from typing import Any

import yaml

from .models.checklist_item import ChecklistItem


class ChecklistLoader:
    """Utility for loading checklist configurations and language adaptations."""

    def __init__(self, config_path: str | None = None):
        """Initialize loader with checklist configuration path."""
        if config_path is None:
            # Default to the checklist mapping in the contracts directory
            base_path = Path(__file__).parent.parent.parent / "specs" / "contracts"
            config_path = str(base_path / "checklist_mapping.yaml")

        self.config_path = config_path
        self.config_data = self._load_config()
        self.checklist_items_config = self.config_data.get("checklist_items", [])
        self.language_adaptations = self.config_data.get("language_adaptations", {})

    def _load_config(self) -> dict[str, Any]:
        """Load checklist configuration from YAML file."""
        try:
            with open(self.config_path, encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Checklist configuration not found at {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in checklist configuration: {e}")

    def get_checklist_items_config(self) -> list[dict[str, Any]]:
        """Get list of checklist item configurations."""
        return self.checklist_items_config

    def get_checklist_item_config(self, item_id: str) -> dict[str, Any] | None:
        """Get configuration for a specific checklist item."""
        for item_config in self.checklist_items_config:
            if item_config.get("id") == item_id:
                return item_config
        return None

    def get_items_by_dimension(self, dimension: str) -> list[dict[str, Any]]:
        """Get all checklist items for a specific dimension."""
        return [
            item for item in self.checklist_items_config
            if item.get("dimension") == dimension
        ]

    def get_language_adaptations(self, language: str) -> dict[str, Any] | None:
        """Get language-specific adaptations."""
        return self.language_adaptations.get(language.lower())

    def get_language_criteria(self, language: str) -> dict[str, Any]:
        """Get language-specific evaluation criteria."""
        adaptations = self.get_language_adaptations(language)
        if not adaptations:
            # Return default criteria if no language-specific adaptations
            return {}

        return adaptations

    def get_adapted_tool_mapping(self, language: str, item_id: str) -> dict[str, Any] | None:
        """Get language-specific tool mapping for a checklist item."""
        adaptations = self.get_language_adaptations(language)
        if not adaptations or item_id not in adaptations:
            return None

        return adaptations[item_id]

    def validate_checklist_config(self) -> dict[str, Any]:
        """Validate the loaded checklist configuration."""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }

        # Required fields for checklist items
        required_item_fields = ["id", "name", "dimension", "max_points", "description", "evaluation_criteria"]

        # Validate each checklist item
        item_ids = set()
        total_max_points = 0
        dimension_counts = {"code_quality": 0, "testing": 0, "documentation": 0}

        for i, item in enumerate(self.checklist_items_config):
            # Check required fields
            for field in required_item_fields:
                if field not in item:
                    validation_results["errors"].append(
                        f"Missing required field '{field}' in checklist_items[{i}]"
                    )
                    validation_results["valid"] = False

            # Check unique IDs
            item_id = item.get("id")
            if item_id:
                if item_id in item_ids:
                    validation_results["errors"].append(f"Duplicate item ID: {item_id}")
                    validation_results["valid"] = False
                item_ids.add(item_id)

            # Validate dimension
            dimension = item.get("dimension")
            if dimension not in ["code_quality", "testing", "documentation"]:
                validation_results["errors"].append(
                    f"Invalid dimension '{dimension}' in item {item_id}"
                )
                validation_results["valid"] = False
            else:
                dimension_counts[dimension] += 1

            # Validate max_points
            max_points = item.get("max_points")
            if isinstance(max_points, int) and max_points > 0:
                total_max_points += max_points
            else:
                validation_results["errors"].append(
                    f"Invalid max_points '{max_points}' in item {item_id}"
                )
                validation_results["valid"] = False

            # Validate evaluation criteria structure
            criteria = item.get("evaluation_criteria", {})
            if not isinstance(criteria, dict):
                validation_results["errors"].append(
                    f"evaluation_criteria must be a dict in item {item_id}"
                )
                validation_results["valid"] = False
            else:
                for status in ["met", "partial", "unmet"]:
                    if status not in criteria:
                        validation_results["warnings"].append(
                            f"Missing '{status}' criteria in item {item_id}"
                        )

        # Check total points
        if total_max_points != 100:
            validation_results["warnings"].append(
                f"Total max_points is {total_max_points}, expected 100"
            )

        # Check item count
        total_items = len(self.checklist_items_config)
        if total_items != 11:
            validation_results["warnings"].append(
                f"Expected 11 checklist items, found {total_items}"
            )

        # Validate language adaptations
        for language, adaptations in self.language_adaptations.items():
            if not isinstance(adaptations, dict):
                validation_results["errors"].append(
                    f"Language adaptations for '{language}' must be a dict"
                )
                validation_results["valid"] = False

        # Generate statistics
        validation_results["statistics"] = {
            "total_checklist_items": total_items,
            "total_max_points": total_max_points,
            "dimension_distribution": dimension_counts,
            "supported_languages": list(self.language_adaptations.keys()),
            "unique_item_ids": len(item_ids)
        }

        return validation_results

    def create_template_checklist_items(self) -> list[ChecklistItem]:
        """Create template ChecklistItem objects from configuration."""
        template_items = []

        for item_config in self.checklist_items_config:
            try:
                template_item = ChecklistItem(
                    id=item_config["id"],
                    name=item_config["name"],
                    dimension=item_config["dimension"],
                    max_points=item_config["max_points"],
                    description=item_config["description"],
                    evaluation_status="unmet",  # Default status
                    score=0.0,  # Default score
                    evidence_references=[]  # Empty evidence list
                )
                template_items.append(template_item)

            except Exception as e:
                raise ValueError(f"Error creating template for item {item_config.get('id', 'unknown')}: {e}")

        return template_items

    def get_dimension_summary(self) -> dict[str, dict[str, Any]]:
        """Get summary of checklist dimensions."""
        dimension_summary = {}

        for dimension in ["code_quality", "testing", "documentation"]:
            items = self.get_items_by_dimension(dimension)
            total_points = sum(item["max_points"] for item in items)

            dimension_summary[dimension] = {
                "items_count": len(items),
                "total_max_points": total_points,
                "item_ids": [item["id"] for item in items],
                "item_names": [item["name"] for item in items]
            }

        return dimension_summary

    def export_checklist_documentation(self, output_path: str) -> str:
        """Export checklist documentation in markdown format."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        dimension_summary = self.get_dimension_summary()

        lines = [
            "# Checklist Evaluation Documentation",
            "",
            "This document describes the 11-item quality checklist used for repository evaluation.",
            "",
            "## Overview",
            "",
            f"- **Total Items:** {len(self.checklist_items_config)}",
            f"- **Total Points:** {sum(item['max_points'] for item in self.checklist_items_config)}",
            f"- **Dimensions:** {len(dimension_summary)}",
            "",
            "## Dimension Breakdown",
            ""
        ]

        for dimension, summary in dimension_summary.items():
            lines.extend([
                f"### {dimension.replace('_', ' ').title()}",
                f"- **Items:** {summary['items_count']}",
                f"- **Max Points:** {summary['total_max_points']}",
                f"- **Percentage of Total:** {(summary['total_max_points'] / 100) * 100:.1f}%",
                ""
            ])

        lines.extend([
            "## Detailed Checklist Items",
            ""
        ])

        # Group items by dimension for documentation
        for dimension in ["code_quality", "testing", "documentation"]:
            items = self.get_items_by_dimension(dimension)
            if items:
                lines.extend([
                    f"### {dimension.replace('_', ' ').title()} ({len(items)} items)",
                    ""
                ])

                for item in items:
                    lines.extend([
                        f"#### {item['name']} ({item['max_points']} points)",
                        f"**ID:** `{item['id']}`",
                        f"**Description:** {item['description']}",
                        "",
                        "**Evaluation Criteria:**"
                    ])

                    criteria = item.get("evaluation_criteria", {})
                    for status in ["met", "partial", "unmet"]:
                        if status in criteria:
                            lines.append(f"- **{status.upper()}:**")
                            for criterion in criteria[status]:
                                lines.append(f"  - {criterion}")

                    # Add metrics mapping if available
                    if "metrics_mapping" in item:
                        mapping = item["metrics_mapping"]
                        lines.extend([
                            "",
                            "**Metrics Mapping:**",
                            f"- Source Path: `{mapping.get('source_path', 'N/A')}`",
                            f"- Required Fields: {mapping.get('required_fields', [])}"
                        ])

                    lines.append("")

        # Language adaptations section
        if self.language_adaptations:
            lines.extend([
                "## Language-Specific Adaptations",
                "",
                "The following programming languages have specific adaptations:",
                ""
            ])

            for language, adaptations in self.language_adaptations.items():
                lines.extend([
                    f"### {language.title()}",
                    ""
                ])

                for item_id, adaptation in adaptations.items():
                    if isinstance(adaptation, dict):
                        lines.append(f"#### {item_id}")
                        for key, value in adaptation.items():
                            lines.append(f"- **{key}:** {value}")
                        lines.append("")

        lines.extend([
            "---",
            f"*Documentation generated from {self.config_path}*"
        ])

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        return str(output_file)

    def reload_config(self) -> None:
        """Reload configuration from file."""
        self.config_data = self._load_config()
        self.checklist_items_config = self.config_data.get("checklist_items", [])
        self.language_adaptations = self.config_data.get("language_adaptations", {})
