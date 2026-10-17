import torch
import time

device = "cuda"

N = 4096

A = torch.randn(N, N, device=device, dtype=torch.float32)
B = torch.randn(N, N, device=device, dtype=torch.float32)

# Warm-up
for _ in range(10):
    C = torch.matmul(A, B)

torch.cuda.synchronize()

iterations = 20

start = time.perf_counter()

for _ in range(iterations):
    C = torch.matmul(A, B)

torch.cuda.synchronize()

elapsed = time.perf_counter() - start

avg_time = elapsed / iterations

# Matrix multiplication:
# 2 * N^3 FLOPs
flops = 2 * N**3
tflops = flops / avg_time / 1e12

print("GPU:", torch.cuda.get_device_name(0))
print(f"Matrix: {N} x {N}")
print(f"Average time: {avg_time * 1000:.3f} ms")
print(f"Performance: {tflops:.2f} TFLOPS")
print("Result shape:", C.shape)