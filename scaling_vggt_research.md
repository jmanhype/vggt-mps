# Scaling VGGT Linearly with Masked Attention

## Research Idea from @gabriberton

This is a brilliant approach to scale VGGT from O(n²) to O(n) complexity! The core insight about using covisibility-based attention masking is spot on.

## Implementation Thoughts for vggt-mps

### 1. MegaLoc Integration
```python
def compute_covisibility_mask(images, threshold=0.7):
    """Use MegaLoc features to determine which frames should attend to each other"""
    # Extract MegaLoc features
    features = megaloc_model.extract_features(images)

    # Compute pairwise distances
    distances = compute_pairwise_distances(features)

    # Create attention mask (1 = attend, 0 = mask out)
    mask = distances < threshold

    # Ensure graph connectivity
    mask = ensure_connected_graph(mask)

    return mask
```

### 2. Sparse Attention Implementation on MPS

Metal Performance Shaders could actually be great for this:
- MPS has sparse matrix operations (`MPSMatrixSolveTriangular`, `MPSMatrixMultiplication`)
- Could leverage `MPSGraphSparseOps` for efficient sparse attention
- Metal's SIMD groups work well with block-sparse patterns

### 3. Graph Connectivity Heuristics

Key considerations:
- Minimum degree: Each image should attend to at least k neighbors
- Bridge detection: Prevent graph splitting
- Component merging: Handle multiple scenes gracefully

```python
def ensure_connected_graph(mask, min_connections=3):
    """Ensure the attention graph remains connected"""
    # Add edges to maintain minimum degree
    for i in range(len(mask)):
        connections = mask[i].sum()
        if connections < min_connections:
            # Add nearest neighbors in feature space
            add_nearest_neighbors(mask, i, min_connections)

    # Check for disconnected components
    components = find_connected_components(mask)
    if len(components) > 1:
        # Bridge components with nearest pairs
        bridge_components(mask, components)

    return mask
```

### 4. Adaptive Masking Strategy

For different scene types:
- **Indoor scenes**: Tighter masking (rooms are separate)
- **Outdoor/street**: Looser masking (continuous views)
- **Object-centric**: Radial masking pattern

### 5. Memory Savings Estimation

For n images with k-nearest neighbor attention:
- Original VGGT: O(n²) memory
- Masked VGGT: O(n·k) memory
- Savings: For n=1000, k=10 → 100x memory reduction!

## Implementation Plan for vggt-mps

1. **Phase 1**: Add MegaLoc feature extraction
2. **Phase 2**: Implement sparse attention masks
3. **Phase 3**: Optimize with Metal sparse ops
4. **Phase 4**: Benchmark on large scenes

## Potential Challenges

1. **MPS Sparse Support**: Need to verify Metal's sparse tensor capabilities
2. **Dynamic Masking**: Mask patterns change per batch
3. **Gradient Flow**: Ensure masked attention doesn't break backprop

## Testing Strategy

```python
# Test scalability
for num_images in [10, 100, 1000, 10000]:
    memory_original = measure_memory(vggt_original, num_images)
    memory_masked = measure_memory(vggt_masked, num_images)
    print(f"Images: {num_images}, Savings: {memory_original/memory_masked:.2f}x")
```

## Next Steps

1. Port MegaLoc to MPS
2. Modify VGGT attention layers for masking
3. Implement graph connectivity checks
4. Benchmark on real large-scale scenes

This could genuinely make VGGT practical for city-scale reconstruction on consumer hardware!

## References

- [1] VGGT: https://arxiv.org/abs/2503.11651
- [2] VGGT-Long: https://arxiv.org/abs/2507.16443
- [3] MegaLoc: https://arxiv.org/abs/2404.15882

---

*Inspired by @gabriberton's research idea thread*