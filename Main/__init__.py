#__all__ = ["v", "vdebug", "vglobals", "vtools"]
import vtools.v
import vtools.vdebug
import vtools.vclassextensions
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

# remove old post-update function from event-listener-list
#if PostUpdate in bpy.app.handlers.scene_update_post:
#	bpy.app.handlers.scene_update_post.append(PostUpdate)
#	Log("removing(1)")

lastUpdate_area = null

processedConsoles = {}

import bpy
import inspect
from bpy.app.handlers import persistent
@CallFuncWithRefToItself
@persistent
def PostUpdate(m, scene):
	if m is not PostUpdate.m:
		bpy.app.handlers.scene_update_post.remove(m.wrapper) # only ever have the latest PostUpdate function in listener-list
		return

	global lastUpdate_area
	if bpy.context.area != lastUpdate_area: # if the active area just changed, ignore this call (handling a switch to a Console panel causes a crash)
		lastUpdate_area = bpy.context.area
		return

	if bpy.context.area and bpy.context.area.type == "CONSOLE" and bpy.context.area not in processedConsoles: # if an area is now active, that area is a Console panel, and we haven't already processed it
		#bpy.app.handlers.scene_update_post.remove(m.wrapper)
		processedConsoles[bpy.context.area] = true

		Log("Setting up globals")
		oldType = bpy.context.area.type
		#bpy.context.area.type = "CONSOLE"

		codeStr = ""
		for propName in ["VTools_Main", "V", "VDebug", "VClassExtensions", "VGlobals", "VTools"]:
			codeStr += ("; " if len(codeStr) > 0 else "") + propName + " = bpy." + propName
		#for propName in dir(bpy.VGlobals): #bpy.VGlobals:
		#for propName in inspect.isfunction(func):
		for key, value in inspect.getmembers(bpy.VGlobals):
			if inspect.getmodule(value) == bpy.VGlobals: # VGlobals: functions (which includes classes)
				codeStr += "; " + key + " = bpy.VGlobals." + key
		for propName in ["null", "false", "true"]: # VGlobals: variables (we have to add these manually)
			codeStr += "; " + propName + " = bpy.VGlobals." + propName
		#codeStr += "; v = V.VWrap"

		#bpy.ops.console.execute()
		bpy.ops.console.clear_line()
		bpy.ops.console.insert(text = codeStr)
		bpy.ops.console.execute()
		#exec(codeStr)

		#bpy.context.area.type = oldType
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
	import vtools.vclassextensions
	import vtools.vtools

	# make modules available to console panels
	# ==========

	import bpy
	bpy.VTools_Main = sys.modules[__name__] #["vtools"]
	bpy.V = v
	bpy.VDebug = vdebug
	bpy.VClassExtensions = vclassextensions
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