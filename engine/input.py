"""
Input handler for Infinite Harvester
"""

import pygame 

class InputHandler:
    def __init__(self):
        self.keys_held   = {}
        self.keys_down   = {}
        self.keys_up     = {}
        self.mouse_pos   = (0,0)
        self.mouse_buttons = [False, False, False]
        self.mouse_down    = [False, False, False]
        self.mouse_up      = [False, False, False]
        self.scroll_delta  = 0

    
    def process_events(self, events):
        self.keys_down   = {}
        self.keys_up     = {}
        self.mouse_down  = [False, False, False]
        self.mouse_up    = [False, False, False]
        self.scroll_delta = 0

        for event in events:
            if event.type == pygame.KEYDOWN:
                self.keys_down[event.key] = True
                self.keys_held[event.key] = True
            elif event.type == pygame.KEYUP:
                self.keys_up[event.key]  = True
                self.keys_held[event.key] =False
            elif event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button <= 3:
                    self.mouse_buttons[event.button - 1] = True
                    self.mouse_down[event.button - 1]  = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button <= 3:
                    self.mouse_buttons[event.button - 1] = False
                    self.mouse_up[event.button - 1] = True
            elif event.type == pygame.MOUSEWHEEL:
                self.scroll_data = event.y
    
    def key_held(self, key):
        return self.keys_held.get(key, False)
    
    def key_pressed(self, key):
        return self.keys_down.get(key, False)
    
    def key_released(self, key):
        return self.keys_up.get(key, False)
    
    def lmb_down(self):
        return self.mouse_down[0]
    
    def lmb_held(self):
        return self.mouse_buttons[0]
    
    def rmb_down(self):
        return self.mouse_down[2]
    
