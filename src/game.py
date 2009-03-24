import pygame
import random
import time

from player import Player
from board import Board
from ball import Ball
import gamelib

#######################
class DodgeBallGame:
    def __init__(self, basegame, music=True, sound=True):
        self.basegame = basegame
        self.music = music
        self.sound = sound
        self.game_config = gamelib.load_configuration("config/game.conf")
        self.screen_size = basegame.get_screen_size()
        self.display = basegame.get_display()
        f = self.basegame.adjust_size
        c = self.game_config.messages
        mf = gamelib.load_font(c.font.path, f(c.font.size, int))
        self.messages = gamelib.Struct(font=mf, color=c.font.color)
        c = self.game_config.status
        sf = gamelib.load_font(c.font.path, f(c.font.size, int))
        self.status = gamelib.Struct(font=sf, color=c.font.color, 
            fields=c.fields)
        self.maxlevel = self.game_config.levels[-1]
        self.current_level = None
        self.init_sound()
        self.background = self.basegame.enable_background()
                    
    def init_sound(self):
        if not self.sound:
            return
        sounds = ((name, gamelib.load_sound(path)) for name, path in 
            vars(self.game_config.sounds).iteritems())
        self.sounds = gamelib.Struct(**dict(sounds))
        
    def run(self):
        self.level = self.game_config.levels[0]
        self.lives = self.game_config.lives
        while 1:
            self.init_level(self.level)
            if not self.play_level():
                break
            
    def play_level(self):
        cancel_key = self.game_config.controls.cancel_game
        self.draw_background()
        check_key = self.basegame.check_pressed_key
        while 1:
            # Update
            if self.basegame.get_events() is None:
                return
            if check_key(cancel_key):
                self.playing = False
                self.show_message("cancel")
            tick = self.get_tick()
            self.update_game(tick)
            self.update_status(tick)
            state = self.update_messages(tick)
            
            # Draw
            self.basegame.draw_background(redraw=True)
            dirty = []
            self.draw_game(dirty)
            self.draw_messages(dirty)
            self.draw_status(dirty)
            self.basegame.draw_screen(dirty)
            
            # Compute next state
            loopstate = self.process_state(state)
            if loopstate == "return":
                return
            elif loopstate == "break":
                break
        return True
        
    def process_state(self, state):
        if state == "start_go":
            self.show_message("start_go")
            self.playing = True
        elif state == "return_menu":
            return "return"
        elif state == "repeat_level":
            self.lives -= 1
            if self.lives < 1:
                self.show_message("game_over")
                self.play_sound("game_over")
            else: return "break"
        elif state == "next_level":
            self.level += 1
            return "break"

    def update_status(self, tick):
        return

    def draw_status(self, dirty):
        for field in "level", "lives", "time":
            cfield = vars(self.status.fields)[field]
            text = self.process_text(cfield.text)
            s = self.status.font.render(text, True, self.status.color)
            rect = self.display.blit(s, \
                self.basegame.adjust_size(cfield.pos, int))
            dirty.append(rect)

    def update_messages(self, tick):
        if not self.messages.status:
            return
        self.messages.timeout -= tick
        if self.messages.timeout < 0:
            if not self.messages.texts:
                self.messages.status = False
                return self.messages.state
            self.messages.text = self.messages.texts.pop()
            self.messages.timeout = self.messages.steptime
            
    def draw_messages(self, dirty):
        if not self.messages.status:
            return
        text = self.process_text(self.messages.text)
        s = self.messages.font.render(text, True, self.messages.color)
        pos = [(a-b)/2 for (a, b) in zip(self.screen_size, s.get_size())]
        rect = self.display.blit(s, pos)
        dirty.append(rect)

    def update_game(self, tick):
        if not self.playing:
            return
        bricks_set = self.player.update(self.board, self.balls, tick, 
            self.basegame.check_pressed_key)
        for x in range(bricks_set):
            self.play_sound("discover")
        collide = False
        for ball in self.balls:
            collide |= ball.update(self.player, self.board, tick, 
                self.basegame.check_pressed_key)		
        if 1 and collide: # DEBUG
            self.playing = False
            self.play_sound("collision")
            self.show_message("collision")
            return
        self.balls_rebounds(self.balls)
        self.remaintime -= tick
        if self.remaintime < 0:
            self.remaintime = 0.0
            self.playing = False
            self.play_sound("time_ended")
            self.show_message("time_ended")
        elif self.board.get_nbricks_unset() == 0:
            self.play_sound("completed")
            self.playing = False
            if self.level < self.maxlevel:
                self.show_message("level_done")
            else: self.show_message("game_finished")

    def draw_game(self, dirty):
        d = dirty.extend
        rect_bricks = self.board.draw_bricks(self.background)
        if rect_bricks:
            self.board.draw_background(self.background)
        d(rect_bricks)
        self.basegame.draw_background()
        d(self.player.draw(self.display))
        for ball in self.balls:
            d(ball.draw(self.display))
        
    #############

    def process_text(self, text):
        subs = {"level": self.level, "maxlevel": self.maxlevel, \
            "lives": self.lives, "time": self.remaintime}
        return text%subs

    def get_tick(self):
        return self.basegame.get_tick()

    def init_level(self, level):
        if self.load_level(level):
            self.show_message("present", self.level_config.messages, "start_go")
        else: self.show_message("start")
        self.level = level
        self.playing = False
        self.remaintime = self.level_config.time
        self.basegame.init_timer()

    def show_message(self, fieldname, config=None, state=None):
        if config is None:
            config = self.game_config.messages.fields
        sfield = vars(config)[fieldname]
        self.messages.status = True
        if sfield.type == "text":
            self.messages.texts = [sfield.text]
        elif sfield.type == "textlist":
            self.messages.texts = list(reversed(sfield.texts[:]))
        elif sfield.type == "random":
            index = random.randint(0, len(sfield.texts)-1)
            self.messages.texts = [sfield.texts[index]]
        if state is None:
            state = sfield.state
        self.messages.state = state
        self.messages.text = self.messages.texts.pop()
        self.messages.steptime = sfield.time
        self.messages.timeout = self.messages.steptime

    def draw_background(self):
        self.background.fill((0, 0, 0))
        self.board.draw_bricks(self.background, redraw=True)
        self.board.draw_background(self.background)
        self.basegame.draw_background(redraw=True)
        self.basegame.draw_screen()
        
    def balls_rebounds(self, balls):
        nb = len(balls)
        for index1 in range(nb-1):
            ball1 = balls[index1]
            for index2 in range(index1+1, nb):
                ball2 = balls[index2]
                ball1.update_collision_with_ball(ball2)

    def load_level(self, level):
        if level == self.current_level:
            self.restart_level()
            return False
        self.current_level = level
        filename = "levels/level%d.conf"%level
        clevel = gamelib.load_configuration(filename)
        self.level_config = clevel
        tostruct = lambda d: gamelib.Struct(**d)
        ref = [(float(x)/100.0) for x in self.screen_size]
        scale = self.basegame.adjust_size
        # Balls
        balls = [(bdef.radius, bdef, Ball(radius=scale(bdef.radius), solid=bdef.solid, \
                electron=bdef.electron, color=bdef.color)) \
                for bdef in [tostruct(x) for x in clevel.balls]]
        extract = lambda i: [x[i] for x in sorted(balls, reverse=True)]
        self.balls_config = extract(1)
        self.balls = extract(2)
        # Player
        cp = clevel.player
        btd = self.game_config.bricks_triangles_depth
        self.player = Player(cp.color, cp.figure, fsize=ref, \
            bricks_triangles_depth=btd)
        self.player.set_speed(scale(cp.speed), cp.rotate_speed)
        self.player.set_controls(self.game_config.controls)
        # Board
        if self.game_config.brick_mode == "image":
            background = clevel.background
        else: background = None
        self.board = Board(clevel.board.color, (100, 100), clevel.board.figures, background, \
            fsize=ref, partition=clevel.brick_partition)
        if vars(clevel).has_key("music"):
            self.play_music(clevel.music)
        self.restart_level()
        return True

    def play_music(self, music):
        if self.music:
            gamelib.load_music(music)
            gamelib.play_music()
            
    def play_sound(self, name):
        if self.sound:
            vars(self.sounds)[name].play()

    def restart_level(self):
        scale = self.basegame.adjust_size
        for ball, bdef in zip(self.balls, self.balls_config):
            ball.set_speed(scale(bdef.speed))
            ball.set_pos(scale(bdef.pos))
        self.player.set_angle(0.0)
        self.player.set_pos(scale(self.level_config.player.initial_pos))
