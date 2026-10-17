import torch
import time

print("PyTorch:", torch.__version__)
print("GPU available:", torch.cuda.is_available())

device = torch.device("cuda")

# Create vectors directly on GPU
a = torch.randn(10_000_000, device=device, dtype=torch.float32)
b = torch.randn(10_000_000, device=device, dtype=torch.float32)

# Warm-up
for _ in range(10):
    torch.dot(a, b)

torch.cuda.synchronize()

# Benchmark
start = time.perf_counter()

result = torch.dot(a, b)

torch.cuda.synchronize()
elapsed = time.perf_counter() - start

print("GPU:", torch.cuda.get_device_name(0))
print("Dot product:", result.item())
print(f"Time: {elapsed * 1000:.3f} ms")