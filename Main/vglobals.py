from vtools import *
'''moduleNamesToNiceNames = {"v": "V", "vdebug": "VDebug", "vglobals": "VGlobals", "vtools": "VTools"}
for name, niceName in enumerate(moduleNamesToNiceNames):
	exec(niceName + " = " + name)'''
moduleNiceNames = ["V", "VDebug", "VGlobals", "VTools"]
for niceName in moduleNiceNames:
	if niceName.lower() in locals() or niceName.lower() in globals():
		exec(niceName + " = " + niceName.lower())

import re
import math
from mathutils import *

# snippets
# ==========

#__import__("code").interact(local={k: v for ns in (globals(), locals()) for k, v in ns.items()})

# constants
# ==========

null = None
false = False
true = True

# V class links
# ==========

def Objects():
	return bpy.data.objects
def Obj(name):
	for obj in bpy.data.objects:
		if obj.name == name:
			return obj
	return null
def Selected():
	return bpy.context.selected_objects
def Active():
	return bpy.context.scene.objects.active

def Get3DCursorPosition():
	return bpy.context.scene.cursor_location

# general
# ==========

def Nothing():
	pass

def Log(message):
	print(message)

s_defaultNumberTruncate = -1
def s(obj, numberTruncate = null):
	global s_defaultNumberTruncate
	numberTruncate = numberTruncate if numberTruncate != null else s_defaultNumberTruncate
	#if numberTruncate != -1:
	#	numberTruncate += 1 # todo: make sure this is correct

	result = ""

	#if obj is int or obj is float: #or obj is long: #or obj is complex:
	if type(obj) == int or type(obj) == float:
		result = ("{:." + str(numberTruncate) + "f}").format(float("%g" % obj)) if numberTruncate != -1 else ("%g" % obj) #str(obj)

		if result.find(".") != -1:
			result = result.rstrip("0")
		if result.endswith("."):
			result = result[0:-1]

		if result.startswith("0."):
			result = result[1:]
		if result.startswith("-0."):
			result = "-" + result[2:]
	
		if result == "-0":
			result = "0"
		if result == ".0" or result == "-.0":
			result = "0"
	elif type(obj) == Vector: #elif obj is Vector:
		if "z" in obj:
			result = "[" + s(obj.x, numberTruncate) + " " + s(obj.y, numberTruncate) + " " + s(obj.z, numberTruncate) + "]"
		else:
			result = "[" + s(obj.x, numberTruncate) + " " + s(obj.y, numberTruncate) + "]"
	elif type(obj) == Quaternion:
		result = "[" + s(obj.x, numberTruncate) + " " + s(obj.y, numberTruncate) + " " + s(obj.z, numberTruncate) + " " + s(obj.w, numberTruncate) + "]"
	else:
		result = str(obj)
	
	return result
def st(obj, numberTruncate = null):
	return s(obj, numberTruncate)

# blender constants/shortcuts
# ==========

'''import bpy
def PostSceneLoad(unknown):
	Log("Handler called")
	global C, D
	C = bpy.context
	D = bpy.data

	if PostSceneLoad in bpy.app.handlers.scene_update_post:
		bpy.app.handlers.scene_update_post.remove(PostSceneLoad)

if PostSceneLoad not in bpy.app.handlers.scene_update_post:
	Log("Adding handler")
	bpy.app.handlers.scene_update_post.append(PostSceneLoad)'''

# linq
# ==========

def Any(collection, matchFunc):
	return len(list(filter(matchFunc, collection))) > 0

# class extensions
# ==========

def AddMethod(type, method):
	type[method.__name__] = method
	del(method)

import bpy_types
#bpy_types.Object.GetBounds = GetBounds()

# Object
# ----------

def GetBounds(s):
	'''result = Box(s.location, s.dimensions)
	for child in s.children:
		result = result.Encapsulate(child.GetBounds())
	return result'''
	result = Box.Null
	for corner in s.bound_box:
		result = result.Encapsulate(s.matrix_world * Vector(corner))
	return result
#AddMethod(bpy_types.Object, GetBounds)
bpy_types.Object.GetBounds = GetBounds
#del(GetBounds)

def ToLocal(s, pos):
	return s.matrix_world.inverted() * pos
bpy_types.Object.ToLocal = ToLocal

def ToWorld(s, pos):
	return s.matrix_world * pos
bpy_types.Object.ToWorld = ToWorld

def SetOrigin(s, pos, preserveLinkedCopyFinalTransforms = true):
	oldCursorPos = bpy.context.scene.cursor_location.copy()
	bpy.context.scene.cursor_location = s.ToGlobal(pos)
	bpy.ops.object.origin_set(type = "ORIGIN_CURSOR")
	bpy.context.scene.cursor_location = oldCursorPos

	if preserveLinkedCopyFinalTransforms:
		for obj in s.GetLinkedCopies():
			#obj.location += pos
			#obj.location = obj.ToWorld(pos)
			obj.location += (obj.rotation_euler.to_matrix() * pos)
bpy_types.Object.SetOrigin = SetOrigin

def GetLinkedCopies(s, includeSelf = false):
	result = []
	for obj in Objects():
		if obj.data == s.data and (obj != s or includeSelf):
				result.append(obj)
	return result
bpy_types.Object.GetLinkedCopies = GetLinkedCopies

def GetDescendents(s):
	result = []
	for child in s.children:
		result.append(child)
		result.extend(child.GetDescendents())
	return result
bpy_types.Object.GetDescendents = GetDescendents

# AnimData
# ----------

'''def ActionContainsChannelsForArmature(action, armature):
	armatureBoneNames = [x.name for x in armature.bones]
	for fcurve in action.fcurves:
		boneName = fcurve.data_path[fcurve.data_path.find('"') + 1:fcurve.data_path.find('"', fcurve.data_path.find('"') + 1)]
		if boneName in armatureBoneNames:
			return true
	return false

def GetActions(s):
	result = []
	for action in bpy.data.actions:
		if ActionContainsChannelsForArmature(action, s): # action.groups[0].name == obj.data.name or action.groups[0].name in obj.data.bones: # action == obj.animation_data.action # todo: make sure this is correct
			result.append(action)
	return result
#AddMethod(bpy_types.Object, GetBounds)
bpy_types.AnimData.GetActions = GetActions'''

# Bone
# ----------

# fix the root-bone matrix, to use the more sensible resting position/orientation (where the rest rotation has the tail-end toward z+, rather than y+)
#if s.parent is null:
#	result = fixMatrixForRootBone(result)

def Bone_GetMatrix_Object(s):
	return s.matrix_local
bpy_types.Bone.GetMatrix_Object = Bone_GetMatrix_Object

def Bone_GetMatrix(s):
	result = s.matrix_local # starts out including parent-matrix
	if s.parent is not null:
		result = s.parent.matrix_local.inverted() * result
	return result
bpy_types.Bone.GetMatrix = Bone_GetMatrix

# PoseBone
# ----------

# note that, as per V heirarchy/parent-and-unit conceptualization standards, matrix_object does not include base-matrix_object (so it's not in object-space--at least not in-the-same-way/with-the-same-units as, say, vertexes are)
def PoseBone_GetMatrix_Object(s, addBaseMatrixes = true):
	baseBone = s.bone

	result = s.matrix # starts out as: base-matrix_object + matrix_object(pose-matrix_object)
	if not addBaseMatrixes:
		result = baseBone.matrix_local.inverted() * result
	
	return result
bpy_types.PoseBone.GetMatrix_Object = PoseBone_GetMatrix_Object

def PoseBone_GetMatrix(s, addBaseMatrixes = true):
	baseBone = s.bone

	result = s.matrix # starts out as: [parent-base-matrix_object + parent-matrix_object] + [base-matrix_object + matrix_object]
	if s.parent is not null: # remove this part: [parent-base-matrix_object + parent-matrix_object]
		result = s.parent.GetMatrix_Object().inverted() * result
	if not addBaseMatrixes: # remove this part: base-matrix_object
		result = baseBone.GetMatrix_Object().inverted() * s.matrix

	return result
bpy_types.PoseBone.GetMatrix = PoseBone_GetMatrix

# Box (i.e. bounds) class
# ==========

RareFloat = -9876.54321

class Box:
	'''_Null = null
	@classmethod
	@property
	def Null():
		return Box(Vector((RareFloat, RareFloat, RareFloat)), Vector((RareFloat, RareFloat, RareFloat)))'''
	Null = null

	def __init__(s, position, size):
		s.position = Vector(position)
		s.size = Vector(size)
	#def GetMin():
	#	return position
	def GetMax(s):
		return s.position + s.size
	def Encapsulate(s, point_orBox):
		result = Box(s.position, s.size)
		if type(point_orBox) is Box:
			box = point_orBox
			if result.position == Box.Null.position and result.size == Box.Null.size: #s is Box.Null:
				result.position = box.position
				result.size = box.size
			else:
				result.position.x = min(result.position.x, box.position.x)
				result.position.y = min(result.position.y, box.position.y)
				result.position.z = min(result.position.z, box.position.z)
				result.size.x = max(result.GetMax().x, box.GetMax().x) - result.position.x
				result.size.y = max(result.GetMax().y, box.GetMax().y) - result.position.y
				result.size.z = max(result.GetMax().z, box.GetMax().z) - result.position.z
		else:
			point = point_orBox
			if result.position == Box.Null.position and result.size == Box.Null.size: #s is Box.Null:
				result.position = point
				result.size = (0, 0, 0)
			else:
				result.position.x = min(result.position.x, point.x)
				result.position.y = min(result.position.y, point.y)
				result.position.z = min(result.position.z, point.z)
				result.size.x = max(result.GetMax().x, point.x) - result.position.x
				result.size.y = max(result.GetMax().y, point.y) - result.position.y
				result.size.z = max(result.GetMax().z, point.z) - result.position.z
		return result
	def Intersects(s, point_orBox):
		if type(point_orBox) is Box:
			box = point_orBox
			xIntersects = s.position.x < box.GetMax().x and box.x < s.GetMax().x
			yIntersects = s.position.y < box.GetMax().y and box.y < s.GetMax().y
			zIntersects = s.position.z < box.GetMax().z and box.z < s.GetMax().z
			return xIntersects and yIntersects and zIntersects
		else:
			point = point_orBox
			xIntersects = s.position.x < point.x and point.x < s.GetMax().x
			yIntersects = s.position.y < point.y and point.y < s.GetMax().y
			zIntersects = s.position.z < point.z and point.z < s.GetMax().z
			return xIntersects and yIntersects and zIntersects

Box.Null = Box(Vector((RareFloat, RareFloat, RareFloat)), Vector((RareFloat, RareFloat, RareFloat)))