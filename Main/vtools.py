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

def AreKeyframesLoaded(context):
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
		return AreKeyframesLoaded(context)
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
		return AreKeyframesLoaded(context)
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

class RetargetAction(bpy.types.Operator):
	bl_idname = "graph.retarget_action"
	bl_label = "Retarget action"
	bl_description = "Transforms the action's keyframes to be based-on/relative-to the active-object's armature's rest-pose, rather than the specified source-object's armature's rest-pose."
	bl_options = {"REGISTER", "UNDO"}
	bl_space_type = "GRAPH_EDITOR"
	bl_region_type = "UI"

	sourceObjectName = bpy.props.StringProperty(name = "Source object name")

	@classmethod
	def poll(cls, context):
		return AreKeyframesLoaded(context)
	def execute(self, context):
		action = context.active_object.animation_data.action

		#enderFrame = int(action.frame_range[1]) + 1
		#for frame in range(0, enderFrame): # process all frames

		for channelIndex, firstChannel in enumerate(action.fcurves):
			if firstChannel.array_index is not 0: # only run this process for the first of each channel-group
				continue

			if len(action.fcurves) > channelIndex + 3 and action.fcurves[channelIndex + 3].array_index == 3: # if channel-group has a fourth item (for a Vector4's "w" component)
				channels = action.fcurves[channelIndex:channelIndex + 4]
			else:
				channels = action.fcurves[channelIndex:channelIndex + 3]

			sourceObj = Obj(self.sourceObjectName)
			if sourceObj == null:
				return {"FINISHED"}
			boneName = firstChannel.data_path[firstChannel.data_path.find("\"") + 1:firstChannel.data_path.rfind("\"")]
			sourcePoseBone = sourceObj.pose.bones[boneName] #[a for a in sourceObj.pose.bones if a.name == boneName][0]
			obj = context.active_object
			poseBone = obj.pose.bones[boneName] #[a for a in obj.pose.bones if a.name == boneName][0]

			#newBoneToBoneMatrix = poseBone.bone.GetMatrix_Object().inverted() * sourcePoseBone.bone.GetMatrix_Object()
			newBoneToBoneMatrix = poseBone.bone.GetMatrix().inverted() * sourcePoseBone.bone.GetMatrix()

			'''if ".location" in firstChannel.data_path:
				#channels_matrix = Vector((channels[0], channels[1], channels[2])).to_matrix()
				channels_matrix = mathutils.Matrix.Translation((channels[0], channels[1], channels[2]))
			elif ".rotation_quaternion" in firstChannel.data_path:
				channels_matrix = Quaternion((channels[0], channels[1], channels[2], channels[3])).to_matrix()
			elif ".scale" in firstChannel.data_path:
				#channels_matrix = Vector((channels[0], channels[1], channels[2])).to_matrix()
				channels_matrix = mathutils.Matrix.Scale(1, 4, (channels[0], channels[1], channels[2]))'''

			for i, keyframe_ignored in enumerate(firstChannel.keyframe_points): # assumes that the channel-group's keyframe-points are all aligned on the same x-axis points
				if ".location" in firstChannel.data_path:
					vector = Vector((channels[0].keyframe_points[i].co[1], channels[1].keyframe_points[i].co[1], channels[2].keyframe_points[i].co[1]))
					newVector = newBoneToBoneMatrix * vector
				elif ".rotation_quaternion" in firstChannel.data_path:
					vector = Quaternion((channels[0].keyframe_points[i].co[1], channels[1].keyframe_points[i].co[1], channels[2].keyframe_points[i].co[1], channels[3].keyframe_points[i].co[1]))
					#newVector = newBoneToBoneMatrix * vector
					vector.rotate(newBoneToBoneMatrix)
					newVector = vector
				elif ".scale" in firstChannel.data_path:
					vector = Vector((channels[0].keyframe_points[i].co[1], channels[1].keyframe_points[i].co[1], channels[2].keyframe_points[i].co[1]))
					#newVector = newBoneToBoneMatrix * vector
					newVector = vector # todo: add correct handling for scale

				for i2 in range(0, len(channels)):
					channel = channels[i2]
					keyframe = channel.keyframe_points[i]
					newComp = newVector[i2]
					compOffset = newComp - keyframe.co.y

					keyframe.co.y += compOffset
					keyframe.handle_left.y += compOffset
					keyframe.handle_right.y += compOffset

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
		return AreKeyframesLoaded(context)
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
		exec("action" + S(i) + "_name = bpy.props.StringProperty(name = \"" + S(i) + ") Name\", default = \"Action " + S(i) + "\")")
		exec("action" + S(i) + "_firstFrame = bpy.props.IntProperty(name = \"First frame\")")
		exec("action" + S(i) + "_lastFrame = bpy.props.IntProperty(name = \"Last frame\")")

	@classmethod
	def poll(cls, context):
		return AreKeyframesLoaded(context)
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
			row.prop(self.properties, "action" + S(i) + "_name")

			row = layout.row()
			row.prop(self.properties, "action" + S(i) + "_firstFrame")

			row = layout.row()
			row.prop(self.properties, "action" + S(i) + "_lastFrame")
	def execute(self, context):
		if not self.start:
			return {"FINISHED"}

		action = context.active_object.animation_data.action
		for i in range(1, 11):
			name = eval("self.action" + S(i) + "_name")
			firstFrame = eval("self.action" + S(i) + "_firstFrame")
			lastFrame = eval("self.action" + S(i) + "_lastFrame")

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

'''class SetOriginTo3DCursor_KeepLinkedObjectPositions(bpy.types.Operator):
	bl_idname = "view3d.set_origin_to_3d_cursor__keep_linked_object_positions"
	bl_label = "Set origin to 3D cursor - keep linked object positions"
	bl_options = {"REGISTER", "UNDO"}
	@classmethod
	def poll(cls, context):
		#return context.active_object is not null
		return Active() is not null
	def execute(self, context):
		# todo

		return {"FINISHED"}'''

class FocusOnSelectedVertexes(bpy.types.Operator):
	bl_idname = "view3d.focus_on_selected_vertexes"
	bl_label = "Focus on selected vertexes"
	bl_options = {"REGISTER", "UNDO"}
	@classmethod
	def poll(cls, context):
		return ActiveVertex() is not null
	def execute(self, context):
		oldCursorPos = bpy.context.scene.cursor_location.copy()
		bpy.ops.view3d.snap_cursor_to_selected()
		bpy.ops.view3d.view_center_cursor()
		bpy.context.scene.cursor_location = oldCursorPos

		return {"FINISHED"}

class SetPosition_Local(bpy.types.Operator):
	bl_idname = "view3d.set_position__local"
	bl_label = "Set position - local"
	#bl_description = "Set's the active object's local position to that specified."
	bl_options = {"REGISTER", "UNDO"}
	#bl_space_type = "GRAPH_EDITOR"
	bl_region_type = "UI"

	x = bpy.props.FloatProperty(name="X", description="X component of new local position.")
	y = bpy.props.FloatProperty(name="Y", description="Y component of new local position.")
	z = bpy.props.FloatProperty(name="Z", description="Z component of new local position.")
	moveChildren = bpy.props.BoolProperty(name="Move children", description="Whether to have the active-object's childrens' world-positions change as well.", default=true)

	#childOldWorldPositions = null

	@classmethod
	def poll(cls, context):
		return Active() is not null
	def execute(s, context):
		obj = Active()

		'''childOldWorldPositions = {}
		for child in obj.children:
			childOldWorldPositions[child] = child.location.copy()'''
		'''if s.childOldWorldPositions == null:
			s.childOldWorldPositions = {}
			for child in obj.children:
				s.childOldWorldPositions[child.name] = child.location.copy()
				Log("Storing:" + S(s.childOldWorldPositions[child.name]))'''

		#obj.parent.ToLocal(obj.location)
		offset = Vector((s.x, s.y, s.z)) - obj.matrix_local.decompose()[0]
		obj.matrix_local *= Matrix.Translation(offset)

		for child in obj.children:
			#child.matrix_local = child.matrix_local
			child.location = child.location

		childCounterOffset = -obj.ToLocal(obj.parent.ToWorld(offset))
		if not s.moveChildren:
			for child in obj.children:
				#child.matrix_local *= Matrix.Translation(-offset)
				'''Log("Loading:" + S(s.childOldWorldPositions[child.name]))
				child.location = s.childOldWorldPositions[child.name]'''
				child.location += childCounterOffset

		return {"FINISHED"}

# registration stuff
# ==========

bpy.utils.register_module("vtools")