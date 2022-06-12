bl_info = {
    "name": "Material-Asset-Creator",
    "description": "Scans through selected directory and creates material assets with textures",
    "author": "BoomRaccoon",
    "version": (0, 2, 0),
    "blender": (3, 0, 0),
    "warning": "",
    "doc_url": "https://github.com/BoomRaccoon/Blender_MaterialAssetCreator",
    "category": "Material",
}


import bpy
import os
import re
from pathlib import Path, PurePath
import inspect

# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator



# RegEx Patterns
searchPatternDiffuse = re.compile(r'(diffuse|diff|basecolor|_base)|_color\.', re.I)
searchPatternMetal = re.compile(r'(_metal\.)', re.I)
searchPatternRoughness = re.compile(r'(_roughness\.|_rough.)', re.I)
searchPatternNormal = re.compile(r'(normal)', re.I)
searchPatternSpecular = re.compile(r'(specular|spec)', re.I)
searchPatternMask = re.compile(r'(mask)', re.I)
searchPatternDisplacement = re.compile(r'(height|displace|bump)', re.I)


def lookForTextures(path, materialPrefix, newObj, specular, bumpStrength, bumpDistance):
    if not hasDir(path):            
        mat = bpy.data.materials.new(materialPrefix)
        mat.use_nodes = True
        matNodes = mat.node_tree.nodes
        matLinks = mat.node_tree.links
        shader = mat.node_tree.nodes["Principled BSDF"]
        shader.inputs['Specular'] = specular
        
        for entry in os.scandir(path):
            if searchPatternDiffuse.search(entry.name):
                tex = matNodes.new(type="ShaderNodeTexImage")
                tex.hide = True
                tex.location = (-300, 185)
                tex.image = bpy.data.images.load(entry.path)
                matLinks.new(shader.inputs['Base Color'], tex.outputs['Color'])
            elif searchPatternMetal.search(entry.name):
                tex = matNodes.new(type="ShaderNodeTexImage")
                tex.hide = True
                tex.location = (-300, 55)
                tex.image = bpy.data.images.load(entry.path)
                matLinks.new(shader.inputs['Metallic'], tex.outputs['Color'])
            elif searchPatternSpecular.search(entry.name):
                tex = matNodes.new(type="ShaderNodeTexImage")
                tex.hide = True
                tex.location = (-300, 25)
                tex.image = bpy.data.images.load(entry.path)
                matLinks.new(shader.inputs['Specular'], tex.outputs['Color'])
            elif searchPatternRoughness.search(entry.name):
                tex = matNodes.new(type="ShaderNodeTexImage")
                tex.hide = True
                tex.location = (-300, -10)
                tex.image = bpy.data.images.load(entry.path)
                matLinks.new(shader.inputs['Roughness'], tex.outputs['Color'])
            elif searchPatternMask.search(entry.name):
                tex = matNodes.new(type="ShaderNodeTexImage")
                tex.hide = True
                tex.location = (-300, -260)
                tex.image = bpy.data.images.load(entry.path)
                matLinks.new(shader.inputs['Alpha'], tex.outputs['Color'])
            elif searchPatternDisplacement.search(entry.name):
                tex = matNodes.new(type="ShaderNodeTexImage")
                tex.hide = True
                tex.location = (-500, -260)
                tex.image = bpy.data.images.load(entry.path)
                tex.image.colorspace_settings.name = 'Non-Color'
                nodeBump = matNodes.new(type="ShaderNodeBump")
                nodeBump.hide = True
                nodeBump.location = (-200, -290)
                nodeBump.inputs['Strength'].default_value = bumpStrength
                nodeBump.inputs['Distance'].default_value = bumpDistance
                matLinks.new(nodeBump.inputs['Height'], tex.outputs['Color'])
            elif searchPatternNormal.search(entry.name):
                bBump = False
                tex = matNodes.new(type="ShaderNodeTexImage")
                tex.hide = True
                tex.location = (-500, -300)
                tex.image = bpy.data.images.load(entry.path)
                tex.image.colorspace_settings.name = 'Non-Color'
                for node in mat.node_tree.nodes:
                    if node.type == 'BUMP':
                        bBump = True
                        nodeBump = node
                nMap = matNodes.new(type="ShaderNodeNormalMap")
                nMap.hide = True
                nMap.location = (-500, -340)
                matLinks.new(nMap.inputs['Color'], tex.outputs['Color'])
                if bBump:
                    matLinks.new(nodeBump.inputs['Normal'], nMap.outputs['Normal'])
                    matLinks.new(nodeBump.outputs['Normal'], shader.inputs['Normal'])
                else:
                    matLinks.new(shader.inputs['Normal'], nMap.outputs['Normal'])

        # Assign it to object
        texCoord = matNodes.new(type="ShaderNodeTexCoord")
        texCoord.location = (-900,0)
        mapping = matNodes.new(type="ShaderNodeMapping")
        mapping.location = (-700,0)
        matLinks.new(texCoord.outputs['UV'], mapping.inputs['Vector'])
        for texNode in mat.node_tree.nodes:
            if texNode.type == "TEX_IMAGE":
                matLinks.new(mapping.outputs['Vector'], texNode.inputs['Vector'])
        newObj.data.materials.append(mat)
        mat.asset_mark()
        mat.asset_generate_preview()
    else:
        for entry in os.scandir(path):        
            if entry.is_dir():
                lookForTextures(entry.path, materialPrefix, newObj)

        

def hasDir(path):
    bhasDir = False
    for entry in os.scandir(path):
        if entry.is_dir():
            bhasDir = True
    return bhasDir
        


class AddMaterialsToLibrary(Operator, ImportHelper):
    """Select directory to iterate over and use diffuse-, metal-, roughness- and normal-textures to create materials"""
    bl_idname = "material.create_assets"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Create material assets"

    directory: bpy.props.StringProperty(
        name="Outdir Path",
        description="Select",
        subtype="DIR_PATH",
    )
    
    materialPrefix: bpy.props.StringProperty(
        name="Material Prefix",
        description="Specify how what the prefix should be for the material.",
        default="Mat",
    )

    specular: bpy.props.FloatProperty(
        name="Specular",
        description="Amount of dielectric specular reflection. Specifies facing (along normal) reflectivity in the most common 0 - 8% range.",
        default= 0.0,
    )

    bumpStrength: bpy.props.FloatProperty(
        name="Bump strength",
        description="Makes darker shadows. High values will make it ugly",
        default= .25,
    )

    bumpDistance: bpy.props.FloatProperty(
        name="Bump distance",
        description=" High values will stop making changes (but will make it ugly at some point",
        default= .35,
    )

    filter_folder: bpy.props.BoolProperty(default=True, options={"HIDDEN"})
    filepath: bpy.props.StringProperty(default="F:\Art\Textures\Collection")

    

    def execute(self, context):
        try:
            newObj = bpy.data.objects['Cube']
        except:
            bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            newObj = bpy.context.active_object

        lookForTextures(self.directory, self.materialPrefix, newObj, self.specular, self.bumpDistance, self.bumpStrength)

        
        return {"FINISHED"}

def register():
    bpy.utils.register_class(AddMaterialsToLibrary)

def unregister():
    bpy.utils.unregister_class(AddMaterialsToLibrary)
            


