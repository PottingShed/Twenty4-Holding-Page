import bpy, math, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--')+1:]
OUT = argv[0]; RES = int(argv[1]); SAMPLES = int(argv[2]); CAMS = argv[3].split(',')
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene

# ---------- material: dark anodised blue metal, bead-blasted micro-grain ----------
mat = bpy.data.materials.new('MAT_anodised'); mat.use_nodes = True
nt = mat.node_tree; N = nt.nodes; L = nt.links
b = N['Principled BSDF']
b.inputs['Base Color'].default_value = (0.030, 0.075, 0.26, 1)
b.inputs['Metallic'].default_value = 0.82
b.inputs['Roughness'].default_value = 0.46
tc = N.new('ShaderNodeTexCoord')
grain = N.new('ShaderNodeTexNoise'); grain.inputs['Scale'].default_value = 1800; grain.inputs['Detail'].default_value = 2; grain.inputs['Roughness'].default_value = 0.6
L.new(tc.outputs['Object'], grain.inputs['Vector'])
bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.14; bump.inputs['Distance'].default_value = 0.002
L.new(grain.outputs['Fac'], bump.inputs['Height']); L.new(bump.outputs['Normal'], b.inputs['Normal'])
# gentle roughness variation so the light falls off softly
rv = N.new('ShaderNodeTexNoise'); rv.inputs['Scale'].default_value = 3; rv.inputs['Detail'].default_value = 1
mr = N.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.52; mr.inputs['To Max'].default_value = 0.62
L.new(tc.outputs['Object'], rv.inputs['Vector']); L.new(rv.outputs['Fac'], mr.inputs['Value']); L.new(mr.outputs['Result'], b.inputs['Roughness'])

# ---------- slab: rounded-corner plate with fine bevelled edges ----------
S = 2.4
me = bpy.data.meshes.new('slab'); me.from_pydata([(-S,-S,0),(S,-S,0),(S,S,0),(-S,S,0)], [], [[0,1,2,3]]); me.update()
slab = bpy.data.objects.new('ENV_slab', me); scn.collection.objects.link(slab)
m1 = slab.modifiers.new('round', 'BEVEL'); m1.affect = 'VERTICES'; m1.width = 0.7; m1.segments = 32
m2 = slab.modifiers.new('thick', 'SOLIDIFY'); m2.thickness = 0.28; m2.offset = -1
m3 = slab.modifiers.new('edge', 'BEVEL'); m3.width = 0.035; m3.segments = 8; m3.limit_method = 'ANGLE'; m3.harden_normals = True
slab.data.materials.append(mat)
for p in slab.data.polygons: p.use_smooth = True

# ---------- 4+ raised from the logo SVG paths ----------
plus = [(850.4,91),(811.9,91),(811.9,52.5),(788.5,52.5),(788.5,91),(750,91),(750,114.4),(788.5,114.4),(788.5,152.9),(811.9,152.9),(811.9,114.4),(850.4,114.4)]
diag = [(770.1,0),(705.4,90.9),(705.4,114.3),(718.1,114.3),(790.1,9.4),(790.1,0)]
cx, cy, k = 777.9, 76.5, 0.0095
def P(p): return [((x-cx)*k, -(y-cy)*k, 0.0) for x,y in p]
v1, v2 = P(plus), P(diag)
fm = bpy.data.meshes.new('four'); fm.from_pydata(v1+v2, [], [list(range(len(v1))), list(range(len(v1), len(v1)+len(v2)))]); fm.update()
four = bpy.data.objects.new('HERO_four', fm); scn.collection.objects.link(four)
four.location = (0.35, 0.3, 0.0)
f1 = four.modifiers.new('raise', 'SOLIDIFY'); f1.thickness = 0.12; f1.offset = 1
f2 = four.modifiers.new('edge', 'BEVEL'); f2.width = 0.008; f2.segments = 5; f2.limit_method = 'ANGLE'; f2.harden_normals = True
four.data.materials.append(mat)
for p in four.data.polygons: p.use_smooth = True

# ---------- world + light: low-key, raking ----------
w = bpy.data.worlds.new('W'); scn.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0.004, 0.008, 0.022, 1); bg.inputs['Strength'].default_value = 1.0
def area(name, loc, target, size, energy, color, shape='SQUARE', size_y=None):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.color = color; ld.shape = shape; ld.size = size
    if size_y: ld.size_y = size_y
    lo = bpy.data.objects.new(name, ld); scn.collection.objects.link(lo); lo.location = loc
    lo.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
area('LGT_key', (6.0, 5.0, 2.2), (0, 0, 0), 4, 1300, (0.78, 0.86, 1.0))              # big soft raking key, top-right
area('LGT_edge', (-5.0, -3.0, 0.9), (-1.5, -1.5, 0), 0.4, 900, (0.55, 0.75, 1.0), 'RECTANGLE', 6)   # strip to catch the bevelled edge
area('LGT_fill', (0, -6, 4), (0, 0, 0), 6, 60, (0.4, 0.55, 1.0))

# ---------- cameras ----------
def cam(name, loc, target, lens, fstop, focus='HERO_four', roll=0.0):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_start = 0.001; cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop; cd.dof.focus_object = bpy.data.objects[focus]
    co = bpy.data.objects.new(name, cd); scn.collection.objects.link(co); co.location = loc
    co.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if roll: co.rotation_euler.rotate_axis('Z', roll)
    cd.dof.focus_object = None; cd.dof.focus_distance = (Vector(target) - Vector(loc)).length
    return co
cams = {
  'a': cam('CAM_a', (0.30, 0.05, 0.95), (0.16, 0.42, 0.04), 45, 7.1, roll=-0.6),              # front-right, high: the diagonal sweeps past the plus
  'b': cam('CAM_b', (0.62, -0.62, 0.95), (0.40, 0.30, 0.04), 45, 6.3, roll=0.0),   # (kept) high three-quarter on the full 4+
  'c': cam('CAM_c', (0.48, -0.34, 0.98), (0.50, 0.12, 0.04), 50, 7.1, roll=0.12),  # steep, tilted overhead of the whole mark
}

scn.render.engine = 'CYCLES'
try:
    pr = bpy.context.preferences.addons['cycles'].preferences; pr.compute_device_type = 'METAL'; pr.get_devices()
    for d in pr.devices: d.use = True
    scn.cycles.device = 'GPU'
except Exception as e: print('GPU setup failed', e)
scn.cycles.samples = SAMPLES; scn.cycles.use_denoising = True
scn.render.film_transparent = False
scn.render.resolution_x = RES; scn.render.resolution_y = RES
scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast'
scn.render.image_settings.file_format = 'PNG'
os.makedirs(OUT, exist_ok=True)
EXPO = {'a': -0.8, 'b': -0.8, 'c': -0.9}
TURN = {'a': 0.0, 'b': 0.0, 'c': 0.0}   # face the mark towards each lens
for c in CAMS:
    scn.view_settings.exposure = EXPO[c]
    four.rotation_euler = (0, 0, TURN[c])
    scn.camera = cams[c]; scn.render.filepath = os.path.join(OUT, f'blue-{c}.png')
    bpy.ops.render.render(write_still=True); print('RENDERED', scn.render.filepath)
