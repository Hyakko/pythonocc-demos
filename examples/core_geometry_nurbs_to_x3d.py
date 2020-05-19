##Copyright 2020 Thomas Paviot (tpaviot@gmail.com)
##
##This file is part of pythonOCC.
##
##pythonOCC is free software: you can redistribute it and/or modify
##it under the terms of the GNU Lesser General Public License as published by
##the Free Software Foundation, either version 3 of the License, or
##(at your option) any later version.
##
##pythonOCC is distributed in the hope that it will be useful,
##but WITHOUT ANY WARRANTY; without even the implied warranty of
##MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##GNU Lesser General Public License for more details.
##
##You should have received a copy of the GNU Lesser General Public License
##along with pythonOCC.  If not, see <http://www.gnu.org/licenses/>.

from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeTorus
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_NurbsConvert
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface

from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.GeomAbs import GeomAbs_BSplineSurface

    
# then export to x3d
X3D_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE X3D PUBLIC "ISO//Web3D//DTD X3D 4.0//EN" "https://www.web3d.org/specifications/x3d-4.0.dtd">
<X3D profile='Immersive' version='4.0' xmlns:xsd='http://www.w3.org/2001/XMLSchema-instance' xsd:noNamespaceSchemaLocation='http://www.web3d.org/specifications/x3d-4.0.xsd'>
<head>
    <meta name='generator' content='pythonocc-7.4.1-dev X3D exporter (www.pythonocc.org)'/>
    <meta name='creator' content='pythonocc-7.4.1-dev generator'/>
    <meta name='identifier' content='http://www.pythonocc.org'/>
    <meta name='description' content='pythonocc-7.4.1-dev x3dom based shape rendering'/>
</head>
    <Scene>
    %s
    </Scene>
</X3D>
"""

base_shape = BRepPrimAPI_MakeTorus(30, 10).Shape()

# conversion to a nurbs representation
nurbs_converter = BRepBuilderAPI_NurbsConvert(base_shape, True)
#nurbs_converter.Perform()
converted_shape = nurbs_converter.Shape()

# now, all edges should be BSpline curves and surfaces BSpline surfaces
# see https://www.opencascade.com/doc/occt-7.4.0/refman/html/class_b_rep_builder_a_p_i___nurbs_convert.html#details

expl = TopologyExplorer(converted_shape)

nurbs_node_str = ""

face_idx = 1

for face in expl.faces():
    surf = BRepAdaptor_Surface(face, True)
    surf_type = surf.GetType()
    # check each of the is a BSpline surface
    # it should be, since we used the nurbs converter before
    if not surf_type == GeomAbs_BSplineSurface:
        raise AssertionError("the face was not converted to a GeomAbs_BSplineSurface")
    # get the nurbs
    bsrf = surf.BSpline()
    print(bsrf.IsUPeriodic())
    print(bsrf.IsVPeriodic())
    bsrf.SetUNotPeriodic()
    bsrf.SetVNotPeriodic()

    
    # fill in the x3d template with nurbs information
    nurbs_node_str = "<Shape>"
    nurbs_node_str += "<Appearance><Material></Material></Appearance>\n"
    nurbs_node_str += "<NurbsPatchSurface DEF='nurbs_%i' solid='false' " % face_idx
    nurbs_node_str += 'uDimension="%i" uOrder="%i" ' % (bsrf.NbUPoles(), bsrf.UDegree()+1)
    nurbs_node_str += 'vDimension="%i" vOrder="%i" ' % (bsrf.NbVPoles(), bsrf.VDegree()+1)
    nurbs_node_str += "uKnot='"
    uknots = bsrf.UKnots()
    for i in range(bsrf.NbUKnots()):
# AP: repeat knots as necessary
        m=bsrf.UMultiplicity(i+1)
        nurbs_node_str += ("%g " % uknots.Value(i + 1)) * m
    nurbs_node_str +="' "

    nurbs_node_str += "vKnot='"
    vknots = bsrf.VKnots()
    for i in range(bsrf.NbVKnots()):
        m=bsrf.VMultiplicity(i+1)
        nurbs_node_str += ("%g " % vknots.Value(i + 1)) * m
    nurbs_node_str +="' "

    weights = bsrf.Weights()
    # weights can be None
    if weights is not None:
        nurbs_node_str += "weight='"
# weight is per pole
# x3d has u as fast dim. in the grid
        for i in range(bsrf.NbVPoles()):
            for j in range(bsrf.NbUPoles()):
                nurbs_node_str +="%g " % bsrf.Weight(j+1, i+1) #weights.Value(j + 1, i + 1)
        nurbs_node_str +="' "

    # weights can be None
#     if weights is None:

    nurbs_node_str += "containerField='geometry'>\n"
    # the control points
    nurbs_node_str += "<Coordinate containerField='controlPoint' point='"
    # control points (aka poles), as a 2d array
    poles = bsrf.Poles()
    # weights can be None
    if poles is not None:
        for i in range(bsrf.NbVPoles()):
            for j in range(bsrf.NbUPoles()):
                p = bsrf.Pole(j + 1, i + 1) #poles.Value(j + 1, i + 1)
                nurbs_node_str += "%g %g %g " % (p.X(), p.Y(), p.Z())
        nurbs_node_str +="'/>"

    nurbs_node_str += "</NurbsPatchSurface></Shape>\n"

    face_idx += 1

# write x3d file
fp = open("nurbs.x3d", "w")
fp.write(X3D_TEMPLATE % nurbs_node_str)
fp.close()
