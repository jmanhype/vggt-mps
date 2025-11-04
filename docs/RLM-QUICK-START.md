# RLM Self-Improvement: Quick Start Guide

## 🎯 What You Just Got

You now have **TWO autonomous self-improvement systems**:

### 1. Standard Self-Improve (`self-improve.yml`)
- Single Claude Code instance (75 turns)
- Linear execution: analyze → implement → PR
- Runs twice daily (6am/6pm CT)
- ✅ **Active** - includes Qodo integration

### 2. Recursive Self-Improve (`recursive-self-improve.yml`)
- Three Claude Code instances in recursive coordination
- Parallel execution with conflict resolution
- Execution trace logging for transparency
- 🆕 **Just added** - triggered manually or via schedule

## 🚀 Try It Now

### Manual Trigger
```bash
# Run the recursive workflow
gh workflow run recursive-self-improve.yml

# Watch it execute
gh run watch
```

### View Results
```bash
# List recent runs
gh run list --workflow=recursive-self-improve.yml

# View a specific run
gh run view <run-id> --log

# Download execution traces
gh run download <run-id> --name rlm-traces-depth-1
```

## 📊 What Happens During Execution

### Stage 1: Depth 1 (Root Analysis)
```
⏱️  Duration: ~5 minutes
🎯 Goal: Analyze codebase and partition work
📝 Output: .rlm-trace/depth-1-plan.md

Actions:
1. glob("**/*.py")           # Understand structure
2. grep("TODO|FIXME")        # Find patterns
3. read(key files)           # Get context
4. partition(improvements)   # Split work
```

### Stage 2: Depth 2 (Parallel Implementation)
```
⏱️  Duration: ~10 minutes (parallel)
🎯 Goal: Implement partitions in parallel
📝 Output: .rlm-trace/depth-2-*.md (one per partition)

Actions (for each partition):
1. read(depth-1-plan)        # Get instructions
2. implement(changes)        # Make improvements
3. detect_conflicts()        # Check overlaps
4. write(trace)              # Log execution
```

### Stage 3: Depth 3 (Integration)
```
⏱️  Duration: ~8 minutes
🎯 Goal: Resolve conflicts and create PR
📝 Output: .rlm-trace/depth-3-integration.md + PR

Actions:
1. read(all traces)          # Get full picture
2. detect_conflicts()        # Find overlaps
3. resolve(conflicts)        # Merge/rebase
4. validate(tests)           # Run tests
5. create_pr(receipt)        # Make PR
```

## 🔍 Understanding Execution Traces

Each depth creates a structured trace showing exactly what it did:

```markdown
# RLM Execution Trace - Depth 1

## Input Context
- Parent Commit: a852d94
- Focus Area: auto
- Files Analyzed: [README.md, src/*, tests/*]

## Discoveries
- Pattern 1: Missing error handling in 8 functions
- Pattern 2: No type hints in 15 files
- Pattern 3: 5 TODOs in core modules

## Partitions Created
1. error-handling → [config.py, utils.py]
2. type-hints → [models.py, processor.py]
3. todos → [main.py, README.md]

## Receipt
Hash: e3b0c442...
```

These traces are:
- 📤 **Uploaded** to GitHub Actions artifacts
- 💬 **Posted** as PR comments automatically
- 📥 **Downloadable** via `gh run download`

## ⚠️ Conflict Resolution

When parallel depth-2 executions modify the same files:

### Automatic Resolution
```python
if conflict.type == "overlapping":
    # Use 3-way merge
    base = git_show("HEAD~2:file.py")
    merge(base, version1, version2)

elif conflict.type == "dependent":
    # Reorder changes
    apply_in_dependency_order()

elif conflict.type == "semantic":
    # Use deeper understanding
    use_version_from_depth_3()
```

### Manual Review
If automatic resolution fails, depth 3 will:
1. Mark conflicts in the trace
2. Create PR anyway (with conflict markers)
3. Request human review via PR comment

## 📈 Comparing Both Systems

| Feature | Standard | Recursive (RLM) |
|---------|----------|-----------------|
| **Execution** | Sequential | Parallel |
| **Context Length** | 75k tokens max | Unbounded |
| **Conflict Handling** | Git auto-merge | Intelligent resolution |
| **Transparency** | Claude output | Execution traces |
| **Speed** | ~10 mins | ~15 mins (more thorough) |
| **Best For** | Quick fixes | Complex refactoring |

## 🎮 Advanced Usage

### Focus on Specific Area
```bash
gh workflow run recursive-self-improve.yml \
  --field focus_area=tests
```

Options: `tests`, `docs`, `perf`, `security`, `auto`

### Increase Recursion Depth
Edit `.github/workflows/recursive-self-improve.yml`:
```yaml
strategy:
  matrix:
    depth: [1, 2, 3, 4]  # Add depth 4
```

### Analyze Conflicts Locally
```bash
# Download traces
gh run download <run-id> --name rlm-traces-depth-1
gh run download <run-id> --name rlm-traces-depth-2
gh run download <run-id> --name rlm-traces-depth-3

# Run conflict analyzer
python .github/scripts/rlm-conflict-resolver.py \
  --trace-dir .rlm-trace \
  --auto-resolve

# View report
cat .rlm-trace/resolution-report.md
```

## 🐛 Troubleshooting

### Workflow Failed at Depth 2
```bash
# Check which partition failed
gh run view <run-id> --log | grep "matrix.depth: 2"

# View specific job logs
gh run view <run-id> --log --job=<job-id>
```

### No Execution Traces Created
```bash
# Check if trace directory was created
gh run view <run-id> --log | grep ".rlm-trace"

# If missing, depth didn't complete successfully
# Check for errors in that depth's log
```

### Conflicts Not Resolved
```bash
# Download traces and resolve manually
gh run download <run-id>

# Run conflict resolver
python .github/scripts/rlm-conflict-resolver.py --trace-dir .rlm-trace

# View conflicts
cat .rlm-trace/resolution-report.md
```

## 📚 Learn More

- [Full RLM System Documentation](./RLM-SYSTEM.md)
- [Original RLM Paper](https://alexzhang13.github.io/blog/2025/rlm/)
- [Execution Trace Format](./RLM-SYSTEM.md#-execution-trace-format)
- [Conflict Resolution Guide](./RLM-SYSTEM.md#-conflict-resolution)

## 🎯 Next Steps

1. **Watch the first run** complete:
   ```bash
   gh run watch
   ```

2. **Review the PR** created by depth 3:
   ```bash
   gh pr list | head -n 1
   ```

3. **Check execution traces** in PR comments

4. **Verify Qodo review** was triggered automatically

5. **Merge if satisfied** or provide feedback

## 💡 Tips

- **Start with auto focus** to let the RLM decide priorities
- **Review traces** to understand decision-making process
- **Compare with standard workflow** to see differences
- **Use recursive for complex** multi-file refactoring
- **Use standard for quick** single-focus improvements

## 🤝 When to Use Which?

**Use Standard Self-Improve when:**
- ✅ Quick bug fixes needed
- ✅ Single-focus improvements (just docs, just tests)
- ✅ Want faster execution (~10 mins)
- ✅ Context fits in 75k tokens

**Use Recursive RLM when:**
- ✅ Complex multi-area refactoring
- ✅ Large codebase (100k+ tokens)
- ✅ Want transparency via traces
- ✅ Need conflict-free parallel work
- ✅ Studying autonomous AI behavior

---

**Currently Running**: Check status at https://github.com/jmanhype/vggt-mps/actions/workflows/recursive-self-improve.yml

🎉 **Your recursive self-improvement system is live!**
