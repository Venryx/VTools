from vtools import *
from vtools.vglobals import *

import bpy
import mathutils

import shutil
import os
import os.path
import math
from math import fabs
import operator
import random
import re

import bmesh

# operators
# ==========

class SetOriginTo3DCursor_KeepLinkedObjectPositions(bpy.types.Operator):
	bl_idname = "view3d.test0"
	bl_label = "Set origin to 3D cursor - keep linked object positions"
	@classmethod
	def poll(cls, context):
		return context.active_object is not null
	def execute(self, context):
		# todo

		return {'FINISHED'}

class Test1(bpy.types.Operator):
	bl_idname = "view3d.test1"
	bl_label = "Test1"
	@classmethod
	def poll(cls, context):
		return context.active_object is not null
	def execute(self, context):
		# todo

		return {'FINISHED'}

# registration stuff
# ==========

bpy.utils.register_module("vtools")