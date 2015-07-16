from vtools import *
from vtools.vglobals import *

import re
import math
from mathutils import *

import bpy

# snippets
# ==========

#__import__("code").interact(local={k: v for ns in (globals(), locals()) for k, v in ns.items()})

# general
# ==========

def IndentLines(str, count = 1, indentFirstLine = true):
	for i in range(0, count):
		if indentFirstLine:
			str = "\t" + str
		return re.sub('\n', '\n\t', str)

def ToDegrees(radians): #math.degrees
	return radians * (180 / math.pi) # radians * degrees-in-a-radian
def ToRadians(degrees): #math.radians
	return degrees / (180 / math.pi) # degrees / degrees-in-a-radian

def Vector_ToDegrees(v):
	if len(v) == 3:
		return Vector((toDegrees(v.x), toDegrees(v.y), toDegrees(v.z))) #return {"x": toDegrees(v.x), "y": toDegrees(v.y), "z": toDegrees(v.z)}
	else:
		return Vector((toDegrees(v.x), toDegrees(v.y), toDegrees(v.z), toDegrees(v.w))) #return {"x": toDegrees(v.x), "y": toDegrees(v.y), "z": toDegrees(v.z), "w": toDegrees(v.w)}
def Quaternion_ToDegrees(q):
	return Quaternion((toDegrees(q.w), toDegrees(q.x), toDegrees(q.y), toDegrees(q.z)))

# utils - files
# ==========

def write_file(fname, content):
	out = open(fname, "w", encoding="utf-8")
	out.write(content)
	out.close()

def ensure_folder_exist(foldername):
	"""Create folder (with whole path) if it doesn't exist yet."""

	if not os.access(foldername, os.R_OK | os.W_OK | os.X_OK):
		os.makedirs(foldername)

def ensure_extension(filepath, extension):
	if not filepath.lower().endswith(extension):
		filepath += extension
	return filepath

def generate_mesh_filename(meshname, filepath):
	normpath = os.path.normpath(filepath)
	path, ext = os.path.splitext(normpath)
	return "%s.%s%s" % (path, meshname, ext)

# 3d object creation
# ==========

def CreateObject_Empty(name, position = (0, 0, 0), rotation = (0, 0, 0, 1), scale = (1, 1, 1), emptyDrawType = "PLAIN_AXES"):
	position = Vector(position)
	rotation = Vector(rotation)
	scale = Vector(scale)

	import bpy
	result = bpy.data.objects.new(name, None)

	scene = bpy.context.scene
	scene.objects.link(result)
	scene.update()

	result.location = position
	#result.rotation = rotation
	result.scale = scale #/ 2

	result.empty_draw_type = emptyDrawType
	
	return result

def CreateObject_Cube(name, position = (0, 0, 0), rotation = (0, 0, 0, 1), scale = (1, 1, 1)):
	position = Vector(position)
	rotation = Vector(rotation)
	scale = Vector(scale)

	#return bpy.ops.mesh.primitive_cube_add(location = location, rotation = rotation, scale = scale)
	bpy.ops.mesh.primitive_cube_add() #location = position)
	result = [a for a in bpy.data.objects if a.select][0]
	result.location = position + Vector((scale.x / 2, scale.y / 2, scale.z / 2))
	#result.rotation = rotation #result.localRotation = rotation
	result.scale = scale #result.localScale = scale
	return result

# object control
# ==========

savedSelections = {}
def SaveSelection(name = "main"):
	savedSelections[name] = GetSelection()
def GetSelection():
	result = {}
	for obj in bpy.data.objects:
		result[obj] = obj.select
	return result
def LoadSelection(name = "main"):
	selection = savedSelections[name]
	for obj in bpy.data.objects:
		obj.select = obj in selection and selection[obj]

def DeleteObject(obj):
	for child in obj.children:
		DeleteObject(child)

	for obj2 in bpy.context.scene.objects:
		obj2.select = false
	obj.select = true
	bpy.ops.object.delete()

'''def SetObjectOriginPoint(obj, originPoint):
	saved_location = bpy.context.scene.cursor_location.copy()
    bpy.ops.view3d.snap_cursor_to_selected()

    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')  
    bpy.context.scene.cursor_location = saved_location

    bpy.ops.object.mode_set(mode = 'EDIT')'''