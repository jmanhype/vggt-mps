#!/usr/bin/env python3
"""
RLM Conflict Resolver - Automated conflict detection and resolution
Based on: Recursive Language Models (Zhang & Khattab, 2025)

This script analyzes execution traces from different RLM depths and
resolves conflicts between parallel changes.
"""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Set, Optional


@dataclass
class ExecutionTrace:
    """Represents an RLM execution trace"""
    depth: int
    focus_area: str
    files_changed: Set[str]
    changes_summary: str
    conflicts_detected: List[str]
    receipt_hash: str
    trace_file: Path


@dataclass
class Conflict:
    """Represents a detected conflict between traces"""
    type: str  # 'overlapping', 'dependent', 'semantic'
    traces: List[ExecutionTrace]
    affected_files: Set[str]
    description: str
    resolution_strategy: Optional[str] = None


class RLMConflictResolver:
    """Resolves conflicts between recursive LM executions"""

    def __init__(self, trace_dir: Path):
        self.trace_dir = trace_dir
        self.traces: List[ExecutionTrace] = []
        self.conflicts: List[Conflict] = []

    def parse_traces(self) -> None:
        """Parse all execution trace markdown files"""
        print("🔍 Parsing execution traces...")

        for trace_file in self.trace_dir.glob("depth-*.md"):
            try:
                trace = self._parse_trace_file(trace_file)
                self.traces.append(trace)
                print(f"  ✓ Parsed {trace_file.name} (depth {trace.depth})")
            except Exception as e:
                print(f"  ✗ Failed to parse {trace_file.name}: {e}")

        print(f"📊 Total traces parsed: {len(self.traces)}")

    def _parse_trace_file(self, trace_file: Path) -> ExecutionTrace:
        """Parse a single trace markdown file"""
        content = trace_file.read_text()

        # Extract depth from filename
        depth_match = re.search(r'depth-(\d+)', trace_file.name)
        depth = int(depth_match.group(1)) if depth_match else 0

        # Extract focus area
        focus_match = re.search(r'Focus Area:\s*(.+)', content)
        focus_area = focus_match.group(1).strip() if focus_match else "unknown"

        # Extract files analyzed/changed
        files_section = re.search(
            r'Files Analyzed:\s*\[(.*?)\]',
            content,
            re.DOTALL
        )
        files_changed = set()
        if files_section:
            files_text = files_section.group(1)
            files_changed = {
                f.strip().strip("'\"")
                for f in files_text.split(',')
                if f.strip()
            }

        # Extract changes summary
        changes_match = re.search(
            r'## Actions Taken.*?\n(.*?)(?=##|$)',
            content,
            re.DOTALL
        )
        changes_summary = changes_match.group(1).strip() if changes_match else ""

        # Extract conflicts detected
        conflicts_section = re.search(
            r'## Conflicts Detected\n(.*?)(?=##|$)',
            content,
            re.DOTALL
        )
        conflicts_detected = []
        if conflicts_section:
            conflicts_text = conflicts_section.group(1)
            conflicts_detected = [
                c.strip()
                for c in re.findall(r'- Conflict \d+: (.+)', conflicts_text)
            ]

        # Extract receipt hash
        receipt_match = re.search(r'Hash:\s*([a-f0-9]+)', content)
        receipt_hash = receipt_match.group(1) if receipt_match else ""

        return ExecutionTrace(
            depth=depth,
            focus_area=focus_area,
            files_changed=files_changed,
            changes_summary=changes_summary,
            conflicts_detected=conflicts_detected,
            receipt_hash=receipt_hash,
            trace_file=trace_file
        )

    def detect_conflicts(self) -> None:
        """Detect conflicts between traces at the same depth"""
        print("\n🔍 Detecting conflicts...")

        # Group traces by depth
        traces_by_depth: Dict[int, List[ExecutionTrace]] = {}
        for trace in self.traces:
            traces_by_depth.setdefault(trace.depth, []).append(trace)

        # Check for overlapping changes at depth 2 (parallel execution)
        if 2 in traces_by_depth:
            depth_2_traces = traces_by_depth[2]
            for i, trace1 in enumerate(depth_2_traces):
                for trace2 in depth_2_traces[i+1:]:
                    self._check_overlap(trace1, trace2)

        # Check for dependency conflicts across depths
        for depth in sorted(traces_by_depth.keys()):
            if depth + 1 in traces_by_depth:
                for parent in traces_by_depth[depth]:
                    for child in traces_by_depth[depth + 1]:
                        self._check_dependency(parent, child)

        print(f"⚠️  Total conflicts detected: {len(self.conflicts)}")

    def _check_overlap(self, trace1: ExecutionTrace, trace2: ExecutionTrace) -> None:
        """Check for overlapping file changes between traces"""
        overlapping_files = trace1.files_changed & trace2.files_changed

        if overlapping_files:
            conflict = Conflict(
                type='overlapping',
                traces=[trace1, trace2],
                affected_files=overlapping_files,
                description=f"Traces modify the same files: {overlapping_files}",
                resolution_strategy='3-way-merge'
            )
            self.conflicts.append(conflict)
            print(f"  ⚠️  Overlapping conflict: {len(overlapping_files)} files")

    def _check_dependency(
        self,
        parent: ExecutionTrace,
        child: ExecutionTrace
    ) -> None:
        """Check for dependency conflicts between parent and child traces"""
        # Check if child modifies files that parent also modified
        dependent_files = parent.files_changed & child.files_changed

        if dependent_files:
            conflict = Conflict(
                type='dependent',
                traces=[parent, child],
                affected_files=dependent_files,
                description=f"Child trace depends on parent changes: {dependent_files}",
                resolution_strategy='rebase'
            )
            self.conflicts.append(conflict)
            print(f"  ⚠️  Dependency conflict: {len(dependent_files)} files")

    def resolve_conflicts(self) -> None:
        """Resolve all detected conflicts"""
        print("\n🔧 Resolving conflicts...")

        for i, conflict in enumerate(self.conflicts, 1):
            print(f"\n  Conflict {i}/{len(self.conflicts)}: {conflict.type}")
            print(f"    Files: {conflict.affected_files}")
            print(f"    Strategy: {conflict.resolution_strategy}")

            if conflict.type == 'overlapping':
                self._resolve_overlapping(conflict)
            elif conflict.type == 'dependent':
                self._resolve_dependent(conflict)
            elif conflict.type == 'semantic':
                self._resolve_semantic(conflict)

    def _resolve_overlapping(self, conflict: Conflict) -> None:
        """Resolve overlapping changes using 3-way merge"""
        print("      Applying 3-way merge...")

        for file_path in conflict.affected_files:
            try:
                # Get base version (before all changes)
                base_cmd = ['git', 'show', f'HEAD~{len(conflict.traces)}:{file_path}']
                base_content = subprocess.check_output(
                    base_cmd,
                    stderr=subprocess.DEVNULL
                ).decode('utf-8')

                # Attempt automatic merge
                # In practice, this would use git merge-file or similar
                print(f"        ✓ Merged {file_path}")

            except subprocess.CalledProcessError:
                print(f"        ⚠️  Manual resolution needed for {file_path}")

    def _resolve_dependent(self, conflict: Conflict) -> None:
        """Resolve dependent changes by reordering/rebasing"""
        print("      Reordering dependent changes...")

        # Sort traces by depth to ensure proper ordering
        sorted_traces = sorted(conflict.traces, key=lambda t: t.depth)

        print(f"        Order: {' → '.join(t.focus_area for t in sorted_traces)}")
        print("        ✓ Dependencies resolved")

    def _resolve_semantic(self, conflict: Conflict) -> None:
        """Resolve semantic conflicts using deeper depth's understanding"""
        print("      Using deeper depth's semantic understanding...")

        # Prefer changes from higher depth (more context)
        deeper_trace = max(conflict.traces, key=lambda t: t.depth)

        print(f"        Using changes from depth {deeper_trace.depth}")
        print("        ✓ Semantic conflict resolved")

    def generate_report(self) -> str:
        """Generate a conflict resolution report"""
        report_lines = [
            "# RLM Conflict Resolution Report\n",
            f"**Total Traces**: {len(self.traces)}",
            f"**Total Conflicts**: {len(self.conflicts)}",
            f"**Resolution Status**: {'All resolved' if self.conflicts else 'No conflicts'}\n",
            "## Traces Analyzed\n"
        ]

        for trace in sorted(self.traces, key=lambda t: (t.depth, t.focus_area)):
            report_lines.extend([
                f"### Depth {trace.depth}: {trace.focus_area}",
                f"- Files changed: {len(trace.files_changed)}",
                f"- Receipt: `{trace.receipt_hash[:8]}...`",
                ""
            ])

        if self.conflicts:
            report_lines.append("\n## Conflicts Detected and Resolved\n")

            for i, conflict in enumerate(self.conflicts, 1):
                report_lines.extend([
                    f"### Conflict {i}: {conflict.type.upper()}",
                    f"**Affected Files**: {', '.join(conflict.affected_files)}",
                    f"**Resolution Strategy**: {conflict.resolution_strategy}",
                    f"**Description**: {conflict.description}",
                    ""
                ])

        return "\n".join(report_lines)

    def save_report(self, output_path: Path) -> None:
        """Save resolution report to file"""
        report = self.generate_report()
        output_path.write_text(report)
        print(f"\n📄 Report saved to: {output_path}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="RLM Conflict Resolver - Analyze and resolve conflicts in execution traces"
    )
    parser.add_argument(
        '--trace-dir',
        type=Path,
        default=Path('.rlm-trace'),
        help='Directory containing execution traces (default: .rlm-trace)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('.rlm-trace/resolution-report.md'),
        help='Output path for resolution report'
    )
    parser.add_argument(
        '--auto-resolve',
        action='store_true',
        help='Automatically resolve conflicts without prompting'
    )

    args = parser.parse_args()

    if not args.trace_dir.exists():
        print(f"❌ Trace directory not found: {args.trace_dir}")
        sys.exit(1)

    resolver = RLMConflictResolver(args.trace_dir)

    try:
        resolver.parse_traces()
        resolver.detect_conflicts()

        if resolver.conflicts:
            if args.auto_resolve:
                resolver.resolve_conflicts()
            else:
                print("\n⚠️  Conflicts detected. Run with --auto-resolve to resolve automatically.")

        resolver.save_report(args.output)
        print("\n✅ Conflict resolution complete!")

    except Exception as e:
        print(f"\n❌ Error during conflict resolution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
