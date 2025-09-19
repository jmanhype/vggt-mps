"""
Export utilities for 3D data
"""

import numpy as np
from pathlib import Path
from typing import Optional


def export_point_cloud(
    points: np.ndarray,
    output_path: Path,
    colors: Optional[np.ndarray] = None,
    format: str = "ply"
):
    """
    Export point cloud to various formats

    Args:
        points: Nx3 array of 3D points
        output_path: Output file path
        colors: Optional Nx3 array of RGB colors
        format: Export format (ply, obj, glb)
    """
    if format == "ply":
        export_ply(points, output_path, colors)
    elif format == "obj":
        export_obj(points, output_path, colors)
    elif format == "glb":
        export_glb(points, output_path, colors)
    else:
        raise ValueError(f"Unsupported format: {format}")


def export_ply(points: np.ndarray, output_path: Path, colors: Optional[np.ndarray] = None):
    """Export point cloud to PLY format"""
    num_points = len(points)

    # Prepare header
    header = [
        "ply",
        "format ascii 1.0",
        f"element vertex {num_points}",
        "property float x",
        "property float y",
        "property float z",
    ]

    if colors is not None:
        header.extend([
            "property uchar red",
            "property uchar green",
            "property uchar blue"
        ])

    header.append("end_header")

    # Write PLY file
    with open(output_path, 'w') as f:
        for line in header:
            f.write(line + '\n')

        for i in range(num_points):
            x, y, z = points[i]
            if colors is not None:
                r, g, b = colors[i]
                f.write(f"{x:.6f} {y:.6f} {z:.6f} {int(r)} {int(g)} {int(b)}\n")
            else:
                # Default gray color
                f.write(f"{x:.6f} {y:.6f} {z:.6f}\n")


def export_obj(points: np.ndarray, output_path: Path, colors: Optional[np.ndarray] = None):
    """Export point cloud to OBJ format"""
    with open(output_path, 'w') as f:
        f.write("# VGGT Point Cloud Export\n")
        f.write(f"# Points: {len(points)}\n\n")

        # Write vertices
        for i, point in enumerate(points):
            x, y, z = point
            if colors is not None:
                r, g, b = colors[i] / 255.0
                f.write(f"v {x:.6f} {y:.6f} {z:.6f} {r:.3f} {g:.3f} {b:.3f}\n")
            else:
                f.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")


def export_glb(points: np.ndarray, output_path: Path, colors: Optional[np.ndarray] = None):
    """
    Export point cloud to GLB format (simplified version)
    For full GLB support, consider using trimesh or pygltflib
    """
    # This is a simplified placeholder
    # For production, use a proper GLTF library
    print(f"⚠️ GLB export not fully implemented. Falling back to PLY format.")
    ply_path = output_path.with_suffix('.ply')
    export_ply(points, ply_path, colors)
    print(f"  Saved as PLY: {ply_path}")


def export_mesh(
    vertices: np.ndarray,
    faces: np.ndarray,
    output_path: Path,
    colors: Optional[np.ndarray] = None,
    format: str = "obj"
):
    """
    Export mesh to various formats

    Args:
        vertices: Nx3 array of vertices
        faces: Mx3 array of face indices
        output_path: Output file path
        colors: Optional Nx3 array of vertex colors
        format: Export format (obj, ply)
    """
    if format == "obj":
        with open(output_path, 'w') as f:
            f.write("# VGGT Mesh Export\n")

            # Write vertices
            for i, v in enumerate(vertices):
                x, y, z = v
                if colors is not None:
                    r, g, b = colors[i] / 255.0
                    f.write(f"v {x:.6f} {y:.6f} {z:.6f} {r:.3f} {g:.3f} {b:.3f}\n")
                else:
                    f.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")

            # Write faces (OBJ uses 1-indexed)
            for face in faces:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

    elif format == "ply":
        # PLY format for mesh
        num_vertices = len(vertices)
        num_faces = len(faces)

        header = [
            "ply",
            "format ascii 1.0",
            f"element vertex {num_vertices}",
            "property float x",
            "property float y",
            "property float z",
        ]

        if colors is not None:
            header.extend([
                "property uchar red",
                "property uchar green",
                "property uchar blue"
            ])

        header.extend([
            f"element face {num_faces}",
            "property list uchar int vertex_indices",
            "end_header"
        ])

        with open(output_path, 'w') as f:
            for line in header:
                f.write(line + '\n')

            # Write vertices
            for i, v in enumerate(vertices):
                x, y, z = v
                if colors is not None:
                    r, g, b = colors[i]
                    f.write(f"{x:.6f} {y:.6f} {z:.6f} {int(r)} {int(g)} {int(b)}\n")
                else:
                    f.write(f"{x:.6f} {y:.6f} {z:.6f}\n")

            # Write faces
            for face in faces:
                f.write(f"3 {face[0]} {face[1]} {face[2]}\n")