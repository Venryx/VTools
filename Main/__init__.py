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

# creates event handler that waits for a Console panel to be opened, and then sets up "globals" for each of the submodules attached to the "bpy" object
# ==========

lastUpdate_area = null
inPostUpdate = false

import bpy
import inspect
from bpy.app.handlers import persistent
@persistent
def PostUpdate(scene):
	global inPostUpdate, lastUpdate_area
	if inPostUpdate:
		return
	if bpy.context.area != lastUpdate_area: # if the active area just changed, ignore this call (handling a switch to a Console panel causes a crash)
		lastUpdate_area = bpy.context.area
		return
	inPostUpdate = true

	if bpy.context.area and bpy.context.area.type == "CONSOLE": # if an area is now active, and that area is a Console panel
		if PostUpdate in bpy.app.handlers.scene_update_post: # figure out why this is needed
			bpy.app.handlers.scene_update_post.remove(PostUpdate) # remove this to have the globals set for every Console panel, rather than just the first
		Log("Setting up globals")
		oldType = bpy.context.area.type
		#bpy.context.area.type = "CONSOLE"

		codeStr = ""
		for propName in ["VTools_Main", "V", "VDebug", "VGlobals", "VTools"]:
			codeStr += ("; " if len(codeStr) > 0 else "") + propName + " = bpy." + propName
		#for propName in dir(bpy.VGlobals): #bpy.VGlobals:
		#for propName in inspect.isfunction(func):
		for key, value in inspect.getmembers(bpy.VGlobals):
			if inspect.getmodule(value) == bpy.VGlobals: # VGlobals: functions (which includes classes)
				codeStr += "; " + key + " = bpy.VGlobals." + key
		for propName in ["null", "false", "true"]: # VGlobals: variables (we have to add these manually)
			codeStr += "; " + propName + " = bpy.VGlobals." + propName
		bpy.ops.console.clear_line() # todo: fix infinite-loop crash from this line (or rather, with the in-post-update fix: fix the code-input-being-blocked issue from this line)
		bpy.ops.console.insert(text = codeStr)
		bpy.ops.console.execute()
		#exec(codeStr)

		#bpy.context.area.type = oldType

	inPostUpdate = false
if PostUpdate not in bpy.app.handlers.scene_update_post:
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

def ReloadModules(): # doesn't reload itself (this root/init module), because that already happens when the F8 button is pressed (also, I don't know how to have it do so)
	# clear submodules
	import sys
	module_name = "vtools"
	Log("Reloading submodules for " + module_name)
	for m in dict(sys.modules):
		if m[0:len(module_name) + 1] == module_name + ".":
			Log("    Reloading submodule: " + m[len(module_name) +1:])
			del sys.modules[m]

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
	#bpy.utils.register_module(__name__)
	ReloadModules()
def unregister():
	#bpy.utils.unregister_module(__name__)
	pass
#if __name__ == "__main__":
#	register()