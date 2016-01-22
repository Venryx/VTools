# VTools
Set of Blender tools and operators/functions to speed up various operations/processes.

Here are some of them:
----------

##### Select keyframes in range

##### Copy keyframes to new action
Copies the selected keyframes to a new action.

##### Retarget action
Transforms the action's keyframes to be based-on/relative-to the active-object's armature's rest-pose, rather than the specified source-object's armature's rest-pose.

##### Move keyframes to
Move keyframe-segment, such that its first-frame becomes the given frame.

##### Copy keyframes to new actions

##### Focus on selected vertexes

##### Set position - local

##### Reset scale while preserving world space mesh

##### Separate islands into different objects

##### Create armature from object heirarchy

##### Convert action curves to datapath approach
Converts the active-action's curves from the [bone-name = group-name, component = data-path] approach, to the [bone-name = data-path-part, component = data-path-part] approach

##### Convert action rotation curves to quaternion type
Converts the active-action's rotation curves from the 3-prop euler type, to the 4-prop quaternion type.

##### Replace action curve bones
For each curve linked with old-bone-name, relink to new-bone-name.

##### Create merged action from actions

##### Retarget retarget action from object heirarchy to armature
Transforms the action's keyframes to be based-on/relative-to the active-object's armature's rest-pose, rather than the specified source-object's rest-pose.

##### Transform action keyframes
Transforms the action's keyframes, based on the transformation between from-object and to-object.