#!/usr/bin/env python3
import json
import subprocess
import sys

def call_mcp_tool(tool_name, params):
    """Call an MCP tool through the server"""
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": params
        },
        "id": 1
    }
    
    # Start the MCP server and send request
    cmd = [
        "uv", "run", 
        "--python", "/Users/speed/Downloads/Paper2Agent/VGGT_Agent/repo/vggt-env/bin/python",
        "--with", "fastmcp",
        "/Users/speed/Downloads/Paper2Agent/VGGT_Agent/src/paper2agent_mcp.py"
    ]
    
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send request and get response
    stdout, stderr = proc.communicate(input=json.dumps(request))
    
    # Parse response
    for line in stdout.split('\n'):
        if line.strip() and line.startswith('{'):
            try:
                response = json.loads(line)
                if 'result' in response:
                    return response['result']
            except json.JSONDecodeError:
                continue
    
    return {"error": "No valid response received", "stderr": stderr}

# Test the VGGT inference
print("Testing VGGT Quick Start Inference...")
print("="*50)

result = call_mcp_tool("vggt_quick_start_inference", {
    "image_directory": "/Users/speed/Downloads/Paper2Agent/VGGT_Agent/tmp/inputs",
    "image_format": "jpg",
    "model_id": "vggt",
    "output_directory": "/Users/speed/Downloads/Paper2Agent/VGGT_Agent/tmp/outputs",
    "max_images": 3,
    "save_outputs": True
})

print(json.dumps(result, indent=2))
