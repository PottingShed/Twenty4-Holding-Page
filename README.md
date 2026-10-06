# Twenty4 holding site

This is a static site with no CMS and no build dependencies. You can upload it as-is to any static host.

```
index.html                 Holding page
policies/index.html        Policies index (generated)
policies/<slug>/index.html Individual policies (generated)
cookies/index.html         Cookies Policy (generated)
404.html                   Page not found (generated; root-absolute links, so it only styles correctly on the live domain)
sitemap.xml                Sitemap (generated)
robots.txt                 Allows all crawlers and points to the sitemap
content/*.html             Policy wording, pulled verbatim from fort.group/policies
css/site.css               All styles
js/site.js                 Guernsey-time dial, one-shot reveals, pointer light on the 4+
assets/                    Logo, favicon, fonts, Standard Terms PDF
build.py                   Regenerates the policy pages, 404 and sitemap from content/
```

To edit a policy, change the file in `content/`, then run `python3 build.py`. Each policy's meta description lives next to its title in `build.py`. Canonical URLs and the sitemap use `SITE` in `build.py` (`https://www.twenty4.group/`); the Organization JSON-LD in `index.html` uses the same domain.

To preview locally, run `npx http-server -p 8424`.

## Before go-live
- [ ] **Font licences.** Brockmann (headlines) and Eloquia Display (body) are self-hosted as woff2, converted from the studio OTFs. Confirm both licences cover web embedding.
- [ ] **Cookies Policy wording.** Fort has no existing cookies policy, so this is new draft copy and needs client sign-off. Remove the "Draft" line in `content/cookies.html`.
- [ ] **Footer legal line.** Confirm the entity name and registration details after the rebrand.
- [ ] **Policy wording still says "Fort".** For example, hello@fort.group appears in the privacy notice. It was kept verbatim as agreed.
- [x] **og:image.** `assets/og-image.jpg` (1200×630, cropped from the sign-off still) is set on every page.
- [ ] **Redirects.** Add 301s from the old fort.group URLs to `/` and to the matching `/policies/*` pages.

## Imagery and film
**Film.** `assets/video/film-1080.mp4` and `film-720.mp4` (3.2MB and 1.4MB) are a 9-second, three-shot edit with hard cuts, cut in AVFoundation. It runs from still water (Adobe Stock 806720292) to waves from a moving boat (Artlist, Marzio Mirabella) to the sail rising (Artlist, "Wind Rope Sky Mast", Daniel Schua). `film-poster.jpg` is the still shown before the film loads. The page plays it at 0.8× speed and loops it on a hard cut. Adobe Stock and Artlist licences confirmed to cover the client (1 Oct 2026).

**Photos.** The principles photographs (`assets/img/principle-watch.webp`, `principle-dash.webp` and `principle-yacht.webp`) were supplied by Potting Shed and are self-hosted. The page shows them in black and white with grain and the blue light. **Confirm the source and licence of each.**
- Sign-off: two original Blender 5.2 Cycles shots, locked off on the 4+. `assets/video/rise-1600/960.mp4` (4s) plays once as the section arrives: the 4+ rises from just beneath still navy liquid and settles. It then cross-fades into `float-1600/960.mp4` (4s), a seamless loop of the mark floating with fine rings drifting out. The ripples are simulated by a wave-equation solver in which the 4+ is a solid obstacle pushing rings out from its edges. The loop is rendered after the sim settles into a steady rhythm, so its last frame flows into its first. Both are graded to the site navy with grain (`source/rise-grade.py`). They load only once the visitor scrolls, and pause off screen. `assets/img/signoff-1600/1280.webp` is the final frame, used for reduced motion. To re-render, run `/Applications/Blender.app/Contents/MacOS/Blender -b -P source/rise-render.py -- <out_dir> 1600 48 all` and `source/float-render.py` with the same arguments (about 30 and 25 minutes).

## Still to supply
- [ ] **Service icons.** The three icons (interlocking arcs, stepped bars, offset frames) are original, drawn on a 120-unit grid with a 7-unit stroke and 7-unit gaps. They're in the poster style but aren't copied from any reference. Add them to the master icon set once approved.

## Preview gate (remove at go-live)
The preview is behind a simple password gate (`js/gate.js`), and every page carries `<meta name="robots" content="noindex, nofollow">`. Both are in `index.html` and in the template in `build.py`. The gate stops casual visitors only: the files themselves are public on GitHub Pages. At go-live, remove the gate script tag and the robots meta from `index.html` and `build.py`, run `python3 build.py`, and delete `js/gate.js` plus the "Preview gate" block at the end of `css/site.css`.
