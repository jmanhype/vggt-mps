# Recursive Language Model (RLM) Self-Improvement System

This repository implements a **Recursive Language Model (RLM)** system for autonomous code improvement, based on the research paper ["Recursive Language Models" by Zhang & Khattab (2025)](https://alexzhang13.github.io/blog/2025/rlm/).

## 🧠 What is an RLM?

A Recursive Language Model is an inference strategy where language models can decompose and recursively interact with input context of unbounded length through REPL environments.

Unlike traditional agents that decompose problems, RLMs decompose **context**:
- **Traditional Agents**: Break down tasks based on human intuition
- **RLMs**: Let the LM decide how to partition and recurse over context

## 🏗️ Architecture

Our implementation uses a 3-depth recursive architecture:

```
┌─────────────────────────────────────────────────────────────┐
│ DEPTH 1: ROOT LM (Analysis & Partitioning)                 │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ • PEEK: Use Glob to understand repository structure   │   │
│ │ • GREP: Find patterns (TODOs, FIXMEs, errors)         │   │
│ │ • PARTITION: Identify 2-4 improvement areas           │   │
│ │ • OUTPUT: Execution trace → .rlm-trace/depth-1-*.md   │   │
│ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Execution Trace
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ DEPTH 2: RECURSIVE LM (Parallel Implementation)            │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│ │ Partition 1  │  │ Partition 2  │  │ Partition 3  │       │
│ │ • Read D1    │  │ • Read D1    │  │ • Read D1    │       │
│ │ • Implement  │  │ • Implement  │  │ • Implement  │       │
│ │ • Detect ⚠️  │  │ • Detect ⚠️  │  │ • Detect ⚠️  │       │
│ │ • Write trace│  │ • Write trace│  │ • Write trace│       │
│ └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Multiple Execution Traces
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ DEPTH 3: AGGREGATION LM (Integration & PR)                 │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ • AGGREGATE: Read all D1 + D2 traces                  │   │
│ │ • DETECT: Find conflicts between parallel changes     │   │
│ │ • RESOLVE: 3-way merge, rebase, semantic resolution   │   │
│ │ • VALIDATE: Run tests, check integration             │   │
│ │ • OUTPUT: Create PR with receipt hash                │   │
│ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Execution Trace Format

Each depth creates a structured execution trace:

```markdown
# RLM Execution Trace - Depth N

## Input Context
- Parent Commit: abc123...
- Focus Area: error-handling
- Files Analyzed: [src/main.py, tests/test_main.py]

## Discoveries (PEEK/GREP results)
- Pattern 1: Missing try/except in 15 functions
- Pattern 2: No type hints in core modules

## Actions Taken (MAP/IMPLEMENT)
- Action 1: Added error handling to database operations
- Action 2: Added type hints to config.py

## Conflicts Detected
- Conflict 1: Modified same lines as partition-2
- Resolution: Used 3-way merge with base commit

## Validation
- Tests run: pytest tests/
- Tests passed: yes (23/23)

## Receipt
Hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

## 🔄 Recursive Execution Flow

### Depth 1: Analysis Phase (25 turns)
```python
# What Depth 1 does:
1. glob("**/*.py")  # Understand structure
2. grep("TODO|FIXME")  # Find improvement candidates
3. read(README, main files)  # Understand project
4. partition({
     "error-handling": [file1, file2],
     "type-hints": [file3, file4],
     "tests": [file5, file6],
     "docs": [README, ...]
   })
5. write(".rlm-trace/depth-1-plan.md")
```

### Depth 2: Implementation Phase (40 turns each)
```python
# What each Depth 2 instance does:
parent_analysis = read(".rlm-trace/depth-1-plan.md")
my_partition = get_assigned_partition()  # e.g., "error-handling"

for file in my_partition.files:
    changes = implement_improvements(file)
    conflicts = check_conflicts_with_siblings()

write(f".rlm-trace/depth-2-{my_partition}.md")
```

### Depth 3: Integration Phase (30 turns)
```python
# What Depth 3 does:
all_changes = read_all_traces(depth=1,2)
conflicts = detect_conflicts(all_changes)

for conflict in conflicts:
    if conflict.type == "overlapping":
        resolve_with_3way_merge(conflict)
    elif conflict.type == "dependent":
        reorder_and_rebase(conflict)
    elif conflict.type == "semantic":
        use_deeper_understanding(conflict)

run_tests()
create_pr_with_receipt()
```

## ⚠️ Conflict Resolution

The system detects and resolves three types of conflicts:

### 1. Overlapping Conflicts
**Problem**: Multiple depths modify the same lines differently

**Detection**:
```bash
comm -12 <(sort depth-2-partition-1-files.txt) \
         <(sort depth-2-partition-2-files.txt)
```

**Resolution**: 3-way merge
```python
base = git_show(f"HEAD~2:file.py")
ours = depth_2_partition_1_version
theirs = depth_2_partition_2_version
merged = three_way_merge(base, ours, theirs)
```

### 2. Dependent Conflicts
**Problem**: Changes depend on execution order

**Detection**: Check if depth N+1 modifies files from depth N

**Resolution**: Rebase/reorder
```python
# Ensure changes are applied in dependency order
changes = sort_by_depth(all_changes)
apply_in_order(changes)
```

### 3. Semantic Conflicts
**Problem**: Changes conflict in meaning, not text

**Detection**: LLM analyzes intent of overlapping changes

**Resolution**: Use deeper depth's understanding
```python
# Depth 3 has more context than Depth 2
if conflict.type == "semantic":
    use_version_from_depth(max(conflict.depths))
```

## 🚀 Usage

### Automatic Runs (Scheduled)
The workflow runs twice daily (6am and 6pm Central Time):
```yaml
schedule:
  - cron: "0 11 * * *"  # 6am CT
  - cron: "0 23 * * *"  # 6pm CT
```

### Manual Trigger
```bash
gh workflow run recursive-self-improve.yml
```

### Custom Focus Area
```bash
gh workflow run recursive-self-improve.yml \
  --field focus_area=tests \
  --field max_depth=3
```

### Local Testing
```bash
# Run conflict resolver on traces
python .github/scripts/rlm-conflict-resolver.py \
  --trace-dir .rlm-trace \
  --auto-resolve

# View resolution report
cat .rlm-trace/resolution-report.md
```

## 📊 Execution Traces

All execution traces are stored in `.rlm-trace/` and uploaded as GitHub Actions artifacts:

```
.rlm-trace/
├── depth-1-plan.md              # Root analysis
├── depth-2-error-handling.md    # Partition 1
├── depth-2-type-hints.md        # Partition 2
├── depth-2-tests.md             # Partition 3
├── depth-3-integration.md       # Final integration
└── resolution-report.md         # Conflict resolution
```

### Viewing Traces
```bash
# Download from GitHub Actions
gh run download <run-id> --name rlm-traces-depth-1

# Or view in PR comments (automatically posted)
gh pr view <pr-number>
```

## 🎯 Key Benefits

### 1. Unbounded Context Length
- No single LM call processes huge context
- Context partitioned adaptively by the LM itself
- Successfully handles 10M+ tokens (from paper results)

### 2. Avoids Context Rot
- Root LM context window rarely clogged
- Each recursive call has fresh context
- Performance doesn't degrade with context size

### 3. Parallel Execution
- Depth 2 instances run in parallel
- Conflicts detected and resolved automatically
- Faster than sequential agents

### 4. Full Transparency
- Every decision logged in execution traces
- Conflicts and resolutions visible
- Reproducible and debuggable

## 📈 Performance (from paper)

On OOLONG benchmark (132k tokens):
- **RLM(GPT-5-mini)**: 63.2% (114% improvement over GPT-5)
- **GPT-5**: 29.5%
- **GPT-5-mini**: 26.1%

On BrowseComp-Plus (1000 documents):
- **RLM(GPT-5)**: 100% accuracy
- **ReAct + BM25**: ~60% accuracy
- **GPT-5 (truncated)**: ~40% accuracy

Cost per query roughly equivalent to single GPT-5 call!

## 🔧 Configuration

### Modify Max Depth
Edit `.github/workflows/recursive-self-improve.yml`:
```yaml
strategy:
  matrix:
    depth: [1, 2, 3, 4]  # Add more depths
```

### Change Turn Limits
```yaml
claude_args: |
  --max-turns ${{ matrix.depth == 1 && 30 || matrix.depth == 2 && 50 || 40 }}
```

### Adjust Focus Areas
```python
# In prompt for Depth 1
PARTITION work into focus areas:
- error-handling
- type-hints
- tests
- docs
- performance  # Add new area
```

## 🛡️ Guardrails

RLM execution respects all constraints in `CLAUDE.md`:
- ✅ Can modify: source code, tests, docs, configs
- ❌ Cannot: break APIs, remove features, add heavy deps
- ✅ Must: create execution traces, detect conflicts, validate changes

## 📚 References

1. **Recursive Language Models** (Zhang & Khattab, 2025)
   - Paper: https://alexzhang13.github.io/blog/2025/rlm/
   - GitHub: https://github.com/alexzhang13/rlm

2. **OOLONG Benchmark** (Anonymous, 2025)
   - Long-context reasoning over fine-grained information

3. **CodeAct** (Wang et al., 2024)
   - Executable code actions elicit better LLM agents

## 🤝 Contributing

When contributing to the RLM system:

1. **Test locally** with conflict resolver before submitting
2. **Review execution traces** to understand decisions
3. **Add new patterns** to the RLM prompt if needed
4. **Document conflicts** that required manual resolution

## 📝 License

Same as parent repository.

---

*This RLM implementation demonstrates that autonomous code improvement can scale to large codebases by letting the LM decide how to partition and recurse over context, rather than imposing human-designed decomposition strategies.*
