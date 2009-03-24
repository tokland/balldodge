import pygame
import visual
import math
import gamelib

def process_balls_collision((m1, v1), (m2, v2)):
    a = (m1-m2)/(m1+m2)
    b = 2*m2/(m1+m2)
    new_v1 = a*v1+b*v2
    new_v2 = (m1/m2)*b*v1-a*v2
    return new_v1, new_v2

##############################################
class BallBase:
    def __init__(self, radius, color, circle_npoints):
        self.pos = (0, 0)
        self.vpos = visual.vector(self.pos)
        self.angle = 0.0
        self.set_speed((0, 0))
        self.circle_npoints = circle_npoints
        self.set_radius(radius)
        self.set_color(color)
        self.update_base_circle_points()
        
    def get_radius(self):
        return self.radius
        
    def update_base_circle_points(self):
        pi2 = 2*math.pi
        sin, cos = math.sin, math.cos
        self.base_circle_points = [(self.radius*cos(angle), \
            self.radius*sin(angle)) for angle in \
            [(index*pi2)/self.circle_npoints for \
            index in xrange(self.circle_npoints)]]

    def get_bounds(self):
        (x, y), r = self.pos, self.radius
        return (x-r, y-r), (x+r, y+r)
        
    def set_pos(self, pos):
        self.pos = pos
        self.vpos = visual.vector(pos)

    def set_vpos(self, vpos):
        self.vpos = vpos
        self.pos = vpos.astuple()[:2]

    def get_pos(self):
        return self.pos

    def update_circle_points(self):
        self.circle_points = [[(a+b) for (a, b) in zip(self.pos, point)] \
            for point in self.base_circle_points]

    def set_color(self, color):
        self.color = color
        
    def get_circle_points(self):
        self.update_circle_points()
        return self.circle_points
        
    def set_speed(self, speed):
        self.speed = speed
        self.vspeed = visual.vector(*speed)

    def set_vspeed(self, vspeed):
        self.vspeed = visual.vector(*vspeed)
        self.speed = vspeed.astuple()[:2]

    def set_radius(self, radius):
        self.radius = float(radius)
        self.update_base_circle_points()
        self.update_circle_points()

    def collides_with_figures(self, figures):
        bounds1 = self.get_bounds()
        triangles = {}
        for figure in figures:
            if not gamelib.check_bounds(bounds1, figure.get_bounds()):
                continue
            circle_points = self.get_circle_points()
            for point in circle_points:
                for triangle in figure.get_triangles():
                    if triangle.collides_with_point(point):
                        if not triangles.has_key(triangle):
                            triangles[triangle] = []
                        triangles[triangle].append(point)
        return [(triangle, triangles[triangle]) for triangle in triangles]

    def update_collision_with_ball(self, ball, electron_mode=False):
        point = self.collides_with_ball(ball)
        if not electron_mode:
            if not point or (self.vspeed.dot(point-self.vpos) <= 0 and \
                    ball.vspeed.dot(point-ball.vpos) <= 0):
                return
        elif not point or (self.vspeed.dot(point-self.vpos) > 0 or \
            ball.vspeed.dot(point-ball.vpos) > 0):
            return
        vdiff = ball.vpos - self.vpos
        vdiffo = vdiff.rotate(visual.pi/2.0)
        v1c, v2c = [b.vspeed.proj(vdiff) for b in (self, ball)]
        v1o, v2o = [b.vspeed.proj(vdiffo) for b in (self, ball)]
        m1, m2 = self.radius**2, ball.radius**2
        k1, k2 = [cmp(vdiff.dot(x), 0.0) for x in (v1c, v2c)]
        nv1c, nv2c = process_balls_collision((m1, k1*abs(v1c)), \
            (m2, k2*abs(v2c)))
        self.vspeed = v1o + k1*v1c.norm()*nv1c
        ball.vspeed = v2o + k2*v2c.norm()*nv2c
        return point
        
    def collides_with_ball(self, ball):
        vdiff = ball.vpos - self.vpos
        if abs(vdiff) < self.radius+ball.radius:
            nvdiff = vdiff.norm()
            p1 = self.vpos+self.radius*nvdiff
            p2 = ball.vpos-ball.radius*nvdiff
            return (p1+p2)/2

    def draw(self, surface, color=None, width=0):
        if color is None:
            color = self.color
        return [pygame.draw.circle(surface, color, \
            [int(x) for x in self.pos], int(self.radius), width)]

class Ball(BallBase):
    def __init__(self, radius, color, solid, electron, circle_npoints=16):
        BallBase.__init__(self, radius, color, circle_npoints)
        self.solid = solid
        self.electron = electron
        self.debug_points = []

    def update_collision_with_ball(self, ball):
        if self.solid and ball.solid:
            electron = self.electron or ball.electron
            return BallBase.update_collision_with_ball(self, ball, \
                electron_mode=electron)

    def draw(self, surface):
        rects = []
        rects.extend(BallBase.draw(self, surface))
        if self.solid:
            color = (255, 255, 255)
            rects.extend(BallBase.draw(self, surface, color=color, width=2))
        rects.extend([pygame.draw.circle(surface, (255, 100, 100), \
            [int(x) for x in point], 2) for point in self.debug_points])
        return rects		

    def update(self, player, board, tick, check_pressed_key):
        if check_pressed_key("space"):
            tick = 0.0
        self.set_vpos(self.vpos+tick*self.vspeed)		
        self.debug_triangles = []
        collision =  self.collides_with_figures(board.get_figures()+[player])
        player_collide = False
        if collision:
            ptriangles = player.get_triangles()
            for triangle, points in collision:
                if triangle in ptriangles:
                    player_collide = True
                    break
            triangle, points = collision[0]
            vector = reduce(visual.vector.__add__, \
                [(visual.vector(point)-self.vpos) for point in points])
            if vector.dot(self.vspeed) >= 0:
                orto = vector.rotate(visual.pi/2)
                bfactor = board.get_rebound()
                nvspeed = self.vspeed.proj(orto)-self.vspeed.proj(vector)
                self.set_vspeed(bfactor*(nvspeed))
        return player_collide