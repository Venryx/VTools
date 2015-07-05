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

# animation (dope sheet/graph editor)
# ==========

def AreKeyframesActive(context):
	"""Used by operators as static method to check if the user selected an object with F-Curves."""

	obj = context.active_object
	fcurves = False
	if obj:
		animdata = obj.animation_data
		if animdata:
			act = animdata.action
			if act:
				fcurves = act.fcurves
	return obj and fcurves

'''def GetBoneChannels(action, bone, channelType):
	result = []

	#next((a for a in action.groups if a.name == bone.name), null) != null:
	if len(action.groups) > 0 and Any(action.groups, lambda a:a.name == bone.name): # variant 1: groups:[{name:"Bone1", channels:[{data_path:"location"}]}]
		for groupIndex, group in action.groups.items(): # find the channel group for the given bone
			if group.name == bone.name:
				for channel in group.channels: # get all desired channels in that group
					if channelType in channel.data_path:
						result.append(channel)
	elif len(action.groups) > 0: # variant 2: groups:[{name:"Armature", channels:[{data_path:"pose.bones[\"Bone1\"].location"}]}]
		for groupIndex, group in action.groups.items():
			for channel in group.channels:
				# example: data_path == "pose.bones["ELEPHANt_ear_L_2"].location" (important note: there can be three location channels: one for x, one for y, and one for z)
				if ("[\"" + bone.name + "\"]") in channel.data_path and channelType in channel.data_path:
					result.append(channel)
	else: # variant 3: fcurves:[{data_path:"pose.bones[\"Bone1\"].location"}]
		bone_label = '"%s"' % bone.name
		for channel in action.fcurves:
			data_path = channel.data_path
			if bone_label in data_path and channelType in data_path:
				result.append(channel)

	return result
def GetKeyframe(channel, frame):
	for keyframe in channel.keyframe_points:
		if keyframe.co[0] == frame:
			return keyframe
	return null
def HasKeyframeAt(channels, frame):
	for channel in channels:
		if GetKeyframe(channel, frame) is not null:
			return true
	return false'''

class SelectKeyframesInRange(bpy.types.Operator):
	bl_idname = "graph.select_keyframes_in_range"
	bl_label = "Select keyframes in range"
	#bl_description = "Simplify all Selected FCurves aligning their keyframes"
	bl_options = {"REGISTER", "UNDO"}
	bl_space_type = "GRAPH_EDITOR"
	bl_region_type = "UI"

	firstFrame = bpy.props.IntProperty(name="First frame", description="First frame of range. (inclusive)", min = 0, max = 1000, default = 0)
	lastFrame = bpy.props.IntProperty(name="Last frame", description="Last frame of range. (inclusive)", min = 0, max = 1000, default = 0)

	@classmethod
	def poll(cls, context):
		return AreKeyframesActive(context)
	def draw(s, context):
		layout = s.layout

		row = layout.row()
		row.prop(s, "firstFrame")

		row = layout.row()
		row.prop(s, "lastFrame")
	def execute(s, context):
		obj = context.active_object
		animData = obj.animation_data
		action = animData.action
		channels = action.fcurves
		for channel in channels:
			for keyframe in channel.keyframe_points:
				keyframe.select_control_point = keyframe.co.x >= s.firstFrame and keyframe.co.x <= s.lastFrame

		return {"FINISHED"}

class CopyKeyframesToNewAction(bpy.types.Operator):
	bl_idname = "graph.copy_keyframes_to_new_action"
	bl_label = "Copy keyframes to new action"
	bl_description = "Copies the selected keyframes to a new action."
	bl_options = {"REGISTER", "UNDO"}
	bl_space_type = "GRAPH_EDITOR"
	bl_region_type = "UI"

	@classmethod
	def poll(cls, context):
		return AreKeyframesActive(context)
	def execute(self, context):
		action = context.active_object.animation_data.action
		newAction = bpy.data.actions.new("NewAction")
		newAction.use_fake_user = true
		for channel in action.fcurves:
			newChannel = newAction.fcurves.new(channel.data_path, channel.array_index, channel.group.name)
			for keyframe in channel.keyframe_points:
				if keyframe.select_control_point:
					#newChannel.keyframe_points.add(1)
					#newKeyframe = newChannel.keyframe_points[len(newChannel.keyframe_points) - 1]
					#newKeyframe.co = keyframe.co
					newKeyframe = newChannel.keyframe_points.insert(keyframe.co.x, keyframe.co.y)
					newKeyframe.handle_left = keyframe.handle_left
					newKeyframe.handle_right = keyframe.handle_right
					#channel.keyframe_points.remove(keyframe)

		return {"FINISHED"}

class MoveKeyframesTo(bpy.types.Operator):
	bl_idname = "graph.move_keyframes_to"
	bl_label = "Move keyframes to"
	bl_description = "Move keyframe-segment, such that its first-frame becomes the given frame."
	bl_options = {"REGISTER", "UNDO"}
	bl_space_type = "GRAPH_EDITOR"
	bl_region_type = "UI"

	frame = bpy.props.IntProperty(name="Frame", description="The keyframe-segment's new first-frame. (the frame at which the first-on-x-axis selected-keyframe will be placed)", min = 0, max = 1000, default = 0)

	@classmethod
	def poll(cls, context):
		return AreKeyframesActive(context)
	def execute(self, context):
		action = context.active_object.animation_data.action

		firstKeyframeIndex = 5005005
		for channel in action.fcurves:
			for keyframe in channel.keyframe_points:
				if keyframe.select_control_point:
					firstKeyframeIndex = min(firstKeyframeIndex, keyframe.co.x)
		offset = self.frame - firstKeyframeIndex

		for channel in action.fcurves:
			for keyframe in channel.keyframe_points:
				if keyframe.select_control_point:
					#keyframe.co[0] += offset
					keyframe.co.x += offset
					keyframe.handle_left.x += offset
					keyframe.handle_right.x += offset

		return {"FINISHED"}

class CopyKeyframesToNewActions(bpy.types.Operator):
	bl_idname = "graph.copy_keyframes_to_new_actions"
	bl_label = "Copy keyframes to new actions"
	#bl_description = ""
	bl_options = {"REGISTER", "UNDO"}
	bl_space_type = "GRAPH_EDITOR"
	bl_region_type = "UI"

	moveNewActionKeyframesToFrame0 = bpy.props.BoolProperty(default = true)
	start = bpy.props.BoolProperty(default = false)

	for i in range(1, 11):
		exec("action" + s(i) + "_name = bpy.props.StringProperty(name = \"" + s(i) + ") Name\", default = \"Action " + s(i) + "\")")
		exec("action" + s(i) + "_firstFrame = bpy.props.IntProperty(name = \"First frame\")")
		exec("action" + s(i) + "_lastFrame = bpy.props.IntProperty(name = \"Last frame\")")

	@classmethod
	def poll(cls, context):
		return AreKeyframesActive(context)
	def draw(self, context):
		layout = self.layout

		row = layout.row()
		row.prop(self.properties, "moveNewActionKeyframesToFrame0", "Move new action keyframes to frame 0")
		layout.separator()

		row = layout.row()
		row.prop(self.properties, "start", "Start")
		layout.separator()

		for i in range(1, 11):
			row = layout.row()
			row.prop(self.properties, "action" + s(i) + "_name")

			row = layout.row()
			row.prop(self.properties, "action" + s(i) + "_firstFrame")

			row = layout.row()
			row.prop(self.properties, "action" + s(i) + "_lastFrame")
	def execute(self, context):
		if not self.start:
			return {"FINISHED"}

		action = context.active_object.animation_data.action
		for i in range(1, 11):
			name = eval("self.action" + s(i) + "_name")
			firstFrame = eval("self.action" + s(i) + "_firstFrame")
			lastFrame = eval("self.action" + s(i) + "_lastFrame")

			firstKeyframeIndex = 0
			if self.moveNewActionKeyframesToFrame0:
				firstKeyframeIndex = 5005005
				for channel in action.fcurves:
					for keyframe in channel.keyframe_points:
						if keyframe.co.x >= firstFrame and keyframe.co.x <= lastFrame:
							firstKeyframeIndex = min(firstKeyframeIndex, keyframe.co.x)

			if lastFrame - firstFrame > 0:
				newAction = bpy.data.actions.new(name)
				newAction.use_fake_user = true
				for channel in action.fcurves:
					newChannel = newAction.fcurves.new(channel.data_path, channel.array_index, channel.group.name)
					for keyframe in channel.keyframe_points:
						if keyframe.co.x >= firstFrame and keyframe.co.x <= lastFrame:
							newKeyframe = newChannel.keyframe_points.insert(keyframe.co.x - firstKeyframeIndex, keyframe.co.y)
							newKeyframe.handle_left = [keyframe.handle_left.x - firstKeyframeIndex, keyframe.handle_left.y]
							newKeyframe.handle_right = [keyframe.handle_right.x - firstKeyframeIndex, keyframe.handle_right.y]

		return {"FINISHED"}

# 3d view
# ==========

class SetOriginTo3DCursor_KeepLinkedObjectPositions(bpy.types.Operator):
	bl_idname = "view3d.set_origin_to_3d_cursor__keep_linked_object_positions"
	bl_label = "Set origin to 3D cursor - keep linked object positions"
	@classmethod
	def poll(cls, context):
		return context.active_object is not null
	def execute(self, context):
		# todo

		return {"FINISHED"}

# registration stuff
# ==========

bpy.utils.register_module("vtools")