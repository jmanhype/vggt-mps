# VGGT-MPS: 3D Vision Agent for Apple Silicon

🍎 **VGGT (Visual Geometry Grounded Transformer) optimized for Apple Silicon with Metal Performance Shaders (MPS)**

Transform single or multi-view images into rich 3D reconstructions using Facebook Research's VGGT model, now accelerated on M1/M2/M3 Macs.

## ✨ Features

- **🚀 MPS Acceleration**: Full GPU acceleration on Apple Silicon using Metal Performance Shaders
- **⚡ Sparse Attention**: O(n) memory scaling for city-scale reconstruction (100x savings!)
- **🎥 Multi-View 3D Reconstruction**: Generate depth maps, point clouds, and camera poses from images
- **🔧 MCP Integration**: Model Context Protocol server for Claude Desktop integration
- **📦 5GB Model**: Efficient 1B parameter model that runs smoothly on Apple Silicon
- **🛠️ Multiple Tools**: Video processing, 3D scene generation, COLMAP integration

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

### 1. Clone and Setup

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
python scripts/download_model.py
```

Or manually download from [Hugging Face](https://huggingface.co/facebook/VGGT-1B/resolve/main/model.pt)

### 3. Test MPS Support

```bash
python tests/test_vggt_mps.py
```

Expected output:
```
✅ MPS (Metal Performance Shaders) available!
   Running on Apple Silicon GPU
✅ Model weights loaded to mps
✅ MPS operations working correctly!
```

### 4. Run Demo

```bash
# Create test images
python examples/create_test_images.py

# Run 3D reconstruction demo
python examples/demo_vggt_mps.py

# Test sparse attention (O(n) scaling)
python tests/sparse_attention/test_sparse_vggt_final.py
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
├── src/                         # Source code
│   ├── vggt_mps_mcp.py         # MCP server
│   └── tools/                   # VGGT tools (11 total)
│       ├── readme.py           # Quick inference
│       ├── demo_gradio.py      # Video & 3D tools
│       ├── demo_viser.py       # Visualization
│       └── demo_colmap.py      # COLMAP integration
├── examples/                    # Example scripts
│   ├── demo_vggt_mps.py       # Main demo
│   ├── create_test_images.py  # Generate test data
│   └── vggt_mps_inference.py  # Direct inference
├── tests/                       # Test scripts
│   ├── test_vggt_mps.py       # MPS test
│   └── test_hub_load.py       # Hub loading test
├── scripts/                     # Utility scripts
│   └── download_model.py      # Model downloader
├── repo/vggt/                   # VGGT source
│   ├── hubconf.py              # Torch hub config
│   └── vggt_model.pt          # Model (5GB)
├── tmp/                         # Working directory
│   ├── inputs/                 # Input images
│   └── outputs/                # Results
├── requirements.txt             # Dependencies
├── README.md                    # Documentation
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

## 🤝 Contributing

We now use a `develop` integration branch. Branch from `develop`, keep changes focused, and open pull requests back into it. Maintainers periodically sync `develop` to `main` during releases. Please open an issue first for larger changes or new features.

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Facebook Research for VGGT
- Apple for Metal Performance Shaders
- PyTorch team for MPS backend

---

**Made with 🍎 for Apple Silicon by the AI community**
