"""
Model Context Protocol (MCP) for paper2agent

Paper2Agent is a framework for automated code generation from academic papers and tutorials. This repository contains tools for extracting, analyzing, and implementing methods from research papers, with specific focus on VGGT (Visual Geometry Grounded Transformer) for 3D reconstruction.

This MCP Server contains tools extracted from the following tutorial files:
1. readme
    - vggt_quick_start_inference: Quick start inference with VGGT model
    - vggt_alt_loading: Alternative model loading using HuggingFace
    - vggt_detailed_component_predictions: Detailed predictions with all components
    - vggt_depth_visualization: Visualize depth predictions
    - vggt_track_visualization: Visualize track predictions
2. demo_viser
    - vggt_reconstruction_3d: Perform 3D reconstruction from images
    - vggt_visualize_reconstruction: Visualize 3D reconstruction results
3. demo_gradio
    - vggt_gradio_inference: Run VGGT inference for Gradio interface
    - vggt_gradio_postprocess: Post-process VGGT outputs for visualization
4. demo_colmap
    - vggt_colmap_export: Export VGGT results to COLMAP format
"""

from fastmcp import FastMCP

# Import statements (alphabetical order)
from tools.demo_colmap import demo_colmap_mcp
from tools.demo_gradio import demo_gradio_mcp
from tools.demo_viser import demo_viser_mcp
from tools.readme import readme_mcp

# Server definition and mounting
mcp = FastMCP(name="paper2agent")
mcp.mount(demo_colmap_mcp)
mcp.mount(demo_gradio_mcp)
mcp.mount(demo_viser_mcp)
mcp.mount(readme_mcp)

if __name__ == "__main__":
    mcp.run()