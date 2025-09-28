# Research: Remove Phantom Evidence Paths from ScoringMapper

## Problem Analysis

### Current Phantom Paths Issue
The `ScoringMapper._generate_evidence_paths()` method hardcodes three phantom file paths that are never created:

**Decision**: Remove phantom paths: `evaluation_summary.json`, `category_breakdowns.json`, `warnings.log`
**Rationale**: These paths reference non-existent files, causing integration failures when external systems attempt file access. The EvidenceTracker never creates these files, making the references misleading and breaking the interface contract.
**Alternatives considered**:
- Creating the missing files: Rejected due to unclear purpose and added complexity
- Renaming existing files to match phantom paths: Rejected due to breaking change impact

### Evidence File Generation Flow

**Decision**: Maintain existing EvidenceTracker behavior with improved path consistency
**Rationale**: EvidenceTracker correctly creates individual evidence files by dimension plus summary/manifest files. The issue is phantom path generation, not evidence creation.
**Alternatives considered**:
- Overhauling evidence file structure: Rejected as over-engineering for the scope
- Changing EvidenceTracker to match phantom paths: Rejected as it validates the broken interface

### File Existence Validation

**Decision**: Add validation to ensure evidence_paths only contains existing files
**Rationale**: Provides fail-fast behavior aligned with KISS principle. External integrations require reliable file references.
**Alternatives considered**:
- Warning-only approach: Rejected as it doesn't solve integration failures
- Lazy validation on access: Rejected as validation should be immediate and clear

## Technical Implementation Approach

### Core Changes Required
1. **Remove phantom path hardcoding** from `ScoringMapper._generate_evidence_paths()` (lines 57-61)
2. **Add file existence validation** before including paths in evidence_paths output
3. **Ensure EvidenceTracker-ScoringMapper consistency** through explicit path mapping

### Affected Components
- `src/metrics/scoring_mapper.py`: Remove phantom path generation
- `src/metrics/evidence_tracker.py`: No changes needed (correct behavior)
- `src/cli/evaluate.py`: Potential validation enhancement
- Tests: Add coverage for evidence path consistency

### Validation Strategy
- Pre-output validation: Verify all evidence_paths point to existing files
- Integration tests: End-to-end validation of evidence file accessibility
- Contract tests: Schema validation with file existence requirements

## Constitutional Compliance

### KISS Principle Alignment
- **Simple fix**: Remove hardcoded phantom paths rather than complex workarounds
- **Fail-fast**: Immediate validation prevents downstream integration failures
- **Direct approach**: Target root cause rather than symptoms

### UV Dependency Management
- **No new dependencies**: Working within existing Python/pytest/UV environment
- **Existing toolchain**: Leverage current testing and validation infrastructure

## Implementation Risk Assessment

### Low Risk Changes
- Phantom path removal: No functional impact (paths never pointed to real files)
- Validation addition: Defensive programming with clear failure modes
- Test coverage expansion: Improves system reliability

### Compatibility Considerations
- **Backward compatible**: score_input.json structure unchanged, only phantom entries removed
- **Integration safe**: External systems will see fewer entries (no longer broken ones)
- **Evidence file structure**: No changes to actual evidence file creation or organization

## Success Criteria Validation

### Functional Requirements Mapping
- **FR-001**: File existence validation ensures all paths point to existing files
- **FR-002**: Phantom path removal excludes non-existent placeholders
- **FR-003**: Users can access every referenced file (no more 404 errors)
- **FR-004**: EvidenceTracker-ScoringMapper consistency through explicit mapping
- **FR-005**: Pre-output validation confirms file existence

### Testing Requirements
- Unit tests for phantom path removal behavior
- Integration tests for evidence_paths accuracy
- Contract tests for score_input.json consistency
- Smoke tests for CLI evaluation workflow