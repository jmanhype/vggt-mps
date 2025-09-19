# VGGT Sample Data

**Source:** Copied verbatim from the official [facebookresearch/vggt](https://github.com/facebookresearch/vggt) repository under `examples/kitchen/images`.

- `kitchen/00.png` – `03.png`

Use these images for quick demos:

```bash
# Run portable demo against sample data
default_images=examples/sample_data/kitchen/*.png
python examples/demo_portable.py --images $default_images
```

Please keep this directory in sync with upstream if additional scenes are needed.

Run `python scripts/fetch_sample_data.py --help` for more datasets.