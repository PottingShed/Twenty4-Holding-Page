# Twenty4 holding site

This is a static site with no CMS and no build dependencies. You can upload it as-is to any static host.

```
index.html                 Holding page
policies/index.html        Policies index (generated)
policies/<slug>/index.html Individual policies (generated)
cookies/index.html         Cookies Policy (generated)
content/*.html             Policy wording, pulled verbatim from fort.group/policies
css/site.css               All styles
js/site.js                 Guernsey-time dial, one-shot reveals, pointer light on the 4+
assets/                    Logo, favicon, fonts, Standard Terms PDF
build.py                   Regenerates the policy pages from content/
```

To edit a policy, change the file in `content/`, then run `python3 build.py`.

To preview locally, run `npx http-server -p 8424`.

## Before go-live
- [ ] **Font licences.** Brockmann (headlines) and Eloquia Display (body) are self-hosted as woff2, converted from the studio OTFs. Confirm both licences cover web embedding.
- [ ] **Cookies Policy wording.** Fort has no existing cookies policy, so this is new draft copy and needs client sign-off. Remove the "Draft" line in `content/cookies.html`.
- [ ] **Footer legal line.** Confirm the entity name and registration details after the rebrand.
- [ ] **Policy wording still says "Fort".** For example, hello@fort.group appears in the privacy notice. It was kept verbatim as agreed.
- [ ] **og:image.** Create a 1200×630 share image and add `og:image` / `twitter:image`.
- [ ] **Redirects.** Add 301s from the old fort.group URLs to `/` and to the matching `/policies/*` pages.

## Imagery and film
**Film.** `assets/video/film-1080.mp4` and `film-720.mp4` (3.2MB and 1.4MB) are a 9-second, three-shot edit with hard cuts, cut in AVFoundation. It runs from still water (Adobe Stock 806720292) to waves from a moving boat (Artlist, Marzio Mirabella) to the sail rising (Artlist, "Wind Rope Sky Mast", Daniel Schua). `film-poster.jpg` is the still shown before the film loads. The page plays it at 0.8× speed and loops it on a hard cut. Adobe Stock and Artlist licences confirmed to cover the client (1 Oct 2026).

**Photos.** The principles photographs (`assets/img/principle-watch.webp`, `principle-dash.webp` and `principle-yacht.webp`) were supplied by Potting Shed and are self-hosted. The page shows them in black and white with grain and the blue light. **Confirm the source and licence of each.**
- Sign-off: `assets/seq/d` (desktop, 1440×810) and `assets/seq/m` (phones, portrait crop) are 96 stills from an original 160-frame Blender 5.2 Cycles animation of the 4+ rising from still navy liquid while the camera orbits and settles. They're spaced evenly along the camera's path and graded to the site navy (`source/rise-grade.py`), with grain baked in so the dark gradients don't band. The page draws them to a canvas as you scroll and blends neighbouring frames, so the move glides with no video-seeking stutter. They load only once the visitor scrolls. `assets/img/signoff-1600/1280.webp` is the final frame, used for reduced motion. To re-render, run `/Applications/Blender.app/Contents/MacOS/Blender -b -P source/rise-render.py -- <out_dir> 1600 40 all` (about 35 minutes).

## Still to supply
- [ ] **Service icons.** The three icons (interlocking arcs, stepped bars, offset frames) are original, drawn on a 120-unit grid with a 7-unit stroke and 7-unit gaps. They're in the poster style but aren't copied from any reference. Add them to the master icon set once approved.

## Preview gate (remove at go-live)
The preview is behind a simple password gate (`js/gate.js`), and every page carries `<meta name="robots" content="noindex, nofollow">`. Both are in `index.html` and in the template in `build.py`. The gate stops casual visitors only: the files themselves are public on GitHub Pages. At go-live, remove the gate script tag and the robots meta from `index.html` and `build.py`, run `python3 build.py`, and delete `js/gate.js` plus the "Preview gate" block at the end of `css/site.css`.
