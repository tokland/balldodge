import pygame
import objects

class Board:
    def __init__(self, color, size, figures, imagefile, fsize=(1,1), rebound=1.0, partition=(10,10)):
        self.color = color
        self.rebound = rebound
        self.partition = partition
        self.board_size = [int((a*b)) for (a, b) in zip(size, fsize)]
        self.figures = [objects.TrianglesFigure(figure, fsize) for figure in figures]
        self.init_bricks()
        self.load_image(imagefile)
        
    def load_image(self, imagefile):
        if imagefile:
            s = pygame.image.load(imagefile).convert()
            self.background = pygame.transform.scale(s, self.board_size)
        else: self.background = None
        
    def init_bricks(self):
        px, py = self.partition
        nx, ny = [int(a/b) for (a, b) in zip(self.board_size, self.partition)]
        self.bricks_size = nx, ny
        self.bricks = [[0]*py for x in range(px)]
        self.nbricks = px*py
        self.bricks_done = []
        fi = lambda a, s: (a+0.01, a+s/2.0, a+s-0.01)
        def _check_brick():
            for x in fi(bx*nx, nx):
                for y in fi(by*ny, ny):
                    for figure in self.figures:
                        if figure.collides_with_point((x, y)):
                            break
                    else: 
                        return False
            return True
        for bx in range(px):
            for by in range(py):
                if _check_brick():
                    self.bricks[bx][by] = 1
                    self.bricks_done.append((bx, by))
        self.bricks_drawn = self.bricks_done[:]	
                                
    def set_brick(self, pos, value=1):
        x, y = pos
        px, py = self.partition
        nx, ny = self.bricks_size
        bx, by = int(x/nx), int(y/ny)
        if not self.bricks[bx][by]:
            self.bricks[bx][by] = value
            self.bricks_done.append((bx, by))
            return True
                
    def get_rebound(self):
        return self.rebound
        
    def get_figures(self):
        return self.figures
        
    def draw_background(self, surface):
        rects = []
        for figure in self.figures:
            rects.extend(figure.draw(surface, self.color, width=0))			
        return rects
        
    def get_nbricks_unset(self):
        return (self.nbricks - len(self.bricks_done))
        
    def draw_bricks(self, surface, redraw=False):
        bx, by = self.bricks_size
        px, py = self.partition
        rects = []
        for x in range(px):
            for y in range(py):
                if not self.bricks[x][y]:
                    continue
                if not redraw and (x, y) in self.bricks_drawn:
                    continue
                a, b = x*bx, y*by
                if self.background:
                    r = [(a, b), (a+bx, b), (a+bx, b+by), (a, b+by)]
                    rect = surface.blit(self.background, (a, b), (a, b, bx, by))
                else: 
                    w, wo = 1, 2
                    r = [(a+w, b+w), (a+bx-w, b+w), (a+bx-w, b+by-w), (a+w, b+by-w)]
                    rect = pygame.draw.polygon(surface, (30, 15, 15), r, wo)
                self.bricks_drawn.append((x, y))
                rects.append(rect)
        return rects