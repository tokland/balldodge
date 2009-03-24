import pygame
import math

import gamelib

# TODO: Implement BaseMenu class

#######################
class BaseMenu:
    def __init__(self, basegame, config, audio=True):
        self.basegame = basegame
        self.config = config
        self.audio = audio
        self.screen_size = basegame.get_screen_size()
        self.display = basegame.get_display()
        self.noptions = len(self.config.menu.entries)
        self.init_title(self.config.title)
        self.init_entries(self.config.menu)
        if self.audio:
            move = gamelib.load_sound(self.config.menu.sounds.move)
            select = gamelib.load_sound(self.config.menu.sounds.select)
            self.sounds = gamelib.Struct(move=move, select=select)
        self.ticks = 0.0
        self.background = self.basegame.load_image(self.config.background, \
            size=self.screen_size)

    def run(self, option=0):
        self.music = False
        self.play_music()
        self.option = option
        self.display.blit(self.background, (0, 0))
        self.basegame.draw_screen()
        self.basegame.init_timer()
        while 1:
            # Update
            events = self.basegame.get_events()
            if events is None:
                return
            if self.process_events(events):
                return self.entries[self.option][0]
            tick = self.basegame.get_tick()
            self.update_menu(tick)
            # Draw
            dirty = []
            self.display.blit(self.background, (0, 0))
            self.draw_menu(dirty)
            self.basegame.draw_screen(dirty)

    def get_enabled_audio(self):
        return [x in self.audio_mode for x in "music", "sound"]

    def play_music(self):
        if not self.audio:
            return
        if "music" in self.audio_mode:
            if not self.music:
                gamelib.load_music(self.config.music)
                gamelib.play_music()
                self.music = True
        else:
            gamelib.stop_music()
            self.music = False
            
    def play_sound(self, name):
        if not self.audio:
            return
        if "sound" in self.audio_mode:
            vars(self.sounds)[name].play()
        
    def init_title(self, config):
        font = gamelib.load_font(config.font.path, 128)
        s = font.render(config.text, True, config.font.color)
        (x1, y1), (x2, y2) = [self.basegame.adjust_size(x, int) for x in config.rect]
        s = pygame.transform.scale(s, (x2-x1, y2-y1))
        self.title = gamelib.Struct(surface=s, pos=(x1, y1))
        
    def init_entries(self, config):
        self.entries = config.entries
        self.entries_font = gamelib.load_font(config.font.path, \
            self.basegame.adjust_size(config.font.size))
        self.current_choice = {}
        for name, info in self.entries:
            info = gamelib.Struct(**info)
            if info.type == "choice":
                if pygame.mixer.get_init():
                    choice = info.audio_choice
                else: choice = info.nonaudio_choice
                self.audio_mode = info.choices[choice][0]
                self.current_choice[name] = choice

    def process_events(self, events):
        c = self.config.controls
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if self.basegame.check_key(event, c.down):
                self.play_sound("move")
                self.option = (self.option+1)%self.noptions
            elif self.basegame.check_key(event, c.up):
                self.play_sound("move")
                self.option = (self.option-1)%self.noptions
            elif self.basegame.check_keys(event, c.select):
                self.play_sound("select")
                name, info = self.entries[self.option]
                info = gamelib.Struct(**info)
                if info.type == "choice":
                    next = (self.current_choice[name]+1)%len(info.choices)
                    nam = info.choices[next][0]
                    if nam and not self.audio_mode:
                        if not self.init_audio():
                            continue
                    self.current_choice[name] = next
                    self.audio_mode = nam
                    self.play_music()
                elif info.type == "return":
                    return True

    def init_audio(self):
        try: pygame.mixer.init()
        except pygame.error: return False
        return True

    def update_menu(self, tick):
        self.ticks += tick
    
    def draw_menu(self, dirty):
        c = self.config.menu
        y, y1 = self.basegame.adjust_size(c.ylimits)
        incy = (y1-y) / self.noptions
        rect = self.display.blit(self.title.surface, self.title.pos)
        dirty.append(rect)
        for opt, (name, info) in enumerate(self.entries):
            info = gamelib.Struct(**info)
            if opt == self.option:
                color = c.font.selected_color
                factor = 1.0+0.5*math.sin(self.ticks*\
                    c.font.selected_color_speed)
                color = [max(0, min(255, (x*factor))) for x in color]
            else: color = c.font.color
            text = info.text
            if info.type == "choice":
                oid, t = info.choices[self.current_choice[name]]
                text += " %s"%t
            s = self.entries_font.render(text, True, color)
            x = (self.screen_size[0]-s.get_size()[0])/2
            rect = self.display.blit(s, (x, y))
            y += incy
            dirty.append(rect)

#######################
class Menu(BaseMenu):
    def __init__(self, basegame, audio):
        config = gamelib.load_configuration("config/menu.conf")
        BaseMenu.__init__(self, basegame, config, audio)
