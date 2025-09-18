"""
Model Context Protocol (MCP) for AlphaPOP

AlphaPOP is a tool for predicting the functional impact of genetic variants in human and mouse genomes.
It uses a combination of machine learning models and genomic features to predict the impact of variants on gene expression, splicing, and chromatin accessibility.

This MCP Server contains the tools extracted from the following tutorials with their features:
1. score_batch
    - score_batch_variants: Score genetic variants across multiple regulatory modalities using AlphaPOP
"""

import sys
from pathlib import Path
from fastmcp import FastMCP

# Import the MCP tools from the tools folder
from tools.score_batch import score_batch_mcp

# Define the MCP server
mcp = FastMCP(name = "AlphaPOP")

# Mount the tools
mcp.mount(score_batch_mcp)

# Run the MCP server
if __name__ == "__main__":
  mcp.run(transport="http", host="127.0.0.1", port=8003)