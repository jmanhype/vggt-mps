# VGGT-MPS: 3D Vision Agent for Apple Silicon

[![Version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/jmanhype/vggt-mps/releases/tag/v2.0.0)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![MPS](https://img.shields.io/badge/Apple%20Silicon-M1%2FM2%2FM3-black)](https://developer.apple.com/metal/)

🍎 **VGGT (Visual Geometry Grounded Transformer) optimized for Apple Silicon with Metal Performance Shaders (MPS)**

Transform single or multi-view images into rich 3D reconstructions using Facebook Research's VGGT model, now accelerated on M1/M2/M3 Macs.

## 🎉 Release v2.0.0

**Major Update**: Complete packaging overhaul with unified CLI, PyPI-ready distribution, and production-grade tooling!

## ✨ What's New in v2.0.0

### 🎯 Major Changes
- **Unified CLI**: New `vggt` command with subcommands for all operations
- **Professional Packaging**: PyPI-ready with `pyproject.toml`, proper src layout
- **Web Interface**: Gradio UI for interactive 3D reconstruction (`vggt web`)
- **Enhanced Testing**: Comprehensive test suite with MPS and sparse attention tests
- **Modern Tooling**: UV support, Makefile automation, GitHub Actions CI/CD

### 🚀 Core Features
- **MPS Acceleration**: Full GPU acceleration on Apple Silicon using Metal Performance Shaders
- **⚡ Sparse Attention**: O(n) memory scaling for city-scale reconstruction (100x savings!)
- **🎥 Multi-View 3D Reconstruction**: Generate depth maps, point clouds, and camera poses from images
- **🔧 MCP Integration**: Model Context Protocol server for Claude Desktop integration
- **📦 5GB Model**: Efficient 1B parameter model that runs smoothly on Apple Silicon
- **🛠️ Multiple Export Formats**: PLY, OBJ, GLB for 3D point clouds

## 🎯 What VGGT Does

VGGT reconstructs 3D scenes from images by predicting:
- **Depth Maps**: Per-pixel depth estimation
- **Camera Poses**: 6DOF camera parameters
- **3D Point Clouds**: Dense 3D reconstruction
- **Confidence Maps**: Reliability scores for predictions

## 📋 Requirements

- Apple Silicon Mac (M1/M2/M3)
- Python 3.10+
- 8GB+ RAM
- 6GB disk space for model

## 🚀 Quick Start

### Installation Options

#### Option A: Install from PyPI (Coming Soon)

```bash
# Install from PyPI (when published)
pip install vggt-mps

# Download model weights (5GB)
vggt download
```

#### Option B: Install from Source with UV (Recommended for Development)

```bash
git clone https://github.com/jmanhype/vggt-mps.git
cd vggt-mps

# Install with uv (10-100x faster than pip!)
make install

# Or manually with uv
uv pip install -e .
```

#### Option C: Traditional pip install from Source

```bash
git clone https://github.com/jmanhype/vggt-mps.git
cd vggt-mps

# Create virtual environment
python -m venv vggt-env
source vggt-env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Download Model Weights

```bash
# Download the 5GB VGGT model
vggt download

# Or if running from source:
python main.py download
```

Or manually download from [Hugging Face](https://huggingface.co/facebook/VGGT-1B/resolve/main/model.pt)

### 3. Test MPS Support

```bash
# Test MPS acceleration
vggt test --suite mps

# Or from source:
python main.py test --suite mps
```

Expected output:
```
✅ MPS (Metal Performance Shaders) available!
   Running on Apple Silicon GPU
✅ Model weights loaded to mps
✅ MPS operations working correctly!
```

### 4. Setup Environment (Optional)

```bash
# Copy environment configuration
cp .env.example .env

# Edit .env with your settings
nano .env
```

## 📖 Usage

### CLI Commands (v2.0.0)

All functionality is accessible through the unified `vggt` command:

```bash
# Quick demo with sample images
vggt demo

# Demo with kitchen dataset (4 images)
vggt demo --kitchen --images 4

# Process your own images
vggt reconstruct data/*.jpg

# Use sparse attention for large scenes
vggt reconstruct --sparse data/*.jpg

# Export to specific format
vggt reconstruct --export ply data/*.jpg

# Launch interactive web interface
vggt web

# Open on specific port with public link
vggt web --port 8080 --share

# Run comprehensive tests
vggt test --suite all

# Test sparse attention specifically
vggt test --suite sparse

# Benchmark performance
vggt benchmark --compare

# Download model weights
vggt download
```

### From Source (Development)

If running from source without installation:

```bash
python main.py demo
python main.py reconstruct data/*.jpg
python main.py web
python main.py test --suite mps
python main.py benchmark --compare
```

## 🔧 MCP Server Integration

### Add to Claude Desktop

1. Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vggt-agent": {
      "command": "uv",
      "args": [
        "run",
        "--python",
        "/path/to/vggt-mps/vggt-env/bin/python",
        "--with",
        "fastmcp",
        "fastmcp",
        "run",
        "/path/to/vggt-mps/src/vggt_mps_mcp.py"
      ]
    }
  }
}
```

2. Restart Claude Desktop

### Available MCP Tools

- `vggt_quick_start_inference` - Quick 3D reconstruction from images
- `vggt_extract_video_frames` - Extract frames from video
- `vggt_process_images` - Full VGGT pipeline
- `vggt_create_3d_scene` - Generate GLB 3D files
- `vggt_reconstruct_3d_scene` - Multi-view reconstruction
- `vggt_visualize_reconstruction` - Create visualizations

## 📁 Project Structure

```
vggt-mps/
├── main.py                      # Single entry point
├── setup.py                     # Package installation
├── requirements.txt             # Dependencies
├── .env.example                 # Environment configuration
│
├── src/                         # Source code
│   ├── config.py               # Centralized configuration
│   ├── vggt_core.py            # Core VGGT processing
│   ├── vggt_sparse_attention.py # Sparse attention (O(n) scaling)
│   ├── visualization.py        # 3D visualization utilities
│   │
│   ├── commands/               # CLI commands
│   │   ├── demo.py            # Demo command
│   │   ├── reconstruct.py     # Reconstruction command
│   │   ├── test_runner.py     # Test runner
│   │   ├── benchmark.py       # Performance benchmarking
│   │   └── web_interface.py   # Gradio web app
│   │
│   └── utils/                  # Utilities
│       ├── model_loader.py    # Model management
│       ├── image_utils.py     # Image processing
│       └── export.py          # Export to PLY/OBJ/GLB
│
├── tests/                       # Organized test suite
│   ├── test_mps.py            # MPS functionality tests
│   ├── test_sparse.py         # Sparse attention tests
│   └── test_integration.py    # End-to-end tests
│
├── data/                        # Input data directory
├── outputs/                     # Output directory
├── models/                      # Model storage
│
├── docs/                        # Documentation
│   ├── API.md                  # API documentation
│   ├── SPARSE_ATTENTION.md    # Technical details
│   └── BENCHMARKS.md          # Performance results
│
└── LICENSE                      # MIT License
```

## 🖼️ Usage Examples

### Process Images

```python
from src.tools.readme import vggt_quick_start_inference

result = vggt_quick_start_inference(
    image_directory="./tmp/inputs",
    device="mps",  # Use Apple Silicon GPU
    max_images=4,
    save_outputs=True
)
```

### Extract Video Frames

```python
from src.tools.demo_gradio import vggt_extract_video_frames

result = vggt_extract_video_frames(
    video_path="input_video.mp4",
    frame_interval_seconds=1.0
)
```

### Create 3D Scene

```python
from src.tools.demo_viser import vggt_reconstruct_3d_scene

result = vggt_reconstruct_3d_scene(
    images_dir="./tmp/inputs",
    device_type="mps",
    confidence_threshold=0.5
)
```

## ⚡ Sparse Attention - NEW!

**City-scale 3D reconstruction is now possible!** We've implemented Gabriele Berton's research idea for O(n) memory scaling.

### 🎯 Key Benefits
- **100x memory savings** for 1000 images
- **No retraining required** - patches existing VGGT at runtime
- **Identical outputs** to regular VGGT (0.000000 difference)
- **MegaLoc covisibility** detection for smart attention masking

### 🚀 Usage
```python
from src.vggt_sparse_attention import make_vggt_sparse

# Convert any VGGT to sparse in 1 line
sparse_vggt = make_vggt_sparse(regular_vggt, device="mps")

# Same usage, O(n) memory instead of O(n²)
output = sparse_vggt(images)  # Handles 1000+ images!
```

### 📊 Memory Scaling
| Images | Regular | Sparse | Savings |
|--------|---------|--------|---------|
| 100    | O(10K)  | O(1K)  | **10x** |
| 500    | O(250K) | O(5K)  | **50x** |
| 1000   | O(1M)   | O(10K) | **100x** |

**See full results:** [docs/SPARSE_ATTENTION_RESULTS.md](docs/SPARSE_ATTENTION_RESULTS.md)

## 🔬 Technical Details

### MPS Optimizations

- **Device Detection**: Auto-detects MPS availability
- **Dtype Selection**: Uses float32 for optimal MPS performance
- **Autocast Handling**: CUDA autocast disabled for MPS
- **Memory Management**: Efficient tensor operations on Metal

### Model Architecture

- **Parameters**: 1B (5GB on disk)
- **Input**: Multi-view images
- **Output**: Depth, camera poses, 3D points
- **Resolution**: 518x518 (VGGT), up to 1024x1024 (input)

## 🐛 Troubleshooting

### MPS Not Available

```bash
# Check PyTorch MPS support
python -c "import torch; print(torch.backends.mps.is_available())"
```

### Model Loading Issues

```bash
# Verify model file
ls -lh repo/vggt/vggt_model.pt
# Should show ~5GB file
```

### Memory Issues

- Reduce batch size
- Lower resolution
- Use CPU fallback

## 📚 References

- [VGGT Paper](https://arxiv.org/pdf/2507.04009)
- [Facebook Research VGGT](https://github.com/facebookresearch/vggt)
- [Hugging Face Model](https://huggingface.co/facebook/VGGT-1B)

## 📚 Documentation

- **[Development Guide](DEVELOPMENT.md)** - Setting up your dev environment
- **[Publishing Guide](PUBLISHING.md)** - PyPI release process
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute
- **[API Documentation](docs/)** - Detailed API reference
- **[Examples](examples/)** - Code examples and demos

## 🚀 Release Notes

### v2.0.0 (Latest)
- ✨ Unified CLI with `vggt` command
- 📦 Professional Python packaging (PyPI-ready)
- 🌐 Gradio web interface
- 🧪 Comprehensive test suite
- 🛠️ Modern tooling (UV, Makefile, GitHub Actions)
- 📝 Complete documentation overhaul

See [full changelog](https://github.com/jmanhype/vggt-mps/releases/tag/v2.0.0)

## 🤝 Contributing

We follow a lightweight Git Flow:

- `main` holds the latest stable release and is protected.
- `develop` is the default integration branch for day-to-day work.

When contributing:

1. Create your feature branch from `develop` (`git switch develop && git switch -c feature/my-change`).
2. Keep commits focused and include tests or documentation updates when relevant.
3. Open your pull request against `develop`; maintainers will promote changes to `main` during releases.

Please open issues for bugs or feature requests before starting large efforts. Full details, testing expectations, and the release process live in [`CONTRIBUTING.md`](CONTRIBUTING.md).

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Facebook Research for VGGT
- Apple for Metal Performance Shaders
- PyTorch team for MPS backend

---

**Made with 🍎 for Apple Silicon by the AI community**
