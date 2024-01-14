
import pygame
from .Screens import Screens
from scripts.game_structure.game_essentials import game

class IntroScreen(Screens):
    def __init__(self, name=None):
        super().__init__(name)
        if game.settings['fullscreen']:
            screen_x, screen_y = 1600, 1400
            self.screen = pygame.display.set_mode((screen_x, screen_y), pygame.FULLSCREEN | pygame.SCALED)
        else:
            screen_x, screen_y = 800, 700
            self.screen = pygame.display.set_mode((screen_x, screen_y))
        # self.font = font
        self.clock = None
        if game.settings['fullscreen']:
            self.fade_surface = pygame.Surface((1600, 1400))
        else:
            self.fade_surface = pygame.Surface((800, 700))
        self.alpha = 0
        self.text = "But mom..."
        self.fading_in = False
        self.fading_out = False
        self.final_fade = False
        

    def draw_text(self, text, color):
        self.font = pygame.font.SysFont('georgia', 45)
        text_obj = self.font.render(text, 1, color)
        text_rect = text_obj.get_rect()
        text_rect.center = (400, 300)
        self.fade_surface.blit(text_obj, text_rect)

    def fade_in(self):
        if self.alpha < 250:
            self.fade_surface.fill((0,0,0))
            self.fade_surface.set_alpha(self.alpha)
            self.draw_text(self.text, (255, 0, 0))
            self.screen.blit(self.fade_surface, (0, 0))
            self.alpha += 5
        else:
            self.text = "It's dark in the woods..."
            self.fading_in = False
            self.fading_out = True

    def fade_out(self):
        if self.alpha > 0:
            self.fade_surface.fill((0,0,0))
            self.fade_surface.set_alpha(self.alpha)
            if not self.final_fade:
                self.draw_text(self.text, (255, 0, 0))
            self.screen.blit(self.fade_surface, (0, 0))
            self.alpha -= 2
        else:
            if not self.final_fade:
                self.final_fade = True
                self.alpha = 0  # Reset alpha to max for final fade
                self.change_screen('make clan screen')
                self.text = "It's dark in the woods..."
            else:
                self.fading_out = False
                
    def screen_switches(self):
        self.fading_in = True
        self.final_fade = False
            
    def on_use(self):
        self.clock = pygame.time.Clock()
        font = pygame.font.Font(None, 64)

        if self.fading_in:
            self.fade_in()

        if self.fading_out:
            self.fade_out()
        self.clock.tick(60)