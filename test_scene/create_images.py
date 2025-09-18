#!/usr/bin/env python3
"""
Generate test images for VGGT 3D reconstruction
"""
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os

# Set output directory
output_dir = "/Users/speed/Downloads/Paper2Agent/VGGT_Agent/test_scene/images"

# Generate 8 different viewpoints of a 3D scene
num_views = 8
angles = np.linspace(0, 360, num_views, endpoint=False)

print(f"Creating {num_views} test images for VGGT...")

for i, angle in enumerate(angles):
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Create a colorful cube
    r = [0, 1]
    X, Y = np.meshgrid(r, r)
    
    # Six faces with different colors
    ax.plot_surface(X, Y, np.zeros_like(X), alpha=0.8, color='red')      # bottom
    ax.plot_surface(X, Y, np.ones_like(X), alpha=0.8, color='blue')      # top
    ax.plot_surface(X, np.zeros_like(X), Y, alpha=0.8, color='green')    # front
    ax.plot_surface(X, np.ones_like(X), Y, alpha=0.8, color='yellow')    # back
    ax.plot_surface(np.zeros_like(X), X, Y, alpha=0.8, color='cyan')     # left
    ax.plot_surface(np.ones_like(X), X, Y, alpha=0.8, color='magenta')   # right
    
    # Add a sphere for complexity
    u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
    x = 0.25 * np.cos(u) * np.sin(v) + 1.5
    y = 0.25 * np.sin(u) * np.sin(v) + 0.5  
    z = 0.25 * np.cos(v) + 0.5
    ax.plot_surface(x, y, z, color='orange', alpha=0.9)
    
    # Add a pyramid
    pyramid_x = [0.5, 0.8, 0.8, 0.2, 0.2, 0.5]
    pyramid_y = [1.5, 1.3, 1.7, 1.7, 1.3, 1.5]
    pyramid_z = [1.5, 1.0, 1.0, 1.0, 1.0, 1.5]
    
    # Draw pyramid edges
    for j in range(4):
        ax.plot([pyramid_x[j+1], pyramid_x[0]], 
                [pyramid_y[j+1], pyramid_y[0]], 
                [pyramid_z[j+1], pyramid_z[0]], 'k-', linewidth=2)
    
    # Set view angle
    ax.view_init(elev=25, azim=angle)
    
    # Set axis properties
    ax.set_xlim([-0.5, 2])
    ax.set_ylim([-0.5, 2])
    ax.set_zlim([0, 2])
    ax.set_xlabel('X')
    ax.set_ylabel('Y') 
    ax.set_zlabel('Z')
    ax.set_title(f'View {i+1} - Azimuth: {angle:.0f}°')
    
    # Save image
    output_path = os.path.join(output_dir, f'view_{i+1:03d}.jpg')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  Created: view_{i+1:03d}.jpg")

print(f"\n✅ Successfully created {num_views} images in:")
print(f"   {output_dir}")
print("\nReady for VGGT 3D reconstruction!")
