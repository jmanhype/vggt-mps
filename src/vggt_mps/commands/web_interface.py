"""
Web interface command for VGGT-MPS using Gradio
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import WEB_CONFIG


def launch_web_interface(args):
    """Launch Gradio web interface"""
    print("=" * 60)
    print("🌐 VGGT Web Interface")
    print("=" * 60)

    try:
        import gradio as gr
    except ImportError:
        print("❌ Gradio not installed!")
        print("Run: pip install gradio")
        return 1

    import numpy as np
    from PIL import Image
    from vggt_core import VGGTProcessor
    from vggt_sparse_attention import make_vggt_sparse
    from visualization import create_visualizations
    from config import DEVICE, SPARSE_CONFIG, OUTPUT_DIR

    # Initialize processor
    processor = VGGTProcessor(device=DEVICE)

    def process_images(images, use_sparse, covis_threshold):
        """Process uploaded images through VGGT"""
        if not images:
            return None, None, "Please upload images"

        # Convert images to numpy arrays
        img_arrays = []
        for img in images:
            if isinstance(img, str):
                img = Image.open(img)
            img_arrays.append(np.array(img))

        # Apply sparse attention if requested
        if use_sparse:
            processor.model = make_vggt_sparse(
                processor.model,
                device=DEVICE,
                threshold=covis_threshold
            ) if processor.model else None

        # Process images
        try:
            results = processor.process_images(img_arrays)

            # Create visualizations
            output_dir = OUTPUT_DIR / "web_output"
            output_dir.mkdir(parents=True, exist_ok=True)

            if isinstance(results, dict):
                depth_maps = results.get('depth_maps', [])
            else:
                depth_maps = results

            viz_files = create_visualizations(
                img_arrays, depth_maps, output_dir
            )

            # Load visualization images
            input_viz = str(output_dir / "input_views.png")
            depth_viz = str(output_dir / "depth_maps.png")

            status = f"✅ Processed {len(images)} images successfully"
            if use_sparse:
                status += f" (Sparse mode, threshold: {covis_threshold})"

            return input_viz, depth_viz, status

        except Exception as e:
            return None, None, f"❌ Error: {str(e)}"

    # Create Gradio interface
    with gr.Blocks(title="VGGT 3D Reconstruction", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🚀 VGGT 3D Reconstruction on Apple Silicon
        ### Transform multi-view images into 3D reconstructions with MPS acceleration
        """)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Input Settings")
                image_input = gr.File(
                    label="Upload Images",
                    file_count="multiple",
                    file_types=["image"]
                )
                use_sparse = gr.Checkbox(
                    label="Use Sparse Attention (O(n) scaling)",
                    value=False
                )
                covis_threshold = gr.Slider(
                    label="Covisibility Threshold",
                    minimum=0.1,
                    maximum=1.0,
                    value=SPARSE_CONFIG["covisibility_threshold"],
                    step=0.1,
                    visible=False
                )
                process_btn = gr.Button("🔮 Run Reconstruction", variant="primary")

            with gr.Column(scale=2):
                gr.Markdown("### Results")
                status = gr.Textbox(label="Status", interactive=False)
                with gr.Row():
                    input_viz = gr.Image(label="Input Views", type="filepath")
                    depth_viz = gr.Image(label="Depth Maps", type="filepath")

        # Toggle covisibility slider
        use_sparse.change(
            fn=lambda x: gr.update(visible=x),
            inputs=use_sparse,
            outputs=covis_threshold
        )

        # Process button
        process_btn.click(
            fn=process_images,
            inputs=[image_input, use_sparse, covis_threshold],
            outputs=[input_viz, depth_viz, status]
        )

        gr.Markdown("""
        ### Features:
        - ⚡ **MPS Acceleration** - Optimized for Apple Silicon
        - 🔄 **Sparse Attention** - O(n) memory scaling for large scenes
        - 📊 **Depth Estimation** - Per-pixel depth maps
        - 🎯 **3D Reconstruction** - Point clouds from multi-view images
        """)

    # Launch interface
    port = args.port if hasattr(args, 'port') else WEB_CONFIG["default_port"]
    share = args.share if hasattr(args, 'share') else WEB_CONFIG["share"]

    print(f"Starting web interface on port {port}...")
    if share:
        print("Creating public share link...")

    demo.launch(
        server_port=port,
        share=share,
        show_error=True
    )

    return 0