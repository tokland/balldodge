#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
import optparse
import sys
import os

from game import DodgeBallGame
from menu import Menu
import gamelib

# TODO:
# - time-limited transparent option for playing

max_tick = 0.05
loop_wait = 0.0001

#############################################
class DodgeBall:
    def __init__(self, screen_mode, screen_size, verbose=False):
        self.verbose = verbose
        flags = gamelib.consts.HWSURFACE | gamelib.consts.DOUBLEBUF
        if screen_mode == "fullscreen": 
            flags |= gamelib.consts.FULLSCREEN
            mouse = False
        else: mouse = True
        self.basegame = gamelib.BaseGame(flags, screen_size, \
            show_mouse=mouse, show_fps=bool(verbose), \
            loop_wait=loop_wait, max_tick=max_tick)

    def run(self):
        audio = gamelib.is_mixer_init()
        menu = Menu(self.basegame, audio)
        while 1:
            option = menu.run()
            if option == "play":
                music, sound = menu.get_enabled_audio()
                game = DodgeBallGame(self.basegame, music, sound)
                game.run()
            elif option == "exit":
                break

    def run_game(self):
        game = DodgeBallGame(self.basegame)
        game.run()

##############################################
def main():
    name = os.path.basename(sys.argv[0])
    usage = """usage: %s [options]"""%name
    parser = optparse.OptionParser(usage)
    parser.add_option('-v', '--verbose', dest='verbose', action="count", \
        help='Increase verbose messages')
    parser.add_option('-m', '--screen-mode', dest='screen_mode', type="string", \
        default="fullscreen", help = 'Screen mode (window|fullscreen)')
    parser.add_option('-s', '--screen-size', dest='screen_size', type="string", \
        default="1024x768", help = 'Screen size (WIDTHxHEIGHT)')
    parser.add_option('-d', '--disable-psyco', dest='disable_psyco', \
        action="store_true", default=False, help = 'Disable Psyco x86 acceleration')
    options, args = parser.parse_args()
    if not options.disable_psyco:
        if not gamelib.load_psyco():
            sys.stderr.write("warning: psyco not found\n")
    screen_size = tuple([int(x) for x in options.screen_size.split("x")])
    dbgame = DodgeBall(screen_mode=options.screen_mode, \
    screen_size=screen_size, verbose=options.verbose)
    if options.verbose >= 2:
        dbgame.run_game()
    else: dbgame.run()
    
##########
####################################
if __name__ == '__main__':
    main()
