from __future__ import annotations

def rectangular_prism_triangles(x=2.0, y=4.0, z=1.0):
    vertices = [
        (-x/2,-y/2,-z/2), (x/2,-y/2,-z/2), (x/2,y/2,-z/2), (-x/2,y/2,-z/2),
        (-x/2,-y/2,z/2), (x/2,-y/2,z/2), (x/2,y/2,z/2), (-x/2,y/2,z/2),
    ]
    faces = [
        (0,2,1),(0,3,2), (4,5,6),(4,6,7),
        (0,1,5),(0,5,4), (3,7,6),(3,6,2),
        (1,2,6),(1,6,5), (0,4,7),(0,7,3),
    ]
    return [tuple(vertices[index] for index in face) for face in faces]

def wedge_triangles():
    vertices = [
        (-2,-1,0),(2,-1,0),(2,1,0),(-2,1,0),
        (-1.5,-0.8,1),(1.5,-0.8,1),(0,0.8,2),
    ]
    faces = [
        (0,2,1),(0,3,2), (0,1,5),(0,5,4),
        (1,2,6),(1,6,5), (2,3,6),(3,4,6),
        (3,0,4),(4,5,6),
    ]
    return [tuple(vertices[index] for index in face) for face in faces]
