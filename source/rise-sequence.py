# 96 stills from the graded frames, evenly spaced (the shot now moves at one even pace)
import sys, os
from PIL import Image
src, site = sys.argv[1], sys.argv[2]
N = 96; F0, F1 = 10, 120
for d in ('d', 'm'): os.makedirs(os.path.join(site, 'assets/seq', d), exist_ok=True)
for i in range(N):
    f = round(F0 + (F1 - F0) * i / (N - 1))
    im = Image.open(os.path.join(src, 'f%03d.png' % f)).convert('RGB')
    im.resize((1440, 810), Image.LANCZOS).save(os.path.join(site, 'assets/seq/d/%02d.webp' % i), quality=76, method=6)
    w = round(900 * 9 / 16); cx = int(1600 * 0.7); x0 = max(0, min(1600 - w, cx - w // 2))
    im.crop((x0, 0, x0 + w, 900)).save(os.path.join(site, 'assets/seq/m/%02d.webp' % i), quality=76, method=6)
last = Image.open(os.path.join(src, 'f120.png')).convert('RGB')
last.save(os.path.join(site, 'assets/img/signoff-1600.webp'), quality=90, method=6)
last.resize((1280, 720), Image.LANCZOS).save(os.path.join(site, 'assets/img/signoff-1280.webp'), quality=88, method=6)
print('sequence built')
