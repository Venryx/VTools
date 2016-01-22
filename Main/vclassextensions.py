from vtools import *
from vtools.vglobals import *

from mathutils import *

import bpy_types

'''def AddMethod(type, method):
	type[method.__name__] = method
	del(method)'''

# Object
# ==========

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

def GetCorners(s):
	result = []
	for corner in s.bound_box:
		result.append(corner)
	return result
bpy_types.Object.GetCorners = GetCorners

def GetLocation(s, global_):
	return s.matrix_world.decompose()[0] if global_ == true else s.location
bpy_types.Object.GetLocation = GetLocation

def ToLocal(s, vec, applyTranslations = true):
	matrix = s.matrix_world.inverted()
	if not applyTranslations:
		matrix.translation = Vector((0, 0, 0))
	return matrix * vec
bpy_types.Object.ToLocal = ToLocal

def ToWorld(s, vec, applyTranslations = true):
	matrix = s.matrix_world
	if not applyTranslations:
		matrix.translation = Vector((0, 0, 0))
	return matrix * vec
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

'''def Vertexes(s):
	if s.mode == "EDIT": # this works only in edit mode
		mesh = bmesh.from_edit_mesh(obj.data)
		return W(mesh.verts)
	return W(s.data.vertices)
bpy_types.Object.Vertexes = Vertexes'''
import bmesh
def Mesh(s):
	if s.mode == "EDIT": # this works only in edit mode
		return bmesh.from_edit_mesh(s.data)
	return s.data
bpy_types.Object.Mesh = Mesh

def Object_Vertexes(s):
	if s.mode == "EDIT": # this works only in edit mode
		return BMesh_Vertexes(s.Mesh()).SetThenReturn("objData", s.data)
	return W(s.data.vertices) if s.data is not null else W([])
bpy_types.Object.Vertexes = Object_Vertexes

# bmesh
# ==========

def BMesh_Vertexes(s):
	return W(s.verts).SetThenReturn("mesh", s)
#bmesh.types.BMesh.Vertexes = BMesh_Vertexes
def BMesh_Save(s, objData):
	bpy.ops.ed.undo_push(message = "Pre BMesh.Save")

	#s.to_mesh()
	#bpy.context.object.update_from_editmode() # load the objects edit-mode data into the object data
	bmesh.update_edit_mesh(objData, true)
#bmesh.types.BMesh.Save = BMesh_Save

# list - from bmesh.Vertexes()
# ==========

def List_SaveMesh(s):
	BMesh_Save(s.mesh, s.objData)
List.SaveMesh = List_SaveMesh

# ShaderNodeTree
# ==========

'''def ShaderNodeTree_Nodes(s):
	result = []
	for node in s:
		result.append(node)
	return result
bpy.types.ShaderNodeTree.Nodes = ShaderNodeTree_Nodes'''

# AnimData
# ==========

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
# ==========

# fix the root-bone matrix, to use the more sensible resting position/orientation (where the rest rotation has the tail-end toward z+, rather than y+)
#if s.parent is null:
#	result = fixMatrixForRootBone(result)

def Bone_GetMatrix_World(s, obj):
	return obj.matrix_world * s.matrix_local
bpy_types.Bone.GetMatrix_World = Bone_GetMatrix_World

def Bone_GetMatrix_Object(s):
	return s.matrix_local
bpy_types.Bone.GetMatrix_Object = Bone_GetMatrix_Object

def Bone_GetMatrix(s):
	result = s.matrix_local # starts out including parent-matrix
	if s.parent is not null:
		result = s.parent.matrix_local.inverted() * result
	return result
bpy_types.Bone.GetMatrix = Bone_GetMatrix

# EditBone
# ==========

def EditBone_GetMatrix_World(s, obj):
	return obj.matrix_world * s.matrix # make-so: this is confirmed to be correct
bpy_types.EditBone.GetMatrix_World = EditBone_GetMatrix_World

# PoseBone
# ==========

def PoseBone_GetMatrix_World(s, obj):
	return obj.matrix_world * s.matrix
bpy_types.PoseBone.GetMatrix_World = PoseBone_GetMatrix_World

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

# Matrix
# ==========

def Matrix_NewScale(s, newScale):
	position, rotation, scale = s.decompose()

	#return Matrix.Translation(position) * rotation.to_matrix().to_4x4() * Matrix.Scale(1, 4, scale)
	result = s.copy()
	for i in range(3):
		#result[i][i] = newScale[i]
		result[i][i] = scale[i]
	return result

	#return Matrix.Translation(position) * rotation.to_matrix().to_4x4() * Matrix.Scale(1, 4, newScale)
#Matrix.NewScale = Matrix_NewScale

def Matrix_MultipliedBy(s, quaternion):
	quaternion_copy = quaternion.copy()
	quaternion_copy.rotate(s)
	return quaternion_copy
#Matrix.MultipliedBy = Matrix_MultipliedBy

# FCurve
# ==========

def FCurve_GetBoneName(s):
	if "[\"" in s.data_path and "\"]." in s.data_path:
		return v.GetBoneNameFromDataPath(s.data_path)
	return s.group.name
bpy.types.FCurve.GetBoneName = FCurve_GetBoneName

def FCurve_GetPropertyName(s):
	if "[\"" in s.data_path and "\"]." in s.data_path:
		return v.GetPropertyNameFromDataPath(s.data_path)
	return s.data_path
bpy.types.FCurve.GetPropertyName = FCurve_GetPropertyName

# Keyframe
# ==========

def Keyframe_SetValue(s, value, resetHandles=false):
	s.co.y = value
	if resetHandles:
		s.handle_left = [s.co.x - 3, value]
		s.handle_right = [s.co.x + 3, value]
bpy.types.Keyframe.SetValue = Keyframe_SetValue