import bpy, math, math, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--')+1:]
OUT = argv[0]; W = int(argv[1]); SAMPLES = int(argv[2]); FR = argv[3]
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.fps = 30; scn.frame_start = 1; scn.frame_end = 120

def curves_of(ob):
    ad = ob.animation_data; act = ad.action if ad else None; cs = []
    if act is None: return cs
    if hasattr(act, 'fcurves'): cs = list(act.fcurves)
    if not cs and hasattr(act, 'layers'):
        for ly in act.layers:
            for st in ly.strips:
                for cb in st.channelbags: cs += list(cb.fcurves)
    return cs
def smooth(ob):  # one continuous bezier per channel, flat at every key: no kinks, unhurried ends
    for fc in curves_of(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'; kp.handle_left_type = 'AUTO_CLAMPED'; kp.handle_right_type = 'AUTO_CLAMPED'
        fc.update()

def ease(fc_owner, interp='QUINT', easing='EASE_IN_OUT'):
    ad = fc_owner.animation_data
    if not ad or not ad.action: return
    act = ad.action
    curves = []
    if hasattr(act, 'fcurves'): curves = list(act.fcurves)
    if not curves and hasattr(act, 'layers'):
        for ly in act.layers:
            for st in ly.strips:
                for cb in st.channelbags: curves += list(cb.fcurves)
    for fc in curves:
        for kp in fc.keyframe_points: kp.interpolation = interp; kp.easing = easing

# ---------- materials ----------
def anodised():
    m = bpy.data.materials.new('MAT_anodised'); m.use_nodes = True
    N = m.node_tree.nodes; L = m.node_tree.links; b = N['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.012, 0.075, 0.55, 1)     # richer, more saturated brand blue
    b.inputs['Metallic'].default_value = 0.9
    b.inputs['Roughness'].default_value = 0.3
    b.inputs['Coat Weight'].default_value = 0.35; b.inputs['Coat Roughness'].default_value = 0.08
    tc = N.new('ShaderNodeTexCoord'); g = N.new('ShaderNodeTexNoise'); g.inputs['Scale'].default_value = 1600; g.inputs['Detail'].default_value = 2
    L.new(tc.outputs['Object'], g.inputs['Vector'])
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.06; bp.inputs['Distance'].default_value = 0.001
    L.new(g.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m
lm = bpy.data.materials.new('MAT_liquid'); lm.use_nodes = True
lb = lm.node_tree.nodes['Principled BSDF']
lb.inputs['Base Color'].default_value = (0.001, 0.004, 0.018, 1); lb.inputs['Roughness'].default_value = 0.045; lb.inputs['Specular IOR Level'].default_value = 0.6

# ---------- liquid: a finely tessellated sim surface around the mark, on a wide calm plane ----------
import bmesh
SIM_N = int(os.environ.get('SIM_N', '560'))
gm = bpy.data.meshes.new('liquid'); bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=SIM_N, y_segments=SIM_N, size=2.5); bm.to_mesh(gm); bm.free()
liq = bpy.data.objects.new('ENV_liquid', gm); scn.collection.objects.link(liq); liq.data.materials.append(lm)
liq.location = (0.35, 0.6, 0.0)
for p in liq.data.polygons: p.use_smooth = True
S = 9.0
om = bpy.data.meshes.new('liquid_far'); om.from_pydata([(-S,-S,0),(S,-S,0),(S,S,0),(-S,S,0)], [], [[0,1,2,3]]); om.update()
far = bpy.data.objects.new('ENV_liquid_far', om); scn.collection.objects.link(far); far.data.materials.append(lm); far.location.z = -0.035

# ---------- the 4+ ----------
plus = [(850.4,91),(811.9,91),(811.9,52.5),(788.5,52.5),(788.5,91),(750,91),(750,114.4),(788.5,114.4),(788.5,152.9),(811.9,152.9),(811.9,114.4),(850.4,114.4)]
diag = [(770.1,0),(705.4,90.9),(705.4,114.3),(718.1,114.3),(790.1,9.4),(790.1,0)]
cx, cy, k = 777.9, 76.5, 0.0095
def P(p): return [((x-cx)*k, -(y-cy)*k, 0.0) for x,y in p]
v1, v2 = P(plus), P(diag)
fm = bpy.data.meshes.new('four'); fm.from_pydata(v1+v2, [], [list(range(len(v1))), list(range(len(v1), len(v1)+len(v2)))]); fm.update()
four = bpy.data.objects.new('HERO_four', fm); scn.collection.objects.link(four)
f1 = four.modifiers.new('raise', 'SOLIDIFY'); f1.thickness = 0.14; f1.offset = 1
f2 = four.modifiers.new('edge', 'BEVEL'); f2.width = 0.01; f2.segments = 6; f2.limit_method = 'ANGLE'; f2.harden_normals = True
four.data.materials.append(anodised())
for p in four.data.polygons: p.use_smooth = True
four.location = (0.35, 0.30, -0.165); four.keyframe_insert('location', index=2, frame=1)
four.keyframe_insert('location', index=2, frame=8)
four.location.z = 0.004; four.keyframe_insert('location', index=2, frame=94)
four.location.z = 0.0; four.keyframe_insert('location', index=2, frame=120)
smooth(four)   # rises from just under the surface, floats a hair proud, settles

# ---------- ripples: our own wave-equation sim; the 4+ is a solid obstacle that pushes rings out from its edges ----------
import numpy as np
G = SIM_N + 1; DX = 5.0 / SIM_N
co = np.empty(len(liq.data.vertices) * 3, np.float32); liq.data.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
IX = np.clip(np.round((co[:, 0] + 2.5) / DX).astype(int), 0, SIM_N); IY = np.clip(np.round((co[:, 1] + 2.5) / DX).astype(int), 0, SIM_N)
gx = (np.arange(G) * DX - 2.5) + liq.location.x; gy = (np.arange(G) * DX - 2.5) + liq.location.y
GX, GY = np.meshgrid(gx, gy)          # world xy of each sim cell, indexed [iy, ix]
def inside(poly, X, Y):
    res = np.zeros(X.shape, bool); n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        c = ((y1 > Y) != (y2 > Y)) & (X < (x2 - x1) * (Y - y1) / (y2 - y1 + 1e-12) + x1); res ^= c
    return res
fx, fy = four.location.x, four.location.y
mask = inside([(fx + p[0], fy + p[1]) for p in v1], GX, GY) | inside([(fx + p[0], fy + p[1]) for p in v2], GX, GY)
def dil(m, r):
    out = m.copy()
    for _ in range(r):
        o = out.copy(); o[1:] |= out[:-1]; o[:-1] |= out[1:]; o[:, 1:] |= out[:, :-1]; o[:, :-1] |= out[:, 1:]; out = o
    return out
edge = dil(mask, 3) & ~mask                       # the band of liquid touching the walls
dist = np.hypot(GX - 0.35, GY - 0.6); fade = np.clip((2.45 - dist) / 0.5, 0, 1)   # waves die before the sim's edge
H = np.zeros((G, G), np.float32); Hp = H.copy()
C2 = 0.22; SUB = int(os.environ.get('R_SUB', '5')); DAMP = float(os.environ.get('R_DAMP', '0.9955')); AMP = float(os.environ.get('R_AMP', '0.0007'))
z_prev = None
def ripple_step(frame):
    global H, Hp, z_prev
    zt = four.matrix_world.translation.z; v = 0.0 if z_prev is None else (zt - z_prev); z_prev = zt
    wet = (zt + 0.14 > 0) and (zt < 0.01)          # only while the mark is passing through the surface
    for _ in range(SUB):
        L = (np.roll(H, 1, 0) + np.roll(H, -1, 0) + np.roll(H, 1, 1) + np.roll(H, -1, 1) - 4 * H)
        Hn = (2 * H - Hp + C2 * L) * DAMP
        if wet: Hn[edge] += AMP * (v / 0.003) / SUB      # rising displaces liquid outward from every edge
        Hn[mask] = 0.0                                   # solid: rings reflect off the 4+'s walls
        Hn *= fade
        Hp, H = H, Hn
    Hs = (H * 4 + np.roll(H, 1, 0) + np.roll(H, -1, 0) + np.roll(H, 1, 1) + np.roll(H, -1, 1)) / 8   # silky
    z = Hs[IY, IX]; c2 = co.copy(); c2[:, 2] = z
    liq.data.vertices.foreach_set('co', c2.ravel()); liq.data.update()
lsub = liq.modifiers.new('smooth', 'SUBSURF'); lsub.levels = 1; lsub.render_levels = 2   # after the sim: silky surface

# ---------- world: deep falloff with a cool horizon for the liquid to mirror ----------
w = bpy.data.worlds.new('W'); scn.world = w; w.use_nodes = True
WN = w.node_tree.nodes; WL = w.node_tree.links; bg = WN['Background']; bg.inputs['Strength'].default_value = 1.0
wtc = WN.new('ShaderNodeTexCoord'); wsep = WN.new('ShaderNodeSeparateXYZ'); wmr = WN.new('ShaderNodeMapRange')
wmr.inputs['From Min'].default_value = -0.02; wmr.inputs['From Max'].default_value = 0.4
wr = WN.new('ShaderNodeValToRGB'); wr.color_ramp.elements[0].color = (0.05, 0.16, 0.6, 1); wr.color_ramp.elements[1].color = (0.0, 0.002, 0.008, 1)
WL.new(wtc.outputs['Generated'], wsep.inputs[0]); WL.new(wsep.outputs['Z'], wmr.inputs['Value']); WL.new(wmr.outputs['Result'], wr.inputs['Fac']); WL.new(wr.outputs['Color'], bg.inputs['Color'])

def area(name, loc, target, size, energy, color, shape='SQUARE', size_y=None):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.color = color; ld.shape = shape; ld.size = size
    if size_y: ld.size_y = size_y
    lo = bpy.data.objects.new(name, ld); scn.collection.objects.link(lo); lo.location = loc
    lo.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    try: ld.cycles.is_caustics_light = False
    except Exception: pass
    lo.visible_camera = False
    lo.visible_glossy = False
area('LGT_key', (4.5, 4.0, 3.4), (0.35, 0.3, 0), 3.5, 900, (0.7, 0.82, 1.0))
area('LGT_rim_a', (-3.5, 3.8, 0.7), (0.35, 0.3, 0.05), 0.35, 3200, (0.55, 0.85, 1.0), 'RECTANGLE', 5)   # rim strip behind-left: traces the bevels
area('LGT_rim_b', (3.8, -2.2, 0.5), (0.35, 0.3, 0.05), 0.3, 2200, (0.5, 0.8, 1.0), 'RECTANGLE', 4)     # rim strip front-right
area('LGT_top', (0.35, 0.3, 4.0), (0.35, 0.3, 0), 2.2, 220, (0.45, 0.6, 1.0))

card_m = bpy.data.materials.new('MAT_card'); card_m.use_nodes = True
cn = card_m.node_tree.nodes; cn.remove(cn['Principled BSDF']); em = cn.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 22.0; em.inputs['Color'].default_value = (0.55, 0.78, 1.0, 1)
card_m.node_tree.links.new(em.outputs[0], cn['Material Output'].inputs[0])
def card(name, loc, rot, sx, sy):
    cm = bpy.data.meshes.new(name); cm.from_pydata([(-sx,-sy,0),(sx,-sy,0),(sx,sy,0),(-sx,sy,0)], [], [[0,1,2,3]]); cm.update()
    co_ = bpy.data.objects.new(name, cm); scn.collection.objects.link(co_); co_.location = loc; co_.rotation_euler = rot; co_.data.materials.append(card_m)
    co_.visible_camera = False
    return co_
def strip(name, loc, rot, sx, sy, w):  # area lights, not geometry: they light the 4+ but can't block a reflection
    ld = bpy.data.lights.new(name, 'AREA'); ld.shape = 'RECTANGLE'; ld.size = sx; ld.size_y = sy; ld.energy = w; ld.color = (0.55, 0.78, 1.0)
    lo = bpy.data.objects.new(name, ld); scn.collection.objects.link(lo); lo.location = loc; lo.rotation_euler = rot
    lo.visible_camera = False
    return lo
rc = strip('LGT_rimstrip', (0.3, 2.6, 1.2), (math.radians(75 + 180), 0, 0), 6.0, 0.16, 70)
sc = strip('LGT_sidestrip', (-2.4, 0.2, 0.9), (0, math.radians(-70 + 180), 0), 0.12, 5.2, 45)
# light linking: the rim cards and rim strips light only the 4+, so the liquid never mirrors them as lines
only_four = bpy.data.collections.new('LINK_four'); only_four.objects.link(four)
for ob in (rc, sc, bpy.data.objects['LGT_rim_a'], bpy.data.objects['LGT_rim_b']):
    try: ob.light_linking.receiver_collection = only_four; ob.light_linking.blocker_collection = None
    except Exception as e: print('link', e)

sm = bpy.data.materials.new('MAT_sheen'); sm.use_nodes = True
SN = sm.node_tree.nodes; SN.remove(SN['Principled BSDF']); em = SN.new('ShaderNodeEmission')
em.inputs['Color'].default_value = (0.06, 0.28, 1.0, 1); em.inputs['Strength'].default_value = 1.6
sgr = SN.new('ShaderNodeTexGradient'); sgr.gradient_type = 'QUADRATIC_SPHERE'; stc = SN.new('ShaderNodeTexCoord'); smx = SN.new('ShaderNodeMath'); smx.operation = 'MULTIPLY'
SL = sm.node_tree.links; smp = SN.new('ShaderNodeVectorMath'); smp.operation = 'SCALE'; smp.inputs['Scale'].default_value = 0.28
SL.new(stc.outputs['Object'], smp.inputs[0]); SL.new(smp.outputs['Vector'], sgr.inputs['Vector']); SL.new(sgr.outputs['Fac'], smx.inputs[0]); smx.inputs[1].default_value = 15.0
SL.new(smx.outputs['Value'], em.inputs['Strength']); SL.new(em.outputs['Emission'], SN['Material Output'].inputs['Surface'])
smesh = bpy.data.meshes.new('sheen'); Q = 3.4; smesh.from_pydata([(-Q,-Q,0),(Q,-Q,0),(Q,Q,0),(-Q,Q,0)], [], [[0,1,2,3]])
sheen = bpy.data.objects.new('ENV_sheen', smesh); scn.collection.objects.link(sheen); sheen.data.materials.append(sm)
sheen.location = (-0.6, 2.6, 2.1); sheen.rotation_euler = (math.radians(125), 0, 0)
sheen.visible_camera = False; sheen.visible_diffuse = False; sheen.visible_shadow = False
hm = bpy.data.materials.new('MAT_horizon'); hm.use_nodes = True
HN = hm.node_tree.nodes; HN.remove(HN['Principled BSDF']); hem = HN.new('ShaderNodeEmission'); hem.inputs['Color'].default_value = (0.12, 0.38, 1.0, 1)
htc = HN.new('ShaderNodeTexCoord'); hsc = HN.new('ShaderNodeVectorMath'); hsc.operation = 'MULTIPLY'; hsc.inputs[1].default_value = (0.16, 1.1, 1.0)
hgr = HN.new('ShaderNodeTexGradient'); hgr.gradient_type = 'QUADRATIC_SPHERE'; hmx = HN.new('ShaderNodeMath'); hmx.operation = 'MULTIPLY'; hmx.inputs[1].default_value = 3.2
HL = hm.node_tree.links; HL.new(htc.outputs['Object'], hsc.inputs[0]); HL.new(hsc.outputs['Vector'], hgr.inputs['Vector']); HL.new(hgr.outputs['Fac'], hmx.inputs[0])
HL.new(hmx.outputs['Value'], hem.inputs['Strength']); HL.new(hem.outputs['Emission'], HN['Material Output'].inputs['Surface'])
hmesh = bpy.data.meshes.new('horizon'); hmesh.from_pydata([(-6,-0.9,0),(6,-0.9,0),(6,0.9,0),(-6,0.9,0)], [], [[0,1,2,3]])
hz = bpy.data.objects.new('ENV_horizon', hmesh); scn.collection.objects.link(hz); hz.data.materials.append(hm)
hz.location = (-0.4, 5.2, 0.7); hz.rotation_euler = (math.radians(90), 0, math.radians(-12))
hz.visible_camera = False; hz.visible_diffuse = False; hz.visible_shadow = False
only_liq = bpy.data.collections.new('LINK_liquid'); only_liq.objects.link(liq)
hz.light_linking.receiver_collection = only_liq
# a slim studio strip mirrored in the liquid behind the mark: the ripples bend and shimmer it
stm = bpy.data.materials.new('MAT_strip'); stm.use_nodes = True
TN = stm.node_tree.nodes; TN.remove(TN['Principled BSDF']); tem = TN.new('ShaderNodeEmission'); tem.inputs['Color'].default_value = (0.45, 0.72, 1.0, 1)
ttc = TN.new('ShaderNodeTexCoord'); tsc = TN.new('ShaderNodeVectorMath'); tsc.operation = 'MULTIPLY'; tsc.inputs[1].default_value = (0.4, 11.0, 1.0)
tgr = TN.new('ShaderNodeTexGradient'); tgr.gradient_type = 'QUADRATIC_SPHERE'; tmx = TN.new('ShaderNodeMath'); tmx.operation = 'MULTIPLY'; tmx.inputs[1].default_value = 6.0
TL = stm.node_tree.links; TL.new(ttc.outputs['Object'], tsc.inputs[0]); TL.new(tsc.outputs['Vector'], tgr.inputs['Vector']); TL.new(tgr.outputs['Fac'], tmx.inputs[0])
TL.new(tmx.outputs['Value'], tem.inputs['Strength']); TL.new(tem.outputs['Emission'], TN['Material Output'].inputs['Surface'])
tmesh = bpy.data.meshes.new('strip'); tmesh.from_pydata([(-2.5,-0.05,0),(2.5,-0.05,0),(2.5,0.05,0),(-2.5,0.05,0)], [], [[0,1,2,3]])
stp = bpy.data.objects.new('ENV_strip', tmesh); scn.collection.objects.link(stp); stp.data.materials.append(stm)
def mirror_place(ob, P, dist):  # put ob where the camera sees it reflected at liquid point P, facing back down at P
    C = Vector((1.25, -1.70, 1.82)); d = Vector(P) - C; r = Vector((d.x, d.y, -d.z)).normalized()
    ob.location = Vector(P) + r * dist
    ob.rotation_euler = (-r).to_track_quat('Z', 'Y').to_euler()
mirror_place(stp, (-0.15, 0.95, 0.0), 1.0)   # the strip's reflection runs just behind the mark
stp.visible_camera = False; stp.visible_diffuse = False; stp.visible_shadow = False
stp.light_linking.receiver_collection = only_liq
sheen.light_linking.receiver_collection = only_liq  # the liquid catches it; the 4+ never does

# ---------- camera: high and turned, sweeping round and down into the hero angle ----------
cd = bpy.data.cameras.new('CAM'); cd.lens = 42; cd.clip_start = 0.01; cd.dof.use_dof = False
cam = bpy.data.objects.new('CAM', cd); scn.collection.objects.link(cam); scn.camera = cam
tg = bpy.data.objects.new('CAM_target', None); scn.collection.objects.link(tg)
con = cam.constraints.new('TRACK_TO'); con.target = tg; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
cam.location = (1.25, -1.70, 1.82); tg.location = (0.0, -0.02, 0.05)
cd.lens = 44.0; cd.keyframe_insert('lens', frame=1)
cd.lens = 42.5; cd.keyframe_insert('lens', frame=120)     # a barely perceptible pull back
smooth(cd)
cd.dof.use_dof = True; cd.dof.focus_object = four; cd.dof.aperture_fstop = 4.0

# ---------- Cycles, crisp ----------
scn.render.engine = 'CYCLES'
try:
    pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'METAL'; pr.get_devices()
    for d in pr.devices: d.use = True
    scn.cycles.device = 'GPU'
except Exception as e: print('GPU', e)
scn.cycles.samples = SAMPLES; scn.cycles.use_denoising = True; scn.cycles.max_bounces = 8
scn.render.resolution_x = W; scn.render.resolution_y = int(W * 9 / 16)
scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - High Contrast'; scn.view_settings.exposure = 0.0
scn.render.image_settings.file_format = 'PNG'
os.makedirs(OUT, exist_ok=True)
frames = list(range(1, 121)) if FR == 'all' else [int(x) for x in FR.split(',')]
for f in range(1, max(frames) + 1):
    scn.frame_set(f); ripple_step(f)
    if f in frames:
        scn.render.filepath = os.path.join(OUT, f'f{f:03d}.png'); bpy.ops.render.render(write_still=True)
print('DONE')
