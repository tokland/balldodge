import pygame
import numpy
import visual

import gamelib

class Triangle:
	def __init__(self, points, fsize=(1, 1), angle=0.0):
		if len(points) != 3:
			raise ValueError, "A triangle should have exactly 3 points"
		self.angle = angle
		self.vbasepoints = [visual.vector([(s*p) for (s, p) in zip(fsize, point)]) \
			for point in points]
		self.vpos = visual.vector((0, 0))
		self.update_points()
				
	def set_vpos(self, pos):
		self.vpos = pos
		self.update_points()
		
	def get_pos(self):
		return self.vpos.astuple()[:2]
				
	def set_angle(self, angle):
		self.angle = angle
		self.update_points()
		
	def update_points(self):
		self.vpoints = [(v.rotate(self.angle)+self.vpos) \
			for v in self.vbasepoints]
		self.points = [v.astuple()[:2] for v in self.vpoints]
		gp = lambda k: [p[k] for p in self.points]
		px, py = gp(0), gp(1)
		self.bounds = (min(px), min(py)), (max(px), max(py))
			
	def get_bounds(self):
		return self.bounds
		
	def get_points(self):
		return self.points
		
	def collides_with_point(self, point):
		if not gamelib.check_bounds((point, point), self.get_bounds()):
			return
		p0, p1, p2 = self.points
		orientation = self.get_orientation()
		for triangle in (Triangle((q0, q1, q2)) for (q0, q1, q2) \
				in ((p0, p1, point), (p1, p2, point), (p2, p0, point))):
			if triangle.get_orientation()*orientation < 0:
				return
		return (p0, p1, p2)

	def collides_with_points(self, points):
		for point in points:
			if self.collides_with_point(point):
				return point

	def get_orientation(self):
		p1, p2, p3 = self.vpoints
		a, b = (p2-p1), (p3-p1)
		return (a[0]*b[1]-a[1]*b[0])

	def get_segments(self):
		v1, v2, v3 = self.vpoints
		return [Segment(start=vpoint.astuple()[:2], vector=vector) \
			for vpoint, vector in [(v1, (v2-v1)), (v2, (v3-v2)), (v3, (v1-v3))]]

	def get_points_depth(self, depth):
		output = self.points[:]
		output.extend([v.astuple()[:2] for v in \
			self.get_center_vpoints(self.vpoints, depth)])
		return output
	
	def get_center_vpoints(self, vpoints, depth):
		p1, p2, p3 = vpoints
		p4 = (p1+p2+p3)/3
		output = [p4]
		if not depth:
			return output
		depth -= 1
		output.extend([p for vps in [(p1, p2, p4), (p1, p3, p4), (p2, p3, p4)] \
			for p in self.get_center_vpoints(vps, depth)])
		return output

#t = Triangle([(-5, 4), (-4, 5), (-3, 4)])
		
##############################################
class TrianglesFigure:
	def __init__(self, triangles, fsize=None):
		self.angle = 0.0
		self.points = None
		self.bounds = None
		self.triangles = [Triangle(vertices, fsize) for vertices in triangles]
		self.set_pos((0, 0))
		self.f = False

	def draw(self, surface, color=(0, 0, 255), width=0):
		rects = [pygame.draw.polygon(surface, color, \
			t.get_points(), width) for t in self.triangles]
		return rects
		
	def get_points(self):
		self.update_points()
		return self.points
							
	def get_bounds(self):
		return self.bounds

	def update_points(self):
		points = [p for t in self.triangles for p in t.get_points()]
		if not points:
			return
		px, py = [[p[k] for p in points] for k in range(2)]		
		self.points = points
		self.bounds = (min(px), min(py)), (max(px), max(py))
		
	def set_pos(self, pos):
		vpos = visual.vector(pos)
		for triangle in self.triangles:
			triangle.set_vpos(vpos)
		self.vpos = vpos
		self.update_points()
	
	def add_vpos(self, incpos):
		self.vpos += incpos
		self.set_pos(self.vpos)
		
	def get_pos(self):
		return self.vpos.astuple()[:2]
		
	def get_triangles(self):
		return self.triangles
		
	def set_angle(self, angle):
		self.angle = angle
		for t in self.triangles:
			t.set_angle(angle)
		self.update_points()

	def add_angle(self, increment):
		self.angle += increment
		for t in self.triangles:
			t.set_angle(self.angle)
		self.update_points()
		
	def get_angle(self):
		return self.angle
					
	def collides_with_figures(self, figures):
		bounds1 = self.get_bounds()
		for figure in figures:
			fbounds = figure.get_bounds()
			if not gamelib.check_bounds(bounds1, fbounds):
				continue
			for t1 in self.get_triangles():
				if not gamelib.check_bounds(bounds1, t1.get_bounds()):
					continue
				t1segs = t1.get_segments()
				for t2 in figure.get_triangles():
					for seg1 in t1segs:
						for seg2 in t2.get_segments():
							if seg1.collides_with_segment(seg2):
								return (t1, t2)

	def collides_with_point(self, pos):
		if not gamelib.check_bounds(self.get_bounds(), (pos, pos)):
			return
		for triangle in self.triangles:
			if not gamelib.check_bounds(triangle.get_bounds(), (pos, pos)):
				continue
			if triangle.collides_with_point(pos):
				return triangle

class Segment:
	def __init__(self, start, end=None, vector=None):
		self.p1 = start
		if end is not None:
			self.p2 = end
			self.vector = visual.vector(end)-visual.vector(start)
		elif vector is not None:
			self.vector = vector
			self.p2 = (visual.vector(start)+vector).astuple()[:2]
		self.update_bounds()
	
	def __repr__(self):
		return "<Segment: %s -> %s>"%(self.p1, self.p2)
		
	def get_bounds(self):
		return self.bounds
	
	def update_bounds(self):
		(x1, y1), (x2, y2) = self.p1, self.p2
		self.bounds = [(min(a), max(a)) for a in ((x1, x2), (y1, y2))]
		
	def get_points(self):
		return (self.p1, self.p2)
		
	def get_vector(self):
		return self.vector

	def isbetween(self, n, a, b, epsilon=0.000001):
		if a > b:
			a, b = b, a
		return (n-a)>-epsilon and (b-n)>-epsilon

	def collides_with_segment(self, segment):
		p0x, p0y = self.p1
		t0x, t0y = segment.p1
		vx, vy = self.vector.astuple()[:2]
		wx, wy = segment.vector.astuple()[:2]
		m = numpy.matrix([(vx, -wx), (vy, -wy)])
		r = numpy.matrix([[t0x-p0x], [t0y-p0y]])
		try: 
			k1 = float((numpy.linalg.inv(m)*r)[0])
		except numpy.linalg.linalg.LinAlgError: 
			return
		xc, yc = (p0x+k1*vx, p0y+k1*vy)
		(x1, y1), (x2, y2) = self.p1, self.p2
		(lx1, ly1), (lx2, ly2) = segment.p1, segment.p2
		ib = self.isbetween
		if ib(xc, x1, x2) and ib(xc, lx1, lx2) \
				and ib(yc, y1, y2) and ib(yc, ly1, ly2):
			return xc, yc
