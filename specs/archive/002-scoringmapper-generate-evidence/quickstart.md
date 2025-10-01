# Quickstart: Remove Phantom Evidence Paths

## 🎯 Goal
Verify that evidence_paths in score_input.json only contains file paths that actually exist, with phantom paths removed.

## 🧪 Test Scenarios

### Scenario 1: Basic Evidence Path Validation
**User Story**: As a developer running code evaluation, I want evidence_paths to only reference accessible files.

#### Steps:
```bash
# 1. Run evaluation on test repository
./scripts/run_metrics.sh git@github.com:AIGCInnovatorSpace/code-walker.git --enable-checklist

# 2. Verify output files exist
ls -la output/

# 3. Check score_input.json evidence_paths
cat output/score_input.json | jq '.evidence_paths'

# 4. Validate all referenced files exist
jq -r '.evidence_paths[]' output/score_input.json | while read file; do
  if [ ! -f "$file" ]; then
    echo "ERROR: Referenced file does not exist: $file"
    exit 1
  fi
done
echo "✅ All evidence files exist"
```

#### Expected Result:
- All paths in evidence_paths point to existing files
- No file-not-found errors when accessing evidence files
- Phantom paths (`evaluation_summary`, `category_breakdowns`, `warnings_log`) are absent

### Scenario 2: Phantom Path Removal Verification
**User Story**: As an integration developer, I want reliable evidence file references without phantom paths.

#### Steps:
```bash
# 1. Run evaluation and capture evidence_paths
./scripts/run_metrics.sh git@github.com:AIGCInnovatorSpace/code-walker.git --enable-checklist
evidence_keys=$(jq -r '.evidence_paths | keys[]' output/score_input.json)

# 2. Check for phantom paths (should not be present)
phantom_paths=("evaluation_summary" "category_breakdowns" "warnings_log")
for phantom in "${phantom_paths[@]}"; do
  if echo "$evidence_keys" | grep -q "^$phantom$"; then
    echo "ERROR: Found phantom path: $phantom"
    exit 1
  fi
done
echo "✅ No phantom paths found"

# 3. Verify real evidence files are accessible
for key in $evidence_keys; do
  file_path=$(jq -r ".evidence_paths.\"$key\"" output/score_input.json)
  if [ -f "$file_path" ] && [ -s "$file_path" ]; then
    echo "✅ $key -> $file_path (exists, non-empty)"
  else
    echo "ERROR: Evidence file issue for $key: $file_path"
    exit 1
  fi
done
```

#### Expected Result:
- `evaluation_summary` key not present in evidence_paths
- `category_breakdowns` key not present in evidence_paths
- `warnings_log` key not present in evidence_paths
- All remaining evidence files are accessible and non-empty

### Scenario 3: Integration System Workflow
**User Story**: As an external system, I want to process all evidence files referenced in score_input.json.

#### Steps:
```bash
# 1. Run evaluation
./scripts/run_metrics.sh git@github.com:AIGCInnovatorSpace/code-walker.git --enable-checklist

# 2. Simulate integration system processing
evidence_paths_json=$(jq '.evidence_paths' output/score_input.json)
echo "$evidence_paths_json" | jq -r 'to_entries[] | "\(.key) \(.value)"' | while read key path; do
  # Attempt to read each evidence file
  if content=$(cat "$path" 2>/dev/null); then
    echo "✅ Successfully read evidence: $key"
    # Validate JSON format
    if echo "$content" | jq . >/dev/null 2>&1; then
      echo "  └─ Valid JSON format"
    else
      echo "  └─ WARNING: Not valid JSON"
    fi
  else
    echo "ERROR: Cannot read evidence file: $key -> $path"
    exit 1
  fi
done
```

#### Expected Result:
- All evidence files can be read without errors
- Integration workflow completes successfully
- No FileNotFoundError exceptions

## 🔬 Validation Commands

### Quick Validation
```bash
# Ensure evidence_paths contains only existing files
jq -r '.evidence_paths[]' output/score_input.json | xargs ls -la
```

### Phantom Path Detection
```bash
# Check for phantom paths (should return no results)
jq -r '.evidence_paths | keys[]' output/score_input.json | grep -E "(evaluation_summary|category_breakdowns|warnings_log)"
```

### Evidence File Count
```bash
# Count evidence files
actual_files=$(find output/evidence -name "*.json" | wc -l)
referenced_files=$(jq '.evidence_paths | length' output/score_input.json)
echo "Actual evidence files: $actual_files"
echo "Referenced in evidence_paths: $referenced_files"
```

## 🧪 Test Data Setup

### Repository Requirements
- **Test Repository**: git@github.com:AIGCInnovatorSpace/code-walker.git
- **Language**: Python (for consistent tool execution)
- **Expected Evidence**: Lint results, test results, documentation analysis

### Environment Prerequisites
```bash
# Ensure UV and dependencies are available
uv sync --dev

# Verify tool availability
uv run python -c "from src.metrics.scoring_mapper import ScoringMapper; print('✅ ScoringMapper available')"
uv run python -c "from src.metrics.evidence_tracker import EvidenceTracker; print('✅ EvidenceTracker available')"
```

## ⚡ Success Criteria Checklist

### Functional Validation
- [ ] **FR-001**: All evidence_paths point to existing files
- [ ] **FR-002**: Phantom paths excluded from output
- [ ] **FR-003**: All referenced files are accessible
- [ ] **FR-004**: EvidenceTracker-ScoringMapper consistency maintained
- [ ] **FR-005**: File existence validated before output generation

### Technical Validation
- [ ] ScoringMapper._generate_evidence_paths() removes phantom paths
- [ ] EvidenceTracker behavior unchanged (creates correct files)
- [ ] score_input.json schema unchanged (only content refined)
- [ ] CLI evaluation workflow produces validated evidence_paths
- [ ] Integration tests pass with new behavior

### Performance Validation
- [ ] Evidence path generation time unchanged (< 10ms typical)
- [ ] File existence validation adds minimal overhead
- [ ] Memory usage unchanged or reduced (fewer phantom entries)

## 🔧 Troubleshooting

### Common Issues

**Issue**: "Evidence file not found" errors
**Solution**: Check that EvidenceTracker successfully created evidence files before ScoringMapper generates paths

**Issue**: Empty evidence_paths in score_input.json
**Solution**: Verify evaluation completed successfully and generated evidence files

**Issue**: Phantom paths still present
**Solution**: Confirm ScoringMapper._generate_evidence_paths() phantom path removal implementation

### Debug Commands
```bash
# Check evidence file generation
ls -la output/evidence/

# Verify ScoringMapper behavior
uv run python -c "
from src.metrics.scoring_mapper import ScoringMapper
# Add debug code to inspect _generate_evidence_paths behavior
"

# Validate evidence_paths schema
jq '.evidence_paths' output/score_input.json | jq 'type'
```

## 📊 Expected Output Examples

### Before (with phantom paths):
```json
{
  "evidence_paths": {
    "code_quality_lint": "/output/evidence/code_quality/lint.json",
    "testing_results": "/output/evidence/testing/tests.json",
    "evaluation_summary": "/output/evidence/evaluation_summary.json",
    "category_breakdowns": "/output/evidence/category_breakdowns.json",
    "warnings_log": "/output/evidence/warnings.log"
  }
}
```

### After (phantom paths removed):
```json
{
  "evidence_paths": {
    "code_quality_lint": "/output/evidence/code_quality/lint.json",
    "testing_results": "/output/evidence/testing/tests.json",
    "evidence_summary": "/output/evidence/evidence_summary.json",
    "manifest": "/output/evidence/manifest.json"
  }
}
```

**Key Changes**:
- ❌ `evaluation_summary` removed (phantom)
- ❌ `category_breakdowns` removed (phantom)
- ❌ `warnings_log` removed (phantom)
- ✅ `evidence_summary` present (real file created by EvidenceTracker)
- ✅ `manifest` present (real file created by EvidenceTracker)