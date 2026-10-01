# Brand grade: darker, blacks lifted to the page navy, liquid sheen tamed, highlights on the 4+ kept
import sys, os, numpy as np
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]; only = sys.argv[3].split(',') if len(sys.argv) > 3 else None
os.makedirs(dst, exist_ok=True)
navy = np.array([5, 11, 31], np.float32) / 255
rng = np.random.default_rng(24); noise = None
for f in sorted(x for x in os.listdir(src) if x.endswith('.png')):
    if only and f not in only: continue
    a = np.asarray(Image.open(os.path.join(src, f)).convert('RGB')).astype(np.float32) / 255
    lum = (a * [0.2126, 0.7152, 0.0722]).sum(2, keepdims=True)
    a = lum + (a - lum) * 0.82                       # a touch less saturated
    a = np.power(np.clip(a, 0, 1), 1.35) * 0.78      # deeper midtones, lower exposure
    hi = np.clip((lum - 0.45) / 0.4, 0, 1)           # protect the 4+'s specular edges
    a = a * (1 - hi * 0.25) + np.power(np.clip(a, 0, 1), 0.85) * hi * 0.25
    a = navy + (1 - navy) * a                        # blacks become exactly the page navy
    a = a * 255
    if noise is None: noise = rng.normal(0, 1.6, a.shape[:2]).astype(np.float32)[..., None]
    a = a + noise * (1.0 - 0.6 * lum) + rng.uniform(-0.5, 0.5, a.shape)
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(os.path.join(dst, f), compress_level=1)
print('graded')
