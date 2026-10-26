SetFactory("OpenCASCADE");
Cylinder(1)={0,0,0,0,0,1.3,5.65};
Cylinder(2)={0,0,-.1,0,0,1.5,2.24};
BooleanDifference{Volume{1};Delete;}{Volume{2};Delete;}
Mesh.MeshSizeMin=0.4;Mesh.MeshSizeMax=0.4;
Mesh.ElementOrder=2;Mesh.SecondOrderLinear=0;
Mesh.MshFileVersion=2.2;Mesh.Binary=0;
