SetFactory("OpenCASCADE");
Cylinder(1)={0,0,0,0,0,1.6,6.0};
Cylinder(2)={0,0,-.1,0,0,1.8,2.15};
BooleanDifference{Volume{1};Delete;}{Volume{2};Delete;}
Mesh.MeshSizeMin=0.45;Mesh.MeshSizeMax=0.45;
Mesh.ElementOrder=2;Mesh.SecondOrderLinear=0;
Mesh.MshFileVersion=2.2;Mesh.Binary=0;
