#__all__ = ["v", "vdebug", "vglobals", "vtools"]
import vtools.v
import vtools.vdebug
import vtools.vglobals
import vtools.vtools

# init
# ==========

from vtools import *
from vtools.vglobals import *

from math import *
#import math

bl_info = {
	"name": "VTools",
	"author": "Venryx",
	"version": (0, 0, 1),
	"blender": (2, 7, 0),
	"description": "Small tools to make the Blender infrastructure more usable/accessible.",
	"warning": "",
	"wiki_url": "n/a",
	"tracker_url": "n/a",
	"category": "Object"
}

from bpy.props import *
from bpy_extras.io_utils import ExportHelper, ImportHelper

# VTools object panel
# ==========

'''bpy.types.Object.VModel_export = bpy.props.BoolProperty(default = true)
bpy.types.Object.VModel_anchorToTerrain = bpy.props.BoolProperty(default = false)
bpy.types.Object.material_doubleSided = bpy.props.BoolProperty(default = false)
bpy.types.Object.material_alphaMin_enabled = bpy.props.BoolProperty(default = false)
bpy.types.Object.material_alphaMin = bpy.props.FloatProperty(description = "Minimum alpha required for a pixel/fragment to be rendered.", min = 0, max = 1, default = .5)

class OBJECT_PT_hello(bpy.types.Panel):
	bl_label = "VModel"
	bl_space_type = "PROPERTIES"
	bl_region_type = "WINDOW"
	bl_context = "object"

	def draw(self, context):
		layout = self.layout
		obj = context.object
		
		row = layout.row()
		row.label(text="Selected object: " + obj.name)

		row = layout.row()
		row.prop(obj, "VModel_export", text="Export object")

		row = layout.row()
		row.prop(obj, "VModel_anchorToTerrain", text="Anchor to terrain")

		row = layout.row()
		row.operator("view3d.show_space_taken", text="Show space taken")
		row.operator("view3d.hide_space_taken", text="Hide space taken")

		row = layout.row()
		row.label(text="Material:")

		row = layout.row()
		row.prop(obj, "material_doubleSided", text="Double-sided")

		row = layout.row()
		row.prop(obj, "material_alphaMin_enabled", text="Alpha min")
		if obj.material_alphaMin_enabled:
			row.prop(obj, "material_alphaMin", text="")'''

# VModel material panel
# ==========

'''VModel_material_types = [("Basic", "Basic", "Basic"), ("Phong", "Phong", "Phong"), ("Lambert", "Lambert", "Lambert")]
bpy.types.Material.VModel_materialType = EnumProperty(name = "Material type", description = "Material type", items = VModel_material_types, default = "Lambert")

''#'VModel_blending_types = [("NoBlending", "NoBlending", "NoBlending"), ("NormalBlending", "NormalBlending", "NormalBlending"),
						("AdditiveBlending", "AdditiveBlending", "AdditiveBlending"), ("SubtractiveBlending", "SubtractiveBlending", "SubtractiveBlending"),
						("MultiplyBlending", "MultiplyBlending", "MultiplyBlending"), ("AdditiveAlphaBlending", "AdditiveAlphaBlending", "AdditiveAlphaBlending")]
bpy.types.Material.VModel_blendingType = EnumProperty(name = "Blending type", description = "Blending type", items = VModel_blending_types, default = "NormalBlending")''#'

#bpy.types.Material.VModel_useVertexColors = bpy.props.BoolProperty()

class MATERIAL_PT_hello(bpy.types.Panel):
	bl_label = "VModel"
	bl_space_type = "PROPERTIES"
	bl_region_type = "WINDOW"
	bl_context = "material"

	def draw(self, context):
		layout = self.layout
		mat = context.material

		row = layout.row()
		row.label(text="Selected material: " + mat.name)

		row = layout.row()
		row.prop(mat, "VModel_materialType", text="Material type")

		#row = layout.row()
		#row.prop(mat, "VModel_blendingType", text="Blending type")

		#row = layout.row()
		#row.prop(mat, "VModel_useVertexColors", text="Use vertex colors")'''

# exporter - settings
# ==========

'''SETTINGS_FILE_EXPORT = "vmodel_settings_export.js"

import os
import json

def file_exists(filename):
	"""Return true if file exists and accessible for reading.

	Should be safer than just testing for existence due to links and
	permissions magic on Unix filesystems.

	@rtype: boolean
	"""

	try:
		f = open(filename, 'r')
		f.close()
		return True
	except IOError:
		return False

def get_settings_fullpath():
	return os.path.join(bpy.app.tempdir, SETTINGS_FILE_EXPORT)

def save_settings_export(context, properties):
	settings = {}
	for name in dir(properties): #properties.__dict__.keys():
		if name in properties:
			#Log("propName:" + name)
			settings[name] = properties[name]

	''#'
	fname = get_settings_fullpath()
	f = open(fname, "w")
	json.dump(settings, f)
	''#'

	context.scene["vModelExportSettings"] = json.dumps(settings)

def restore_settings_export(context, properties, self):
	''#'
	settings = {}
	fname = get_settings_fullpath()
	if file_exists(fname):
		f = open(fname, "r")
		''#'
		try: # maybe temp
			settings = json.load(f)
		except:
			pass
		''#'
		settings = json.load(f)
	''#'

	settings = {}
	settings = json.loads(context.scene["vModelExportSettings"]) if "vModelExportSettings" in context.scene else {}
	''#'
	try:
		settings = json.loads(context.scene["vModelExportSettings"]) if "vModelExportSettings" in context.scene else {}
	except:
		pass
	''#'
	
	defaults = {
		"option_vertices": true,
		"option_faces": true,
		"option_normals": true,

		"option_colors": true,
		"option_uv_coords": true,

		"option_skinning": true,
		"option_bones": true,

		"align_model": "None",

		"rotationDataType": "Euler Angle",
		"maxDecimalPlaces": 5,
		"writeDefaultValues": false,

		"option_animation_morph": false,
		"option_animation_skeletal": true,
		"option_frame_index_as_time": true,
	}

	for name in defaults.keys():
		self.properties[name] = defaults[name]
	for name in settings.keys():
		self.properties[name] = settings[name]

	''#'for name in settings.keys(): #dir(settings): #properties.__dict__.keys():
		Log(name + ";" + s(name in settings) + ";" + s(name in defaults))
		if name in settings or name in defaults: #not name.startswith("_"):
			self.properties[name] = settings[name] if name in settings else defaults[name]''#'
'''

# operation that sets up "globals" versions of the for-console module vars created below
# ==========

'''import bpy
class SetUpGlobals(bpy.types.Operator):
	bl_idname = "view3d.set_up_globals"
	bl_label = "Set up globals"
	@classmethod
	def poll(cls, context):
		Log("Checking for set up globals")
		if context.area.type == "CONSOLE":
			# set up their "globals" versions
			for propName in ["VTools_Main", "V", "VDebug", "VGlobals", "VTools"]:
				bpy.ops.console.clear_line()
				bpy.ops.console.insert(text = propName + " = bpy." + propName)
				bpy.ops.console.execute()
			Log("Set up globals")
		return false
	def execute(self, context):
		return {'FINISHED'}'''

'''import bpy
class SetUpGlobals(bpy.types.Operator):
	bl_idname = "view3d.set_up_globals"
	bl_label = "Set up globals"
	@classmethod
	def poll(cls, context):
		return true
	def execute(self, context):
		oldType = context.area.type
		for propName in ["VTools_Main", "V", "VDebug", "VGlobals", "VTools"]:
			bpy.ops.console.clear_line()
			bpy.ops.console.insert(text = propName + " = bpy." + propName)
			bpy.ops.console.execute()
		context.area.type = oldType
		return {'FINISHED'}
bpy.Start = bpy.ops.view3d.set_up_globals
bpy.Start()'''

'''import bpy
from bpy.app.handlers import persistent
@persistent
def PostLoad(scene):
	bpy.app.handlers.load_post.remove(PostLoad)
	Log("Post load")
	''#'oldType = bpy.context.area.type
	for propName in ["VTools_Main", "V", "VDebug", "VGlobals", "VTools"]:
		bpy.ops.console.clear_line()
		bpy.ops.console.insert(text = propName + " = bpy." + propName)
		bpy.ops.console.execute()
	bpy.context.area.type = oldType''#'

	for window in bpy.context.window_manager.windows:
		screen = window.screen
		for area in screen.areas:
			oldType = area.type
			area.type = "CONSOLE"
			for propName in ["VTools_Main", "V", "VDebug", "VGlobals", "VTools"]:
				override = {"window": window, "screen": screen, "area": area, "region": area.regions[0]}

				bpy.ops.console.clear_line(override)
				Log("Running: " + (propName + " = bpy." + propName))
				bpy.ops.console.insert(override, text = propName + " = bpy." + propName)
				bpy.ops.console.execute(override)
			area.type = oldType

			''#'if area.type == "CONSOLE":
				for region in area.regions:
					if region.type == "WINDOW":
						override = {"window": window, "screen": screen, "area": area, "region": region}
						bpy.ops.screen.screen_full_area(override)
						break''#'
bpy.app.handlers.load_post.append(PostLoad)'''

lastUpdate_area = null

import bpy
from bpy.app.handlers import persistent
@persistent
def PostUpdate(scene):
	global lastUpdate_area
	if bpy.context.area != lastUpdate_area: # if the active area just changed, ignore this call (handling a switch to a Console panel causes a crash)
		lastUpdate_area = bpy.context.area
		return

	if bpy.context.area and bpy.context.area.type == "CONSOLE": # if an area is now active, and that area is a Console panel
		bpy.app.handlers.scene_update_post.remove(PostUpdate) # remove this to have the globals set for every Console panel, rather than just the first
		Log("Setting up globals")
		oldType = bpy.context.area.type
		#bpy.context.area.type = "CONSOLE"
		for propName in ["VTools_Main", "V", "VDebug", "VGlobals", "VTools"]:
			bpy.ops.console.clear_line()
			bpy.ops.console.insert(text = propName + " = bpy." + propName)
			bpy.ops.console.execute()
		#bpy.context.area.type = oldType
bpy.app.handlers.scene_update_post.append(PostUpdate)

# registration stuff
# ==========

# old way; would go at top of file (removed--if for no other reason, because it doesn't re-run the root-level code in the submodule)
'''if "bpy" in locals():
	import imp
	#import importlib
	if "vtools" in locals():
		imp.reload(vtools)
		#importlib.reload(vtools)'''

def ReloadModules():
	Log("Reloading submodules")

	# clear modules
	import sys
	module_name = "vtools"
	for m in dict(sys.modules):
		if m[0:len(module_name) + 1] == module_name + ".":
			Log("    Reloading submodule: " + m[len(module_name) +1:])
			del sys.modules[m]
	'''try:
		Log("    Reloading main module")
		del sys.modules[module_name]
	except:
		Log("Error: Addon root is missing for module " + module_name)'''

	import vtools.v
	import vtools.vdebug
	import vtools.vglobals
	import vtools.vtools

	# make modules available to console panels
	# ==========

	import bpy
	bpy.VTools_Main = sys.modules[__name__] #["vtools"]
	bpy.V = v
	bpy.VDebug = vdebug
	bpy.VGlobals = vglobals
	bpy.VTools = bpy.VTools_Main.vtools

def register():
	#bpy.utils.register_module(__name__) #("vtools")

	ReloadModules()
def unregister():
	Nothing()
#if __name__ == "__main__":
#	register()