"""EvidenceTracker class for managing and organizing evaluation evidence."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .models.checklist_item import ChecklistItem
from .models.evaluation_result import EvaluationResult
from .models.evidence_reference import EvidenceReference


class EvidenceTracker:
    """Tracks and organizes evidence collected during evaluation process."""

    def __init__(self, evidence_base_path: str = "evidence"):
        """Initialize evidence tracker with base output path."""
        self.evidence_base_path = Path(evidence_base_path)
        self.evidence_store: dict[str, list[dict[str, Any]]] = {}
        self.file_manifest: dict[str, str] = {}

    def track_evidence(
        self,
        item_id: str,
        evidence: EvidenceReference,
        source_data: dict[str, Any] | None = None
    ) -> str:
        """Track evidence for a checklist item and return evidence key."""
        evidence_key = f"{item_id}_{evidence.source_type}"

        # Store evidence data
        evidence_data = {
            "evidence_key": evidence_key,
            "item_id": item_id,
            "source_type": evidence.source_type,
            "source_path": evidence.source_path,
            "description": evidence.description,
            "confidence": evidence.confidence,
            "raw_data": evidence.raw_data,
            "timestamp": datetime.now().isoformat(),
            "source_data": source_data or {}
        }

        if evidence_key not in self.evidence_store:
            self.evidence_store[evidence_key] = []

        self.evidence_store[evidence_key].append(evidence_data)
        return evidence_key

    def track_checklist_item_evidence(self, checklist_item: ChecklistItem) -> list[str]:
        """Track all evidence for a checklist item."""
        evidence_keys = []

        for evidence in checklist_item.evidence_references:
            evidence_key = self.track_evidence(checklist_item.id, evidence)
            evidence_keys.append(evidence_key)

        return evidence_keys

    def track_evaluation_evidence(self, evaluation_result: EvaluationResult) -> dict[str, list[str]]:
        """Track evidence for entire evaluation result."""
        all_evidence_keys = {}

        for item in evaluation_result.checklist_items:
            evidence_keys = self.track_checklist_item_evidence(item)
            all_evidence_keys[item.id] = evidence_keys

        # Track evaluation metadata as evidence
        self._track_evaluation_metadata(evaluation_result)

        return all_evidence_keys

    def _track_evaluation_metadata(self, evaluation_result: EvaluationResult) -> None:
        """Track evaluation metadata as evidence."""
        metadata_evidence = {
            "evidence_key": "evaluation_metadata",
            "item_id": "system",
            "source_type": "evaluation_metadata",
            "source_path": "$.evaluation_metadata",
            "description": "Evaluation process metadata and statistics",
            "confidence": 1.0,
            "raw_data": json.dumps({
                "evaluator_version": evaluation_result.evaluation_metadata.evaluator_version,
                "processing_duration": evaluation_result.evaluation_metadata.processing_duration,
                "warnings": evaluation_result.evaluation_metadata.warnings,
                "metrics_completeness": evaluation_result.evaluation_metadata.metrics_completeness
            }),
            "timestamp": datetime.now().isoformat(),
            "source_data": {
                "total_score": evaluation_result.total_score,
                "score_percentage": evaluation_result.score_percentage,
                "category_breakdowns": {
                    dimension: {
                        "items_count": breakdown.items_count,
                        "max_points": breakdown.max_points,
                        "actual_points": breakdown.actual_points,
                        "percentage": breakdown.percentage
                    }
                    for dimension, breakdown in evaluation_result.category_breakdowns.items()
                }
            }
        }

        self.evidence_store["evaluation_metadata"] = [metadata_evidence]

    def get_evidence_by_item(self, item_id: str) -> list[dict[str, Any]]:
        """Get all evidence for a specific checklist item."""
        item_evidence = []

        for evidence_key, evidence_list in self.evidence_store.items():
            for evidence in evidence_list:
                if evidence["item_id"] == item_id:
                    item_evidence.append(evidence)

        return item_evidence

    def get_evidence_by_type(self, source_type: str) -> list[dict[str, Any]]:
        """Get all evidence of a specific type."""
        type_evidence = []

        for evidence_list in self.evidence_store.values():
            for evidence in evidence_list:
                if evidence["source_type"] == source_type:
                    type_evidence.append(evidence)

        return type_evidence

    def get_high_confidence_evidence(self, threshold: float = 0.8) -> list[dict[str, Any]]:
        """Get evidence with confidence above threshold."""
        high_confidence = []

        for evidence_list in self.evidence_store.values():
            for evidence in evidence_list:
                if evidence["confidence"] >= threshold:
                    high_confidence.append(evidence)

        return high_confidence

    def generate_evidence_summary(self) -> dict[str, Any]:
        """Generate summary of all tracked evidence."""
        total_evidence = sum(len(evidence_list) for evidence_list in self.evidence_store.values())

        evidence_by_type = {}
        confidence_distribution = {"high": 0, "medium": 0, "low": 0}

        for evidence_list in self.evidence_store.values():
            for evidence in evidence_list:
                # Count by type
                source_type = evidence["source_type"]
                evidence_by_type[source_type] = evidence_by_type.get(source_type, 0) + 1

                # Confidence distribution
                confidence = evidence["confidence"]
                if confidence >= 0.8:
                    confidence_distribution["high"] += 1
                elif confidence >= 0.5:
                    confidence_distribution["medium"] += 1
                else:
                    confidence_distribution["low"] += 1

        return {
            "total_evidence_items": total_evidence,
            "evidence_by_type": evidence_by_type,
            "confidence_distribution": confidence_distribution,
            "unique_evidence_keys": len(self.evidence_store),
            "generation_timestamp": datetime.now().isoformat()
        }

    def save_evidence_files(self) -> dict[str, str]:
        """Save evidence to structured files and return file paths."""
        saved_files = {}

        # Create evidence directory structure
        self.evidence_base_path.mkdir(parents=True, exist_ok=True)

        # Save individual evidence files by dimension
        dimensions = ["code_quality", "testing", "documentation", "system"]
        for dimension in dimensions:
            dimension_path = self.evidence_base_path / dimension
            dimension_path.mkdir(exist_ok=True)

        # Save evidence by checklist item
        for evidence_key, evidence_list in self.evidence_store.items():
            if evidence_list:
                first_evidence = evidence_list[0]
                item_id = first_evidence["item_id"]

                # Determine dimension from item_id
                if item_id.startswith("code_quality"):
                    dimension = "code_quality"
                elif item_id.startswith("testing"):
                    dimension = "testing"
                elif item_id.startswith("documentation"):
                    dimension = "documentation"
                else:
                    dimension = "system"

                # Save evidence file
                evidence_file = self.evidence_base_path / dimension / f"{evidence_key}.json"
                with open(evidence_file, 'w', encoding='utf-8') as f:
                    json.dump(evidence_list, f, indent=2, ensure_ascii=False)

                saved_files[evidence_key] = str(evidence_file)

        # Save evidence summary
        summary = self.generate_evidence_summary()
        summary_file = self.evidence_base_path / "evidence_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        saved_files["evidence_summary"] = str(summary_file)

        # Save evidence manifest
        manifest = {
            "generated_at": datetime.now().isoformat(),
            "evidence_base_path": str(self.evidence_base_path),
            "files": saved_files,
            "total_files": len(saved_files)
        }

        manifest_file = self.evidence_base_path / "manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        saved_files["manifest"] = str(manifest_file)
        self.file_manifest = saved_files

        return saved_files

    def load_evidence_from_files(self, evidence_path: str) -> None:
        """Load previously saved evidence from files."""
        evidence_base = Path(evidence_path)

        if not evidence_base.exists():
            raise FileNotFoundError(f"Evidence path not found: {evidence_path}")

        # Load manifest if available
        manifest_file = evidence_base / "manifest.json"
        if manifest_file.exists():
            with open(manifest_file, encoding='utf-8') as f:
                self.file_manifest = json.load(f)["files"]

        # Load evidence files
        self.evidence_store = {}
        for evidence_file in evidence_base.rglob("*.json"):
            if evidence_file.name not in ["evidence_summary.json", "manifest.json"]:
                try:
                    with open(evidence_file, encoding='utf-8') as f:
                        evidence_data = json.load(f)

                    if isinstance(evidence_data, list) and evidence_data:
                        evidence_key = evidence_data[0].get("evidence_key", evidence_file.stem)
                        self.evidence_store[evidence_key] = evidence_data

                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Warning: Could not load evidence file {evidence_file}: {e}")

    def validate_evidence_integrity(self) -> dict[str, Any]:
        """Validate integrity of tracked evidence."""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }

        required_fields = ["evidence_key", "item_id", "source_type", "confidence", "timestamp"]

        for evidence_key, evidence_list in self.evidence_store.items():
            for i, evidence in enumerate(evidence_list):
                # Check required fields
                for field in required_fields:
                    if field not in evidence:
                        validation_results["errors"].append(
                            f"Missing required field '{field}' in {evidence_key}[{i}]"
                        )
                        validation_results["valid"] = False

                # Validate confidence range
                confidence = evidence.get("confidence", 0)
                if not (0.0 <= confidence <= 1.0):
                    validation_results["errors"].append(
                        f"Invalid confidence {confidence} in {evidence_key}[{i}] (must be 0.0-1.0)"
                    )
                    validation_results["valid"] = False

                # Check for empty descriptions
                description = evidence.get("description", "")
                if not description.strip():
                    validation_results["warnings"].append(
                        f"Empty description in {evidence_key}[{i}]"
                    )

        # Generate statistics
        validation_results["statistics"] = {
            "total_evidence_items": sum(len(el) for el in self.evidence_store.values()),
            "unique_evidence_keys": len(self.evidence_store),
            "error_count": len(validation_results["errors"]),
            "warning_count": len(validation_results["warnings"])
        }

        return validation_results

    def export_evidence_report(self, output_path: str) -> str:
        """Export comprehensive evidence report in markdown format."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        summary = self.generate_evidence_summary()

        lines = [
            "# Evidence Collection Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Total Evidence Items:** {summary['total_evidence_items']}",
            f"**Unique Evidence Keys:** {summary['unique_evidence_keys']}",
            "",
            "## Evidence Distribution by Type",
            ""
        ]

        for source_type, count in summary["evidence_by_type"].items():
            lines.append(f"- **{source_type}:** {count} items")

        lines.extend([
            "",
            "## Confidence Distribution",
            "",
            f"- **High Confidence (≥0.8):** {summary['confidence_distribution']['high']} items",
            f"- **Medium Confidence (0.5-0.8):** {summary['confidence_distribution']['medium']} items",
            f"- **Low Confidence (<0.5):** {summary['confidence_distribution']['low']} items",
            "",
            "## Detailed Evidence Listing",
            ""
        ])

        # List evidence by checklist item
        items_with_evidence = set()
        for evidence_list in self.evidence_store.values():
            for evidence in evidence_list:
                items_with_evidence.add(evidence["item_id"])

        for item_id in sorted(items_with_evidence):
            lines.append(f"### {item_id}")
            lines.append("")

            item_evidence = self.get_evidence_by_item(item_id)
            for evidence in item_evidence:
                confidence_label = "High" if evidence["confidence"] >= 0.8 else "Medium" if evidence["confidence"] >= 0.5 else "Low"
                lines.extend([
                    f"- **{evidence['source_type']}** ({confidence_label} confidence)",
                    f"  - Description: {evidence['description']}",
                    f"  - Source Path: {evidence['source_path']}",
                    f"  - Timestamp: {evidence['timestamp']}",
                    ""
                ])

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        return str(output_file)
