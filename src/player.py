import pygame
import visual

import gamelib
import objects

class Player(objects.TrianglesFigure):
    def __init__(self, color, triangles, fsize=(1, 1), bricks_triangles_depth=1):
        objects.TrianglesFigure.__init__(self, triangles, fsize)
        self.color = color
        self.speed = 0
        self.rspeed = 0
        self.collide = False
        self.debug_triangles = []
        self.bricks_triangles_depth = bricks_triangles_depth
        self.controls = gamelib.Struct(up="up", down="down", right="right", \
            left="left", rotate_clock="x", rotate_counterclock="z")

    def set_controls(self, controls):
        self.controls = controls
        
    def draw(self, surface, width=0):
        rects = []
        rects.extend(objects.TrianglesFigure.draw(self, surface, self.color, width))
        rects.extend([pygame.draw.polygon(surface, (255, 0, 0), \
            t.get_points(), 0) for t in self.debug_triangles])
        return rects

    def update(self, board, balls, tick, check_pressed_key):
        c = self.controls
        self.debug_triangles = []
        
        oldpos = self.get_pos()
        moved = False
        for key, incpos in [(c.up, (0, -1)), (c.down, (0, 1)), \
                (c.right, (1, 0)), (c.left, (-1, 0))]:
            if check_pressed_key(key):
                self.add_vpos(visual.vector(incpos)*self.speed*tick)				
                if self.collides_with_figures(board.get_figures()):
                    self.set_pos(oldpos)
                else: moved = True
        
        oldangle = self.get_angle()
        for key, angle in [(c.rotate_counterclock, -1), (c.rotate_clock, 1)]:
            if check_pressed_key(key):
                self.add_angle(self.rspeed*tick*angle)
                if self.collides_with_figures(board.get_figures()):
                    self.set_angle(oldangle)
                else: moved = True

        nset = 0
        if moved:
            for triangle in self.get_triangles():
                for point in triangle.get_points_depth(self.bricks_triangles_depth):
                    if board.set_brick(point):
                        nset += 1
        return nset
            
    def set_speed(self, speed, rspeed):
        self.speed = speed
        self.rspeed = rspeed
