from vtools import *
from vtools.vglobals import *
# maybe temp
from vtools.vclassextensions import *

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
			if boneName not in sourceObj.pose.bones: # if bone isn't in source armature, we must have recently added it (and added keyframes for it); just leave its keyframes alone
				continue
			sourcePoseBone = sourceObj.pose.bones[boneName] #[a for a in sourceObj.pose.bones if a.name == boneName][0]
			obj = context.active_object
			if boneName not in obj.pose.bones: # if bone isn't in selected armature, we must have recently deleted it (but left keyframes for it); just leave its keyframes alone
				continue
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

'''class DeleteUnusedChannels(bpy.types.Operator):
	bl_idname = "graph.delete_unused_channels"
	bl_label = "Delete unused channels"
	bl_description = "Delete each channel that is not matched by a bone in the active armature."
	bl_options = {"REGISTER", "UNDO"}
	bl_space_type = "GRAPH_EDITOR"
	bl_region_type = "UI"

	@classmethod
	def poll(cls, context):
		return AreKeyframesLoaded(context)
	def execute(self, context):
		action = context.active_object.animation_data.action

		for channel in action.fcurves:
			# todo

		return {"FINISHED"}'''

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

		childCounterOffset = -obj.ToLocal(obj.parent.ToWorld(offset, false), false)
		if not s.moveChildren:
			for child in obj.children:
				#Log("Moving child by:" + S(childCounterOffset))
				#child.matrix_local *= Matrix.Translation(-offset)
				'''Log("Loading:" + S(s.childOldWorldPositions[child.name]))
				child.location = s.childOldWorldPositions[child.name]'''
				child.location += childCounterOffset

		return {"FINISHED"}

class reset_scale_while_preserving_world_space_mesh(bpy.types.Operator):
	bl_idname = "view3d.reset_scale_while_preserving_world_space_mesh"
	bl_label = "Reset scale while preserving world space mesh"
	#bl_description = "Set's the active object's local position to that specified."
	bl_options = {"REGISTER", "UNDO"}
	bl_region_type = "UI"

	@classmethod
	def poll(cls, context):
		return Active() is not null
	def execute(s, context):
		obj = Active()

		scale = obj.scale

		#vertexes = obj.data.vertices
		vertexes = obj.Vertexes() # enables it to work in both Object and Edit mode
		for vertex in vertexes:
			vertex.co = (vertex.co.x * scale.x, vertex.co.y * scale.y, vertex.co.z * scale.z)
		#vertexes.SaveMesh()

		obj.scale = Vector((1, 1, 1))

		return {"FINISHED"}
		
class separate_islands_into_different_objects(bpy.types.Operator):
	bl_idname = "view3d.separate_islands_into_different_objects"
	bl_label = "Separate islands into different objects"
	#bl_description = "Set's the active object's local position to that specified."
	bl_options = {"REGISTER", "UNDO"}
	bl_region_type = "UI"

	@classmethod
	def poll(cls, context):
		return Active() is not null
	def execute(s, context):
		oldSelectMode = context.tool_settings.mesh_select_mode
		context.tool_settings.mesh_select_mode = [true, false, false]
	
		obj = Active()
		vertexes = obj.Vertexes() # enables it to work in both Object and Edit mode
		#runCount = 0
		#while len(vertexes) > 0 and runCount < 100:
		while len(vertexes) > 0:
			vertex = vertexes[0]
			vertex.select = true
			bpy.ops.mesh.select_linked()
			bpy.ops.mesh.separate()
			
			SaveMesh()			
			vertexes = obj.Vertexes()
			#runCount += 1
			
		context.tool_settings.mesh_select_mode = oldSelectMode

		return {"FINISHED"}

class create_armature_from_object_heirarchy(bpy.types.Operator):
	bl_idname = "view3d.create_armature_from_object_heirarchy"
	bl_label = "Create armature from object heirarchy"
	bl_options = {"REGISTER", "UNDO"}
	bl_region_type = "UI"

	@classmethod
	def poll(cls, context):
		return Active() is not null
	def execute(s, context):
		obj = Active()
		
		# create armature and object
		bpy.ops.object.add(type="ARMATURE", enter_editmode=True, location=obj.location)
		armatureObj = bpy.context.object
		armatureObj.parent = obj.parent
		armatureObj.name = obj.name + "_Armature"
		armatureObj.matrix_world = obj.matrix_world
		armature = armatureObj.data
		armature.name = obj.name + "_Armature"

		# create bones
		bpy.ops.object.mode_set(mode="EDIT")
		rootBone = armature.edit_bones.new("RequiredYetUnusedRootBone")
		create_armature_from_object_heirarchy.AddBonesFromObjectHeirarchy(obj, armature, rootBone, [obj])
		bpy.ops.object.mode_set(mode="OBJECT")
		
		return {"FINISHED"}

	def AddBonesFromObjectHeirarchy(rootObj, armature, parent, objects):
		for obj in objects:
			bone = armature.edit_bones.new(obj.name)

			'''bone.use_inherit_rotation = false
			bone.use_inherit_scale = false
			bone.use_local_location = false'''

			if parent:
				bone.parent = parent
				#bone.head = parent.tail
				#bone.head = obj.location * obj.parent.scale
				bone.head = obj.location * Matrix.Scale(1, 4, obj.parent.scale)
				
				#bone.use_connect = false
				#(trans, rot, scale) = parent.matrix.decompose()
				#(trans, rot, scale) = obj.matrix_local.decompose()
				'''objMatrix = obj.matrix_world
				if parent == null:
					objMatrix = v.unfixMatrixForRootBone(objMatrix)
				(trans, rot, scale) = objMatrix.decompose()'''

				#bone.matrix_local = parent.matrix_local * obj.matrix_local
				#bone.matrix = parent.matrix * obj.matrix_local

				parentBoneMatrix_inverted = Matrix.Translation((0, 0, 0)) if parent.name == "RequiredYetUnusedRootBone" else Matrix.Translation(obj.parent.location).inverted()
				bone.matrix = rootObj.matrix_world.inverted() * obj.matrix_world
				#bone.matrix = parentBoneMatrix_inverted * obj.matrix_world
				corners = obj.GetCorners()
				corners.sort(key=lambda a:(Vector(a) - bone.head).length)
				#bone.tail = (parentBoneMatrix_inverted * obj.matrix_world) * Vector(corners[-1])
				bone.tail = (rootObj.matrix_world.inverted() * obj.matrix_world) * Vector(corners[-1])

				# make-so: this uses center of farthest face, rather than farthest corner (e.g. obj.GetExtentCenters())

				'''objMatrix_withFarthestCornerAdded = obj.matrix_world
				corners = obj.GetCorners()
				corners.sort(key=lambda a:(Vector(a) - bone.head).length)
				bone.matrix = rootObj.matrix_world.inverted() * obj.matrix_world
				bone.length = (Vector(corners[-1]) - bone.head).length'''
			else:
				#bone.head = (0,0,0)
				#rot = Matrix.Translation((0,0,0)) # identity matrix
				#bone.matrix = Matrix.Translation(obj.parent.location).inverted() * obj.matrix_world
				pass
			#bone.tail = (rot * Vector(obj.location)) + bone.head
			#bone.tail = (rot * Vector(obj.GetLocation(true))) + bone.head
			#bone.tail = bone.head + Vector((0, 1, 0)) # + (rot * Vector((0, 1, 0)))

			create_armature_from_object_heirarchy.AddBonesFromObjectHeirarchy(rootObj, armature, bone, obj.children)

class convert_action_curves_to_datapath_approach(bpy.types.Operator):
	bl_idname = "graph.convert_action_curves_to_datapath_approach"
	bl_label = "Convert action curves to datapath approach"
	bl_description = "Converts the active-action's curves from the [bone-name = group-name, component = data-path] approach, to the [bone-name = data-path-part, component = data-path-part] approach"
	bl_options = {"REGISTER", "UNDO"}
	bl_space_type = "GRAPH_EDITOR"
	bl_region_type = "UI"

	@classmethod
	def poll(cls, context):
		return AreKeyframesLoaded(context)
	def execute(s, context):
		#action = context.active_object.animation_data.action
		action = ActiveAction()
		for curve in action.fcurves:
			if not ("[\"" in curve.data_path and "\"]." in curve.data_path): # if using old approach
				curve.data_path = "pose.bones[\"" + curve.group.name + "\"]." + curve.data_path
				#curve.group = null

		return {"FINISHED"}

class convert_action_rotation_curves_to_quaternion_type(bpy.types.Operator):
	bl_idname = "graph.convert_action_rotation_curves_to_quaternion_type"
	bl_label = "Convert action rotation curves to quaternion type"
	bl_description = "Converts the active-action's rotation curves from the 3-prop euler type, to the 4-prop quaternion type."
	bl_options = {"REGISTER", "UNDO"}
	bl_space_type = "GRAPH_EDITOR"
	bl_region_type = "UI"

	@classmethod
	def poll(cls, context):
		return AreKeyframesLoaded(context)
	def execute(s, context):
		obj = Active()
		action = ActiveAction()

		curvesToConvert_bones = []
		for curve in action.fcurves:
			if curve.GetPropertyName() == "rotation_euler" and curve.array_index == 0:
				curvesToConvert_bones.append(curve.GetBoneName())

		for boneName in curvesToConvert_bones:
			rotationChannel_x = [a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "rotation_euler" and a.array_index == 0][0]
			rotationChannel_y = [a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "rotation_euler" and a.array_index == 1][0]
			rotationChannel_z = [a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "rotation_euler" and a.array_index == 2][0]

			newRotationChannel_x = action.fcurves.new("pose.bones[\"" + boneName + "\"].rotation_quaternion", 1, boneName)
			newRotationChannel_y = action.fcurves.new("pose.bones[\"" + boneName + "\"].rotation_quaternion", 2, boneName)
			newRotationChannel_z = action.fcurves.new("pose.bones[\"" + boneName + "\"].rotation_quaternion", 3, boneName)
			newRotationChannel_w = action.fcurves.new("pose.bones[\"" + boneName + "\"].rotation_quaternion", 0, boneName) # the array_index for w is 0
			
			for i, keyframe in enumerate(rotationChannel_x.keyframe_points): # assumes that the channel-group's keyframe-points are all aligned on the same x-axis points
				rotation = Euler((rotationChannel_x.keyframe_points[i].co[1], rotationChannel_y.keyframe_points[i].co[1], rotationChannel_z.keyframe_points[i].co[1]), "XYZ").to_quaternion()
				newKeyframeX = newRotationChannel_x.keyframe_points.insert(keyframe.co.x, rotation.x)
				newKeyframeY = newRotationChannel_y.keyframe_points.insert(keyframe.co.x, rotation.y)
				newKeyframeZ = newRotationChannel_z.keyframe_points.insert(keyframe.co.x, rotation.z)
				newKeyframeW = newRotationChannel_w.keyframe_points.insert(keyframe.co.x, rotation.w)

			action.fcurves.remove(rotationChannel_x)
			action.fcurves.remove(rotationChannel_y)
			action.fcurves.remove(rotationChannel_z)

		return {"FINISHED"}

class replace_action_curve_bones(bpy.types.Operator):
	bl_idname = "graph.replace_action_curve_bones"
	bl_label = "Replace action curve bones"
	bl_description = "For each curve linked with old-bone-name, relink to new-bone-name."
	bl_options = {"REGISTER", "UNDO"}
	bl_space_type = "GRAPH_EDITOR"
	bl_region_type = "UI"

	oldBoneName = bpy.props.StringProperty(name = "Old Bone")
	newBoneName = bpy.props.StringProperty(name = "New Bone")

	@classmethod
	def poll(cls, context):
		return AreKeyframesLoaded(context)
	def draw(s, context):
		layout = s.layout

		row = layout.row()
		row.prop(s.properties, "oldBoneName")

		row = layout.row()
		row.prop(s.properties, "newBoneName")
	def execute(s, context):
		if s.oldBoneName == "" or s.newBoneName == "":
			return {"FINISHED"}

		action = ActiveAction()
		for curve in action.fcurves:
			if v.GetBoneNameFromDataPath(curve.data_path) == s.oldBoneName:
				curve.data_path = "pose.bones[\"" + s.newBoneName + "\"]." + v.GetPropertyNameFromDataPath(curve.data_path)

		return {"FINISHED"}

class create_merged_action_from_actions(bpy.types.Operator):
	bl_idname = "graph.create_merged_action_from_actions"
	bl_label = "Create merged action from actions"
	bl_options = {"REGISTER", "UNDO"}
	bl_space_type = "GRAPH_EDITOR"
	bl_region_type = "UI"

	start = bpy.props.BoolProperty(default = false)
	name = bpy.props.StringProperty(name = "Name", default = "MergedAction")

	for i in range(1, 11):
		'''defaultActionName = bpy.data.actions[i - 1] if len(bpy.data.actions) >= i else ""
		exec("action" + S(i) + "_name = bpy.props.StringProperty(name = \"" + S(i) + ") Name\", default = \"" + defaultActionName + "\")")'''
		exec("action" + S(i) + "_name = bpy.props.StringProperty(name = \"" + S(i) + ") Name\", default = \"Action " + S(i) + "\")")

	@classmethod
	def poll(cls, context):
		return AreKeyframesLoaded(context)
	def draw(s, context):
		layout = s.layout

		row = layout.row()
		row.prop(s.properties, "start", "Start")
		layout.separator()

		row = layout.row()
		row.prop(s.properties, "name")

		for i in range(1, 11):
			row = layout.row()
			row.prop(s.properties, "action" + S(i) + "_name")

			if eval("s.action" + S(i) + "_name") == "[auto]" and len(bpy.data.actions) >= i:
				exec("s.action" + S(i) + "_name = \"" + bpy.data.actions[i - 1].name + "\"")
	def execute(s, context):
		if not s.start:
			return {"FINISHED"}

		name = s.name
		newAction = bpy.data.actions.new(name)
		newAction.use_fake_user = true
		for i in range(1, 11):
			name = eval("s.action" + S(i) + "_name")
			if len(name) == 0:
				continue

			action = bpy.data.actions[name]
			for channel in action.fcurves:
				newChannel = newAction.fcurves.new(channel.data_path, channel.array_index, channel.group.name)
				for keyframe in channel.keyframe_points:
					newKeyframe = newChannel.keyframe_points.insert(keyframe.co.x, keyframe.co.y)
					newKeyframe.handle_left = [keyframe.handle_left.x, keyframe.handle_left.y]
					newKeyframe.handle_right = [keyframe.handle_right.x, keyframe.handle_right.y]

		return {"FINISHED"}

class retarget_action_from_object_heirarchy_to_armature(bpy.types.Operator):
	bl_idname = "graph.retarget_action_from_object_heirarchy_to_armature"
	bl_label = "Retarget retarget action from object heirarchy to armature"
	bl_description = "Transforms the action's keyframes to be based-on/relative-to the active-object's armature's rest-pose, rather than the specified source-object's rest-pose."
	bl_options = {"REGISTER", "UNDO"}
	bl_space_type = "GRAPH_EDITOR"
	bl_region_type = "UI"

	sourceObjectName = bpy.props.StringProperty(name = "Source object name")

	@classmethod
	def poll(cls, context):
		return AreKeyframesLoaded(context)
	def execute(self, context):
		obj = Active()
		action = ActiveAction()
		sourceObj = Obj(self.sourceObjectName)
		if sourceObj == null:
			return {"FINISHED"}

		'''for channelIndex, firstChannel in enumerate(action.fcurves):
			if firstChannel.array_index is not 0: # only run this process for the first of each channel-group
				continue

			if len(action.fcurves) > channelIndex + 3 and action.fcurves[channelIndex + 3].array_index == 3: # if channel-group has a fourth item (for a Vector4's "w" component)
				channels = action.fcurves[channelIndex:channelIndex + 4]
			else:
				channels = action.fcurves[channelIndex:channelIndex + 3]

			#boneName = firstChannel.data_path[firstChannel.data_path.find("\"") + 1:firstChannel.data_path.rfind("\"")]
			boneName = firstChannel.group.name
			
			if len([a for a in sourceObj.GetDescendents() if a.name == boneName]) == 0:
				raise ValueError("Couldn't find source-bone-obj with name: " + boneName)
			sourceBone = [a for a in sourceObj.GetDescendents() if a.name == boneName][0]

			obj = context.active_object
			if boneName not in obj.pose.bones: # if bone isn't in selected armature, we must have recently deleted it (but left keyframes for it); just leave its keyframes alone
				continue
			poseBone = obj.pose.bones[boneName] #[a for a in obj.pose.bones if a.name == boneName][0]

			#newBoneToBoneMatrix = poseBone.bone.GetMatrix_Object().inverted() * sourcePoseBone.bone.GetMatrix_Object()
			#newBoneToBoneMatrix = poseBone.bone.GetMatrix().inverted() * sourcePoseBone.bone.GetMatrix()
			newBoneToBoneMatrix = Quaternion([.707107, 0, 0, -.707107]).inverted().to_matrix().to_4x4() * (sourceObj.matrix_world.inverted() * sourceBone.matrix_world).inverted() * poseBone.bone.GetMatrix()

			for i, keyframe_ignored in enumerate(firstChannel.keyframe_points): # assumes that the channel-group's keyframe-points are all aligned on the same x-axis points
				if "location" in firstChannel.data_path:
					pos = Vector((channels[0].keyframe_points[i].co[1], channels[1].keyframe_points[i].co[1], channels[2].keyframe_points[i].co[1]))
					newData = newBoneToBoneMatrix * pos
				elif "rotation_euler" in firstChannel.data_path:
					#rotation = Vector((channels[0].keyframe_points[i].co[1], channels[1].keyframe_points[i].co[1], channels[2].keyframe_points[i].co[1])).to_quaternion()
					rotation = Euler((channels[0].keyframe_points[i].co[1], channels[1].keyframe_points[i].co[1], channels[2].keyframe_points[i].co[1]), "XYZ").to_quaternion()
					#newData = newBoneToBoneMatrix * rotation
					rotation.rotate(newBoneToBoneMatrix)
					newData = rotation.to_euler("XYZ")
					# maybe make-so: channels are changed to [quaternion/4-component]-based, rather than modifying [vector/3-component]-based channels
				elif "rotation_quaternion" in firstChannel.data_path:
					rotation = Quaternion((channels[0].keyframe_points[i].co[1], channels[1].keyframe_points[i].co[1], channels[2].keyframe_points[i].co[1], channels[3].keyframe_points[i].co[1]))
					#newData = newBoneToBoneMatrix * rotation
					rotation.rotate(newBoneToBoneMatrix)
					newData = rotation
				elif "scale" in firstChannel.data_path:
					scale = Vector((channels[0].keyframe_points[i].co[1], channels[1].keyframe_points[i].co[1], channels[2].keyframe_points[i].co[1]))
					#newData = newBoneToBoneMatrix * scale
					newData = scale # todo: add correct handling for scale
				else: # found no handler for this channel's data
					break

				for i2 in range(0, len(channels)):
					channel = channels[i2]
					keyframe = channel.keyframe_points[i]
					newComp = newData[i2]
					compOffset = newComp - keyframe.co.y

					keyframe.co.y += compOffset
					keyframe.handle_left.y += compOffset
					keyframe.handle_right.y += compOffset'''

		curvesToModify_bones = []
		for curve in action.fcurves:
			# (if bone isn't in selected armature, we must have recently deleted it (but left keyframes for it); just ignore its curve)
			if curve.GetBoneName() in obj.pose.bones and curve.GetBoneName() not in curvesToModify_bones:
				curvesToModify_bones.append(curve.GetBoneName())
		for boneName in curvesToModify_bones:
			if len([a for a in sourceObj.GetDescendents() if a.name == boneName]) == 0:
				raise ValueError("Couldn't find source-bone-obj with name: " + boneName)
			sourceBone = [a for a in sourceObj.GetDescendents() if a.name == boneName][0]
			bone = obj.pose.bones[boneName]
			#sourceObjSpaceToObjSpaceMatrix = Quaternion([.707107, 0, 0, -.707107]).inverted().to_matrix().to_4x4() * (sourceObj.matrix_world.inverted() * sourceBone.matrix_world).inverted() * bone.bone.GetMatrix()
			#sourceObjSpaceToObjSpaceMatrix = sourceObj.matrix_world.inverted() * bone.bone.GetMatrix_World(obj)
			#sourceBoneSpaceToBoneSpaceMatrix = sourceBone.matrix_world.inverted() * bone.bone.GetMatrix_World(obj)
			#transformationMatrix = sourceObj.matrix_world.inverted() * bone.bone.GetMatrix_Object(obj)
			transformationMatrix = sourceBone.parent.matrix_world.inverted() * bone.bone.GetMatrix_World(obj)

			# transform position channels
			if len([a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "rotation_quaternion" and a.array_index == 0]) >= 1:
				channelX = [a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "location" and a.array_index == 0][0]
				channelY = [a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "location" and a.array_index == 1][0]
				channelZ = [a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "location" and a.array_index == 2][0]
				for i, keyframe in enumerate(channelX.keyframe_points): # assumes that the channel-group's keyframe-points are all aligned on the same x-axis points
					'''pos = Vector((channelX.keyframe_points[i].co[1], channelY.keyframe_points[i].co[1], channelZ.keyframe_points[i].co[1]))
					pos = transformationMatrix * pos'''
					pos_world = sourceBone.parent.matrix_world * Vector((channelX.keyframe_points[i].co[1], channelY.keyframe_points[i].co[1], channelZ.keyframe_points[i].co[1]))
					#pos_delta = sourceBone.matrix_world.inverted() * pos_world # remember, 'pos for-pose-bone' is actually: the pos delta, from the 'rest pos' (of sourceBone.matrix_world)
				
					# for testing
					#pos_delta = Vector((0, 0, 0))

					#pos_delta_forPoseBone = pos_delta
					#pos_forPoseBone = bone.bone.GetMatrix_World(obj).inverted() * pos_delta
					#pos_forPoseBone = obj.matrix_world.inverted() * pos_delta
					#pos_delta_forPoseBone = bone.bone.GetMatrix_World(obj).inverted() * pos_delta
					#pos_delta_forPoseBone = obj.matrix_world.inverted() * pos_delta
					#pos_delta_forPoseBone = (obj.matrix_world.inverted() * pos_delta) - (obj.matrix_world.inverted() * Vector((0, 0, 0)))

					worldToForPoseBone = bone.bone.GetMatrix_World(obj).inverted()
					pos_forPoseBone = worldToForPoseBone * pos_world

					channelX.keyframe_points[i].SetValue(pos_forPoseBone.x, true)
					channelY.keyframe_points[i].SetValue(pos_forPoseBone.y, true)
					channelZ.keyframe_points[i].SetValue(pos_forPoseBone.z, true)

			# transform rotation channels
			if len([a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "rotation_quaternion" and a.array_index == 0]) >= 1:
				channelX = [a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "rotation_quaternion" and a.array_index == 1][0]
				channelY = [a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "rotation_quaternion" and a.array_index == 2][0]
				channelZ = [a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "rotation_quaternion" and a.array_index == 3][0]
				channelW = [a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "rotation_quaternion" and a.array_index == 0][0] # the array_index for w is 0
				for i, keyframe in enumerate(channelX.keyframe_points): # assumes that the channel-group's keyframe-points are all aligned on the same x-axis points
					'''rotation = Quaternion((channelW.keyframe_points[i].co[1], channelX.keyframe_points[i].co[1], channelY.keyframe_points[i].co[1], channelZ.keyframe_points[i].co[1]))
					rotation.rotate(transformationMatrix)'''
					#rotation_world = sourceBone.parent.matrix_world * Quaternion((channelW.keyframe_points[i].co[1], channelX.keyframe_points[i].co[1], channelY.keyframe_points[i].co[1], channelZ.keyframe_points[i].co[1]))
					rotation_world = Quaternion((channelW.keyframe_points[i].co[1], channelX.keyframe_points[i].co[1], channelY.keyframe_points[i].co[1], channelZ.keyframe_points[i].co[1]))
					rotation_world.rotate(sourceBone.parent.matrix_world)
					#rotation_delta = rotation_world
					#rotation_delta.rotate(sourceBone.matrix_world.inverted()) # remember, 'rotation for-pose-bone' is actually: the rotation delta, from the 'rest rotation' (of sourceBone.matrix_world)
					
					# for testing
					#rotation_delta = Quaternion((1, 0, 0, 0))
					#rotation_delta = Quaternion((.7, -.7, 0, 0))

					# rotation_local: Quaternion((0, .7, 0, -.7))
					# rotation_world: Quaternion((.7, .7, 0, 0))
					# rotation_worldToTarget: Quaternion((.5, -.5, .5, .5))
					# rotation_target: Quaternion((.7, 0, 0, .7))
					
					#rotation_delta_forPoseBone = rotation_delta
					#rotation_forPoseBone.rotate(bone.bone.GetMatrix_World(obj).inverted())
					#rotation_forPoseBone.rotate(obj.matrix_world.inverted())
					#rotation_delta_forPoseBone.rotate(bone.bone.GetMatrix_World(obj).inverted())
					#rotation_delta_forPoseBone.rotate(obj.matrix_world.inverted())
					#rotation_delta_forPoseBone.rotate(obj.matrix_world.inverted())
					#rotation_delta_forPoseBone.rotate(Matrix_MultipliedBy(obj.matrix_world.inverted(), Quaternion((1, 0, 0, 0))).inverted())
					#rotation_delta_forPoseBone.rotate(obj.matrix_world.inverted())
					#rotation_delta_forPoseBone.rotate(Matrix_MultipliedBy(obj.matrix_world.inverted(), Quaternion((1, 0, 0, 0))).inverted())

					rotation_forPoseBone = rotation_world.copy()
					worldToForPoseBone = (Quaternion([.707107, -.707107, 0, 0]).inverted().to_matrix().to_4x4() * bone.bone.GetMatrix_World(obj)).inverted().decompose()[1]
					#worldToForPoseBone.x *= -1
					#worldToForPoseBone.y *= -1
					rotation_forPoseBone.rotate(worldToForPoseBone)

					channelX.keyframe_points[i].SetValue(rotation_forPoseBone.x, true)
					channelY.keyframe_points[i].SetValue(rotation_forPoseBone.y, true)
					channelZ.keyframe_points[i].SetValue(rotation_forPoseBone.z, true)
					channelW.keyframe_points[i].SetValue(rotation_forPoseBone.w, true)

			# maybe make-so: scaling gets transformed

		return {"FINISHED"}

class transform_action_keyframes(bpy.types.Operator):
	bl_idname = "graph.transform_action_keyframes"
	bl_label = "Transform action keyframes"
	bl_description = "Transforms the action's keyframes, based on the transformation between from-object and to-object."
	bl_options = {"REGISTER", "UNDO"}
	bl_space_type = "GRAPH_EDITOR"
	bl_region_type = "UI"

	fromObjectName = bpy.props.StringProperty(name = "From object name")
	toObjectName = bpy.props.StringProperty(name = "To object name")

	@classmethod
	def poll(cls, context):
		return AreKeyframesLoaded(context)
	def execute(s, context):
		obj = Active()
		action = ActiveAction()
		fromObj = Obj(s.fromObjectName)
		toObj = Obj(s.fromObjectName)
		if fromObj == null or toObj == null:
			return {"FINISHED"}

		transformationMatrix = fromObj.matrix_world.inverted() * toObj.matrix_world

		curvesToModify_bones = []
		for curve in action.fcurves:
			# (if bone isn't in selected armature, we must have recently deleted it (but left keyframes for it); just ignore its curve)
			if curve.GetBoneName() in obj.pose.bones and curve.GetBoneName() not in curvesToModify_bones:
				curvesToModify_bones.append(curve.GetBoneName())
		for boneName in curvesToModify_bones:
			# transform position channels
			if len([a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "rotation_quaternion" and a.array_index == 0]) >= 1:
				channelX = [a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "location" and a.array_index == 0][0]
				channelY = [a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "location" and a.array_index == 1][0]
				channelZ = [a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "location" and a.array_index == 2][0]
				for i, keyframe in enumerate(channelX.keyframe_points): # assumes that the channel-group's keyframe-points are all aligned on the same x-axis points
					pos = Vector((channelX.keyframe_points[i].co[1], channelY.keyframe_points[i].co[1], channelZ.keyframe_points[i].co[1]))
					pos = transformationMatrix * pos
					channelX.keyframe_points[i].SetValue(pos.x, true)
					channelY.keyframe_points[i].SetValue(pos.y, true)
					channelZ.keyframe_points[i].SetValue(pos.z, true)

			# transform rotation channels
			if len([a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "rotation_quaternion" and a.array_index == 0]) >= 1:
				channelX = [a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "rotation_quaternion" and a.array_index == 1][0]
				channelY = [a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "rotation_quaternion" and a.array_index == 2][0]
				channelZ = [a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "rotation_quaternion" and a.array_index == 3][0]
				channelW = [a for a in action.fcurves if a.GetBoneName() == boneName and a.GetPropertyName() == "rotation_quaternion" and a.array_index == 0][0] # the array_index for w is 0
				for i, keyframe in enumerate(channelX.keyframe_points): # assumes that the channel-group's keyframe-points are all aligned on the same x-axis points
					rotation = Quaternion((channelW.keyframe_points[i].co[1], channelX.keyframe_points[i].co[1], channelY.keyframe_points[i].co[1], channelZ.keyframe_points[i].co[1]))
					rotation.rotate(transformationMatrix)
					channelX.keyframe_points[i].SetValue(rotation.x, true)
					channelY.keyframe_points[i].SetValue(rotation.y, true)
					channelZ.keyframe_points[i].SetValue(rotation.z, true)
					channelW.keyframe_points[i].SetValue(rotation.w, true)

			# maybe make-so: scaling gets transformed

		return {"FINISHED"}

# registration stuff
# ==========

bpy.utils.register_module("vtools")