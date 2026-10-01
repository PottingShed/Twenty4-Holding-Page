import bpy, math, math, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--')+1:]
OUT = argv[0]; W = int(argv[1]); SAMPLES = int(argv[2]); FR = argv[3]
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.render.fps = 30; scn.frame_start = 1; scn.frame_end = 160

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
lb.inputs['Base Color'].default_value = (0.001, 0.004, 0.018, 1); lb.inputs['Roughness'].default_value = 0.09; lb.inputs['Specular IOR Level'].default_value = 0.7

# ---------- liquid ----------
S = 8.0
me = bpy.data.meshes.new('liquid'); me.from_pydata([(-S,-S,0),(S,-S,0),(S,S,0),(-S,S,0)], [], [[0,1,2,3]]); me.update()
liq = bpy.data.objects.new('ENV_liquid', me); scn.collection.objects.link(liq); liq.data.materials.append(lm)
sub = liq.modifiers.new('sub', 'SUBSURF'); sub.subdivision_type = 'SIMPLE'; sub.levels = 9; sub.render_levels = 10
wv = liq.modifiers.new('ripple', 'WAVE'); wv.use_x = True; wv.use_y = True; wv.use_normal = False
wv.start_position_x = 0.35; wv.start_position_y = 0.30
wv.time_offset = 4; wv.speed = 0.012; wv.height = 0.018; wv.width = 0.16; wv.narrowness = 1.2; wv.damping_time = 90; wv.falloff_radius = 3.4
for p in liq.data.polygons: p.use_smooth = True

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
four.location = (0.35, 0.30, -0.125); four.keyframe_insert('location', index=2, frame=1)
four.location.z = 0.0; four.keyframe_insert('location', index=2, frame=135)
ease(four, 'SINE', 'EASE_IN_OUT')  # an unhurried rise, breaking the surface almost at once

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
rc = card('CARD_rim', (0.3, 2.6, 1.2), (math.radians(75), 0, 0), 3.0, 0.08)
sc = card('CARD_side', (-2.4, 0.2, 0.9), (0, math.radians(-70), 0), 0.06, 2.6)
# light linking: the rim cards and rim strips light only the 4+, so the liquid never mirrors them as lines
only_four = bpy.data.collections.new('LINK_four'); only_four.objects.link(four)
for ob in (rc, sc, bpy.data.objects['LGT_rim_a'], bpy.data.objects['LGT_rim_b']):
    try: ob.light_linking.receiver_collection = only_four; ob.light_linking.blocker_collection = None
    except Exception as e: print('link', e)

sm = bpy.data.materials.new('MAT_sheen'); sm.use_nodes = True
SN = sm.node_tree.nodes; SN.remove(SN['Principled BSDF']); em = SN.new('ShaderNodeEmission')
em.inputs['Color'].default_value = (0.06, 0.28, 1.0, 1); em.inputs['Strength'].default_value = 1.6
sgr = SN.new('ShaderNodeTexGradient'); sgr.gradient_type = 'QUADRATIC_SPHERE'; stc = SN.new('ShaderNodeTexCoord'); smx = SN.new('ShaderNodeMath'); smx.operation = 'MULTIPLY'
SL = sm.node_tree.links; smp = SN.new('ShaderNodeVectorMath'); smp.operation = 'SCALE'; smp.inputs['Scale'].default_value = 0.4
SL.new(stc.outputs['Object'], smp.inputs[0]); SL.new(smp.outputs['Vector'], sgr.inputs['Vector']); SL.new(sgr.outputs['Fac'], smx.inputs[0]); smx.inputs[1].default_value = 7.0
SL.new(smx.outputs['Value'], em.inputs['Strength']); SL.new(em.outputs['Emission'], SN['Material Output'].inputs['Surface'])
smesh = bpy.data.meshes.new('sheen'); Q = 2.6; smesh.from_pydata([(-Q,-Q,0),(Q,-Q,0),(Q,Q,0),(-Q,Q,0)], [], [[0,1,2,3]])
sheen = bpy.data.objects.new('ENV_sheen', smesh); scn.collection.objects.link(sheen); sheen.data.materials.append(sm)
sheen.location = (-0.6, 2.6, 2.1); sheen.rotation_euler = (math.radians(125), 0, 0)
sheen.visible_camera = False; sheen.visible_diffuse = False; sheen.visible_shadow = False
only_liq = bpy.data.collections.new('LINK_liquid'); only_liq.objects.link(liq)
sheen.light_linking.receiver_collection = only_liq  # the liquid catches it; the 4+ never does

# ---------- camera: high and turned, sweeping round and down into the hero angle ----------
cd = bpy.data.cameras.new('CAM'); cd.lens = 42; cd.clip_start = 0.01; cd.dof.use_dof = False
cam = bpy.data.objects.new('CAM', cd); scn.collection.objects.link(cam); scn.camera = cam
tg = bpy.data.objects.new('CAM_target', None); scn.collection.objects.link(tg)
con = cam.constraints.new('TRACK_TO'); con.target = tg; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
keys = [  # frame, camera location, target: high and turned, orbiting round and settling at 38 degrees
  (1,   (-1.05, -0.70, 3.30), (0.35, 0.30, 0.0)),
  (80,  (0.55, -1.75, 2.45), (0.12, 0.12, 0.03)),
  (160, (1.25, -1.70, 1.82), (0.0, -0.02, 0.05)),
]
for f, cl, tl in keys:
    cam.location = cl; cam.keyframe_insert('location', frame=f)
    tg.location = tl; tg.keyframe_insert('location', frame=f)
ease(cam, 'QUINT', 'EASE_IN_OUT'); ease(tg, 'QUINT', 'EASE_IN_OUT')

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
frames = range(1, 161) if FR == 'all' else [int(x) for x in FR.split(',')]
for f in frames:
    scn.frame_set(f); scn.render.filepath = os.path.join(OUT, f'f{f:03d}.png'); bpy.ops.render.render(write_still=True)
print('DONE')
