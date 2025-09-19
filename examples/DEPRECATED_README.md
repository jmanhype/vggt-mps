# ⚠️ DEPRECATED - Old Examples

These example scripts are **deprecated** and kept for reference only.

## Migration to New Structure

The project has been reorganized with a clean, professional structure:

### Old Way (Deprecated):
```bash
# Running individual demo scripts
python examples/demo_vggt_mps.py
python examples/demo_kitchen_2images.py
```

### New Way (Recommended):
```bash
# Single entry point with subcommands
python main.py demo
python main.py demo --kitchen --images 2
python main.py reconstruct data/*.jpg
python main.py test
python main.py benchmark --compare
python main.py web
```

## Benefits of New Structure:

1. **Single Entry Point** - All functionality through `main.py`
2. **No Hardcoded Paths** - Works on any system
3. **Organized Commands** - Clear subcommands for each feature
4. **Centralized Config** - All settings in `src/config.py`
5. **Proper Testing** - Organized test suite in `tests/`

## Files in this Directory:

- `demo_vggt_mps.py` - Old MPS demo (use `python main.py demo`)
- `demo_kitchen_2images.py` - Kitchen dataset demo (use `python main.py demo --kitchen`)
- `demo_portable.py` - Portable demo attempt (now default behavior)
- `vggt_mps_inference.py` - Direct inference script (use `python main.py reconstruct`)
- `create_test_images.py` - Test image creator (moved to `src/utils/`)

## MCP Server Note:

The MCP server tools in `src/tools/` remain unchanged and continue to work with the new structure.