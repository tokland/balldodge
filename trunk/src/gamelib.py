import pygame
import inspect
import time
import imp
import os

consts = pygame.constants

#############################################
def dict2struct(data):
    if not isinstance(data, dict):
        return data
    sdata = Struct(**data)
    for key, value in data.iteritems():
        setattr(sdata, key, dict2struct(value))
    return sdata

#############################################
def load_configuration(filename):
    name = os.path.basename(filename)
    module = imp.load_source(name, filename)
    output = Struct()
    for var, data in inspect.getmembers(module):
        if var.find("__") != 0:
            setattr(output, var, dict2struct(data))
    return output
    
#############################################
def get_keys_names():
    keys_name = {}
    for key, value in inspect.getmembers(pygame.constants):
        if not key.startswith("K_"):
            continue
        keys_name[pygame.key.name(value)] = value
    return keys_name

##############################################
class BaseGame:
    _font_color = (255, 0, 0)
    _fps_position = (20, 40)
    
    def __init__(self, flags=0, screen_size=(640, 480), show_mouse=True, \
            show_fps=False, fontsize=24, images_cache_size=None, 
            loop_wait=0.0, max_tick=1.0):
        self.screen_size = screen_size
        self.show_fps = show_fps
        self.loop_wait = loop_wait
        self.max_tick = max_tick
        self.images = {}
        self.images_cache_size = images_cache_size
        pygame.mixer.pre_init(44100)
        pygame.init()
        pygame.mouse.set_visible(show_mouse)
        self.font = pygame.font.SysFont("", fontsize)
        self.display = pygame.display.set_mode(self.screen_size, flags)
        if show_fps:
            self.init_fps(update_time=0.5)
        self.last_dirty = []
        self.last_time = None
        self.keys_name = get_keys_names()
        self.background = None
        
    def get_screen_size(self):
        return self.screen_size
        
    def enable_background(self):
        self.background = pygame.Surface(self.display.get_size())
        return self.background

    def disable_background(self):
        self.background = None

    def get_display(self):
        return self.display

    def get_events(self):
        self.get_keys()
        events = []
        for event in get_events():
            if event.type == consts.QUIT:
                return
            events.append(event)
        return events

    def get_keys(self):
        self.keys = get_keys()

    def check_key(self, event, name):
        return event.key == self.keys_name[name]

    def check_keys(self, event, names):
        for name in names:
            if self.check_key(event, name):
                return True

    def check_pressed_key(self, name):
        index = self.keys_name[name]
        return self.keys[index]
    
    def check_pressed_keys(self, names):
        for name in names:
            if self.check_pressed_key(name):
                return True

    def draw_fps(self, dirty):
        if not self.show_fps:
            return
        self.update_fps()
        s = self.font.render("fps: %0.0f"%self.fps.last_fps, 1,self._font_color)
        rect = self.display.blit(s, self._fps_position)
        if dirty is not None:
            dirty.append(rect)

    def draw_screen(self, dirty=None, draw_update_rects=None):
        self.draw_fps(dirty)
        if dirty is not None:
            if draw_update_rects:
                for rect in dirty:
                    pygame.draw.rect(self.display, draw_update_rects, rect, 1)
            pygame.display.update(self.last_dirty+dirty)
            self.last_dirty = dirty
        else: 
            pygame.display.flip()
        if self.loop_wait:
            time.sleep(self.loop_wait)
        pygame.event.pump()
            
    def init_fps(self, update_time=1.0):
        self.fps = Struct(itime=time.time(), frames=0, last_fps=0, \
            update_time=update_time)

    def update_fps(self):
        self.fps.frames += 1
        now = time.time()
        if now - self.fps.itime > self.fps.update_time:
            fps = self.fps.frames / (now-self.fps.itime)
            self.fps.last_fps = fps
            self.fps.itime = now
            self.fps.frames = 0

    def init_timer(self):
        self.last_time = time.time()

    def get_tick(self):
        now = time.time()
        if self.last_time is None:
            self.last_time = now
        tick = now - self.last_time
        if tick > self.max_tick:
            tick = self.max_tick
        self.last_time = now
        return tick
        
    def draw_background(self, redraw=False):
        if not self.background:
            return
        if redraw:
            self.display.blit(self.background, (0, 0))
            return
        for rect in self.last_dirty:
            self.display.blit(self.background, rect, rect)
        
    def load_image(self, path, alpha=False, from_cache=True, size=None):
        if from_cache and path in self.images:
            return self.images[path]
        self.limit_images_size()
        image = pygame.image.load(path)
        if alpha: 
            image = image.convert_alpha()
        else: image = image.convert()
        if size is not None:
            image = pygame.transform.scale(image, size)
        self.images[path] = image
        return image

    def adjust_size(self, values, ttype=float, reference=100.0):
        f = lambda x, y: ttype(float(x)*y/reference)
        if not isinstance(values, (tuple, list)):
            return f(values, self.screen_size[0])
        return [f(x, y) for (x, y) in zip(values, \
            (len(values)/2)*self.screen_size)]


    ##############################################
    def limit_images_size(self):
        if not self.images_cache_size:
            return
        total_size = 0
        for path, image in self.images.items():
            w, h = image.get_size()
            total_size += (w*h)
            if total_size > self.images_cache_size:
                del self.images[path]

##############################################
class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __repr__(self):
        args = ['%s=%s' % (k, repr(v)) for (k,v) in vars(self).items()]
        return 'Struct(%s)' % (', '.join(args))

    def __getitem__(self, name):
        return self.__dict__[name]

##############################################
##############################################

def load_font(filename, size):
    return pygame.font.Font(filename, int(size))

def get_events():
    return pygame.event.get()

def get_keys():
    return pygame.key.get_pressed()

def is_mixer_init():
    return bool(pygame.mixer.get_init())
    
def load_sound(path):
    return pygame.mixer.Sound(path)
    
def play_sound(sound):
    sound.play()

def load_music(path):
    pygame.mixer.music.load(path)

def play_music(loop=True, startpos=0.0, rewind=False):
    if rewind:
        pygame.mixer.music.rewind()
    pygame.mixer.music.play(loop, startpos)

def pause_music():
    pygame.mixer.music.pause()

def unpause_music():
    pygame.mixer.music.unpause()

def stop_music():
    pygame.mixer.music.stop()

def multiply_color_surface(surface, factor):
    rect = surface.get_rect()
    dest = surface.copy()
    for x in range(rect.width):
        for y in range(rect.height):
            color = surface.get_at((x, y))
            if color[3] == 0: 
                continue
            color = pygame.color.multiply(color, 255*factor)
            dest.set_at((x,y), color)
    return dest

##############################################
def load_psyco():
    try:
        import psyco
        psyco.full()
    except ImportError:
        return False
    return True

def check_bounds(bounds1, bounds2):
    if not bounds1 or not bounds2:
        return False
    (xmin, ymin), (xmax, ymax) = bounds1
    (bxmin, bymin), (bxmax, bymax) = bounds2
    return (bxmin < xmax and bxmax > xmin and \
            bymin < ymax and bymax > ymin)

##############################################
class Job:
    def __init__(self, period, callback):
        self.period = period
        self.cb_function = callback[0]
        self.cb_args = callback[1:]
        self.update_ntime()

    def update_ntime(self, now=None):
        if now is None:
            now = time.time()
        self.ntime = now + self.period
        
    def run(self, now=None):
        if self.cb_function(*self.cb_args):
            self.update_ntime(now)

##############################################
class Scheduler:
    def __init__(self):
        self.jobs = []
        
    def add_job(self, job, run=True):
        self.jobs.append(job)
        if run: 
            job.run()

    def remove_job(self, job):
        self.jobs.remove(job)

    def update(self):
        now = time.time()
        for job in self.jobs:
            if now > job.ntime:
                job.run(now)