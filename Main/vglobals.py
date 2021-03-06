from vtools import *
'''moduleNamesToNiceNames = {"v": "V", "vdebug": "VDebug", "vglobals": "VGlobals", "vtools": "VTools"}
for name, niceName in enumerate(moduleNamesToNiceNames):
	exec(niceName + " = " + name)'''
moduleNiceNames = ["V", "VDebug", "VClassExtensions", "VGlobals", "VTools"]
for niceName in moduleNiceNames:
	if niceName.lower() in locals() or niceName.lower() in globals():
		exec(niceName + " = " + niceName.lower())

import bpy
import math
from mathutils import *
import re

# snippets
# ==========

#__import__("code").interact(local={k: v for ns in (globals(), locals()) for k, v in ns.items()})

# constants
# ==========

null = None
false = False
true = True

# Blender: general
# ==========

def Objects():
	return bpy.data.objects
def Object(name):
	for obj in bpy.data.objects:
		if obj.name == name:
			return obj
	return null
def Selected(includeActive = true):
	result = bpy.context.selected_objects
	if not includeActive:
		result = [a for a in result if a != Active()]
	return result
def Active():
	return bpy.context.scene.objects.active
def SelectedVertexes():
	return Active().Vertexes().Where("a.select") #if Active() is not null else []
def SelectedVertex():
	selectedVerts = SelectedVertexes()
	return selectedVerts[0] if len(selectedVerts) >= 1 else null
def ActiveVertex():
	return SelectedVertex()
def ActiveBone():
	if len(Active().data.edit_bones) >= 1:
		return [a for a in Active().data.edit_bones if a.select or a.select_head or a.select_tail][0]
	return [a for a in Active().pose.bones if a.bone == Active().data.bones.active][0]
def ActiveAction():
	return Active().animation_data.action if Active() and Active().animation_data else null
def ActiveMaterial():
	return Active().active_material if Active() else null
def ActiveNode():
	return [a for a in Active().active_material.node_tree.nodes if a.select][0] if ActiveMaterial() else null

def Material(name):
	return W([a for a in bpy.data.materials if a.name == name]).First()

def SaveMesh():
	oldMode = bpy.context.object.mode
	bpy.ops.object.mode_set(mode = "OBJECT")
	bpy.ops.object.mode_set(mode = oldMode)

def Get3DCursorPosition():
	return bpy.context.scene.cursor_location

# general
# ==========

def Nothing():
	pass

def Log(message):
	print(message)

class AnonymousObject(object):
	'''def __init__(s, **kwargs):
		for (k,v) in kwargs.items():
			s.__setattr__(k, v)'''
	def __init__(s, dictionary):
		for (k,v) in dictionary.items():
			s.__setattr__(k, v)
	def __repr__(s):
		return 'literal(%s)' % ', '.join('%s = %r' % i for i in sorted(s.__dict__.items()))
	def __str__(s):
		return repr(s)
def O(dictionary):
	return AnonymousObject(dictionary)

s_defaultNumberTruncate = -1
def S(obj, numberTruncate = null):
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
			result = "[" + S(obj.x, numberTruncate) + " " + S(obj.y, numberTruncate) + " " + S(obj.z, numberTruncate) + "]"
		else:
			result = "[" + S(obj.x, numberTruncate) + " " + S(obj.y, numberTruncate) + "]"
	elif type(obj) == Quaternion:
		result = "[" + S(obj.x, numberTruncate) + " " + S(obj.y, numberTruncate) + " " + S(obj.z, numberTruncate) + " " + S(obj.w, numberTruncate) + "]"
	else:
		result = str(obj)

	return result
#def st(obj, numberTruncate = null):
#	return S(obj, numberTruncate)

# use like this:
#	bpy_types.Object.PrintXAndY = F("print(str1 + str2)", "str1, str2")
def F(body, arglistStr = null):
	if arglistStr is null:
		arglistStr = "a"

	'''g = {}
	exec("def anonfunc({0}):\n{1}".format(arglistStr, "\n".join("	{0}".format(line) for line in body.splitlines())), g)
	return g["anonfunc"]'''

	g = globals()
	exec("def tempFunc({0}):\n{1}".format(arglistStr, "\n".join("	{0}".format(line) for line in body.splitlines())), g)
	result = g["tempFunc"]
	#result = tempFunc
	#del(tempFunc)
	return result

def GetCurrentFunction():
	from inspect import currentframe, getframeinfo
	frame_back1 = currentframe().f_back
	func_name = getframeinfo(frame_back1)[2]

	frame_back2 = frame_back1.f_back
	#from pprint import pprint
	func = frame_back2.f_locals.get(func_name, frame_back2.f_globals.get(func_name))

	return func

# function helper
# ==========

import functools
def CallFuncWithRefToItself(func):
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		return func(func, *args, **kwargs)
	wrapper.m = func
	func.wrapper = wrapper
	return wrapper

# VWrap
# ==========

import types
#class List(types.ListType):
class List(list):
	def __getitem__(s, key):
		#return list.__getitem__(s, key - 1)
		return super(List, s).__getitem__(key)
	def __setitem__(s, key, value):
		return super(List, s).__setitem__(key, value)

	'''def __init__(s, obj):
		s.obj = obj
	obj = null'''

	# list
	def Each(s, func_orFuncStr):
		#func = func_orFuncStr if type(func_orFuncStr) == types.function else F(func_orFuncStr)
		func = func_orFuncStr if type(func_orFuncStr) == types.FunctionType else F(func_orFuncStr)
		for item in s:
			func(item)
		return s # for chaining
	def Where(s, func_orFuncStr):
		func = func_orFuncStr
		if type(func_orFuncStr) != types.FunctionType:
			funcStr = func_orFuncStr
			if funcStr.count("return ") == 0:
				funcStr = "return " + funcStr
			func = F(funcStr)

		result = List()
		#if "objData" in s:
		if hasattr(s, "objData"):
			result.objData = s.objData
		if hasattr(s, "mesh"):
			result.mesh = s.mesh
		for item in s:
			if func(item):
				result.append(item)
		return result

	# special
	def SetThenReturn(s, propName, value):
		exec("s." + propName + " = value")
		return s

type_copy = type
def W(obj):
	#type = globals()["type"](obj)
	type = type_copy(obj)
	typeName = type.__name__
	#if type(obj) == list or type(obj) == bpy.types.bpy_prop_collection or type(obj) == List:
	#if type == list or type == List or type == bpy_types.bpy_prop_collection:
	#if type == list or type == List or obj.__getitem__("__iter__") != null:
	#if type == list or type == List or hasattr(obj, "__iter__"):
	if hasattr(obj, "__iter__"):
		return List(obj)

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