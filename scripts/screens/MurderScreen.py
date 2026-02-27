import pygame.transform
import pygame_gui.elements
from random import choice, randint
import ujson
import math
import re
from scripts.cat.history import History
from scripts.event_class import Single_Event

from .Screens import Screens
from scripts.utility import (
    get_text_box_theme, 
    scale, 
    process_text, 
    pronoun_repl, 
    # neonpink!
    get_alive_status_cats,
    check_relationship_value
    )
from scripts.cat.cats import Cat, INJURIES
from scripts.game_structure import image_cache
from scripts.game_structure.ui_elements import UIImageButton, UISpriteButton
from scripts.game_structure.game_essentials import game, screen, screen_x, screen_y, MANAGER
from scripts.cat.skills import SkillPath

class MurderScreen(Screens):
    selected_cat = None
    accomplice_cat = None
    current_page = 1
    list_frame = None
    apprentice_details = {}
    selected_details = {}
    cat_list_buttons = {}
    stage = 'choose murder cat'

    def __init__(self, name=None):
        super().__init__(name)
        self.list_page = None
        self.next_cat = None
        self.previous_cat = None
        self.next_page_button = None
        self.previous_page_button = None
        self.current_mentor_warning = None
        self.confirm_mentor = None
        self.randomiser_button = None
        self.back_button = None
        self.next_cat_button = None
        self.mentor_icon = None
        self.app_frame = None
        self.mentor_frame = None
        self.accomplice_frame = None
        self.methodtext = None
        self.locationtext = None
        self.timetext = None
        self.attackmethod = None
        self.poisonmethod = None
        self.accidentmethod = None
        self.predatormethod = None
        self.camplocation = None
        self.territorylocation = None
        self.borderlocation = None
        self.dawntime = None
        self.daytime = None
        self.nighttime = None
        self.current_mentor_text = None
        self.info = None
        self.heading = None
        self.subtitle = None
        self.mentor = None
        self.the_cat = None
        self.murder_cat = None
        self.next = None
        self.prev = None
        self.method = None
        self.location = None
        self.time = None
        self.methodinfo = None
        self.methodheading = None
        self.locationinfo = None
        self.locationheading = None
        self.timeinfo = None
        self.timeheading = None
        self.your_sprite = None
        self.victim_sprite = None
        self.victim_info = None
        self.victim_name = None
        self.chancetext = None
        self.willingnesstext = None

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.confirm_mentor and self.selected_cat and self.stage == 'choose murder cat':
                if not self.selected_cat.dead:
                    self.exit_screen()
                    self.cat_to_murder = self.selected_cat

                    self.stage = 'choose murder method'

                    self.method = choice(["attack", "poison", "accident", "predator"])
                    self.location = choice(["camp", "territory", "border"])
                    self.time = choice(["dawn", "day", "night"])

                    self.screen_switches()
                    self.print_chances(self.selected_cat, accomplice=None)

            elif event.ui_element in self.cat_list_buttons.values():
                if self.stage == "choose accomplice":
                    self.update_chance_text(self.cat_to_murder, accomplice=self.selected_cat)
                else:
                    self.update_chance_text(self.selected_cat, accomplice=None)
                if event.ui_element.return_cat_object() == self.selected_cat:
                    self.selected_cat = None
                    self.confirm_mentor.disable()
                    if self.willingnesstext:
                        self.willingnesstext.hide()
                    if self.chancetext:
                        self.chancetext.hide()
                else:
                    if self.stage == "choose accomplice":
                        self.update_chance_text(self.cat_to_murder, accomplice=self.selected_cat)
                    else:
                        self.update_chance_text(self.selected_cat, accomplice=None)
                    self.confirm_mentor.enable()
                    self.selected_cat = event.ui_element.return_cat_object()
                    if self.willingnesstext:
                        self.willingnesstext.hide()
                    if self.chancetext:
                        self.chancetext.hide()

                if self.stage == "choose murder cat":
                    self.chancetext = None
                    self.update_selected_cat()
                    self.print_chances(self.selected_cat, accomplice=None)
                elif self.stage == "choose accomplice":
                    self.chancetext = None
                    self.update_selected_cat2()
                    self.print_chances(self.cat_to_murder, accomplice=self.selected_cat)
            
            elif event.ui_element == self.confirm_mentor and self.method and self.location and self.time and self.stage == 'choose murder method':
                if not self.selected_cat.dead:
                    self.exit_screen()
                    self.selected_cat = None
                    self.stage = 'choose accomplice'
                    self.screen_switches()
                    self.confirm_mentor.disable()

            elif event.ui_element == self.randomiser_button and self.stage == "choose murder method":
                self.method = choice(["attack", "poison", "accident", "predator"])
                self.location = choice(["camp", "territory", "border"])
                self.time = choice(["dawn", "day", "night"])

                self.update_murder_buttons()
                self.update_method_info()
                self.update_chance_text(self.cat_to_murder, accomplice=None)
                self.print_chances(self.selected_cat, accomplice=None)
            
            elif event.ui_element == self.confirm_mentor and self.selected_cat:
                r = randint(1,100)
                accompliced = False
                chance = self.get_accomplice_chance(game.clan.your_cat, self.selected_cat, self.cat_to_murder)
                if game.config["accomplice_chance"] != -1:
                    try:
                        chance = game.config["accomplice_chance"]
                    except:
                        pass
                if r < chance:
                    accompliced = True
                    if 'accomplices' in game.switches:
                        game.switches['accomplices'].append(self.selected_cat.ID)
                    else:
                        game.switches['accomplices'] = []
                        game.switches['accomplices'].append(self.selected_cat.ID)
                                            
                self.change_cat(self.murder_cat, self.selected_cat, accompliced)
                self.stage = 'choose murder cat'

            elif self.stage == 'choose murder method' and event.ui_element == self.next:
                self.change_cat(self.murder_cat, None, None)
                self.stage = 'choose murder cat'
            
            elif self.stage == 'choose accomplice' and event.ui_element == self.next:
                self.change_cat(self.murder_cat, None, None)
                self.stage = 'choose murder cat'
            
            elif event.ui_element == self.prev:
                if self.stage == "choose murder method":
                    self.stage = "choose murder cat"
                    self.method = None 
                    self.location = None
                    self.time = None
                    self.exit_screen()
                    self.screen_switches()
                elif self.stage == "choose accomplice":
                    self.stage = "choose murder method"
                    self.exit_screen()
                    self.screen_switches()

            elif event.ui_element == self.back_button:
                self.change_screen('profile screen')
                self.stage = 'choose murder cat'

                # reset cats
                self.selected_cat = None
                self.cat_to_murder = None

            # Method buttons
            elif event.ui_element == self.attackmethod:
                self.method = 'attack'
                self.attackmethod.disable()
                self.poisonmethod.enable()
                self.accidentmethod.enable()
                self.predatormethod.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)
            elif event.ui_element == self.poisonmethod:
                self.method = 'poison'
                self.poisonmethod.disable()
                self.attackmethod.enable()
                self.accidentmethod.enable()
                self.predatormethod.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)
            elif event.ui_element == self.accidentmethod:
                self.method = 'accident'
                self.accidentmethod.disable()
                self.poisonmethod.enable()
                self.attackmethod.enable()
                self.predatormethod.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)
            elif event.ui_element == self.predatormethod:
                self.method = 'predator'
                self.predatormethod.disable()
                self.poisonmethod.enable()
                self.accidentmethod.enable()
                self.attackmethod.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)

            # Location buttons
            elif event.ui_element == self.camplocation:
                self.location = 'camp'
                self.camplocation.disable()
                self.territorylocation.enable()
                self.borderlocation.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)
            elif event.ui_element == self.territorylocation:
                self.location = 'territory'
                self.territorylocation.disable()
                self.camplocation.enable()
                self.borderlocation.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)
            elif event.ui_element == self.borderlocation:
                self.location = 'border'
                self.borderlocation.disable()
                self.territorylocation.enable()
                self.camplocation.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)

            # Time buttons
            elif event.ui_element == self.dawntime:
                self.time = 'dawn'
                self.dawntime.disable()
                self.daytime.enable()
                self.nighttime.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)
            elif event.ui_element == self.daytime:
                self.time = 'day'
                self.daytime.disable()
                self.dawntime.enable()
                self.nighttime.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)
            elif event.ui_element == self.nighttime:
                self.time = 'night'
                self.nighttime.disable()
                self.daytime.enable()
                self.dawntime.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)

            elif event.ui_element == self.next_cat_button:
                if isinstance(Cat.fetch_cat(self.next_cat), Cat):
                    game.switches['cat'] = self.next_cat
                    self.update_cat_list()
                    self.update_selected_cat()
                    self.print_chances(self.selected_cat, accomplice=None)
                    # self.update_buttons()
                else:
                    print("invalid next cat", self.next_cat)
            elif event.ui_element == self.next_page_button:
                self.current_page += 1
                if self.stage == "choose murder cat":
                    self.update_cat_list()
                else:
                    self.update_cat_list2()
            elif event.ui_element == self.previous_page_button:
                self.current_page -= 1
                if self.stage == "choose murder cat":
                    self.update_cat_list()
                else:
                    self.update_cat_list2()

    def update_murder_buttons(self):
        """ updates the method, location and time buttons for the randomiser to work """
        if self.method == "attack":
            self.attackmethod.disable()
            self.poisonmethod.enable()
            self.accidentmethod.enable()
            self.predatormethod.enable()
        elif self.method == "poison":
            self.attackmethod.enable()
            self.poisonmethod.disable()
            self.accidentmethod.enable()
            self.predatormethod.enable()
        elif self.method == "accident":
            self.attackmethod.enable()
            self.poisonmethod.enable()
            self.accidentmethod.disable()
            self.predatormethod.enable()
        elif self.method == "predator":
            self.attackmethod.enable()
            self.poisonmethod.enable()
            self.accidentmethod.enable()
            self.predatormethod.disable()

        if self.location == "camp":
            self.camplocation.disable()
            self.territorylocation.enable()
            self.borderlocation.enable()
        elif self.location == "territory":
            self.camplocation.enable()
            self.territorylocation.disable()
            self.borderlocation.enable()
        elif self.location == "border":
            self.camplocation.enable()
            self.territorylocation.enable()
            self.borderlocation.disable()

        if self.time == "dawn":
            self.dawntime.disable()
            self.daytime.enable()
            self.nighttime.enable()
        elif self.time == "day":
            self.dawntime.enable()
            self.daytime.disable()
            self.nighttime.enable()
        elif self.time == "night":
            self.dawntime.enable()
            self.daytime.enable()
            self.nighttime.disable()

        

    def screen_switches(self):

        if self.stage == 'choose murder cat':
            self.the_cat = game.clan.your_cat
            self.mentor = Cat.fetch_cat(self.the_cat.mentor)
            
            self.next = None
            self.prev = None
            self.methodheading = None
            self.methodinfo = None
            self.locationinfo = None
            self.timeinfo = None
            self.timeheading = None
            self.locationheading = None
            self.accomplice_frame = None
            self.victim_sprite = None
            self.victim_info = None
            self.victim_name = None
            self.randomiser_button = None
            self.chancetext = None
            self.willingnesstext = None

            self.list_frame = pygame.transform.scale(image_cache.load_image("resources/images/choosing_frame.png").convert_alpha(),
                                        (1300 / 1600 * screen_x, 452 / 1400 * screen_y))
            
            self.heading = pygame_gui.elements.UITextBox("<b>Your target</b>",
                                                        scale(pygame.Rect((300, 50), (1000, 80))),
                                                        object_id=get_text_box_theme("#text_box_34_horizcenter"),
                                                        manager=MANAGER)
            
            self.subtitle = pygame_gui.elements.UITextBox("Who will be your victim?",
                                                        scale(pygame.Rect((300, 90), (1000, 80))),
                                                        object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                        manager=MANAGER)
            
            # Layout Images:
            self.mentor_frame = pygame_gui.elements.UIImage(scale(pygame.Rect((150, 175), (400, 540))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/victim_panel.png").convert_alpha(),
                                                                (569, 399)), manager=MANAGER)
            self.your_sprite = pygame_gui.elements.UIImage(
                                            scale(pygame.Rect((650, 360), (300, 300))),
                                            pygame.transform.scale(
                                                self.the_cat.sprite,
                                                (300, 300)), manager=MANAGER)
            
            self.methodtext = pygame_gui.elements.UITextBox("Method:",
                                                        scale(pygame.Rect((1110, 155), (200, 80))),
                                                        object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                        manager=MANAGER)
        
            self.attackmethod = pygame_gui.elements.UIImage(scale(pygame.Rect((987, 220), (110, 110))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/attackmethod_grey.png").convert_alpha(),
                                                                (110,110)), manager=MANAGER)
            
            self.poisonmethod = pygame_gui.elements.UIImage(scale(pygame.Rect((1105, 220), (110, 110))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/poisonmethod_grey.png").convert_alpha(),
                                                                (110,110)), manager=MANAGER)
            
            self.accidentmethod = pygame_gui.elements.UIImage(scale(pygame.Rect((1220, 220), (110, 110))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/accidentmethod_grey.png").convert_alpha(),
                                                                (110,110)), manager=MANAGER)
            self.predatormethod = pygame_gui.elements.UIImage(scale(pygame.Rect((1335, 220), (110, 110))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/predatormethod_grey.png").convert_alpha(),
                                                                (110,110)), manager=MANAGER)
            
            self.accidentmethod.disable()
            self.predatormethod.disable()
           

            self.locationtext = pygame_gui.elements.UITextBox("Location:",
                                                        scale(pygame.Rect((1110, 335), (200, 80))),
                                                        object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                        manager=MANAGER)

            self.camplocation = pygame_gui.elements.UIImage(scale(pygame.Rect((1045, 400), (110, 110))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/camplocation_grey.png").convert_alpha(),
                                                                (110,110)), manager=MANAGER)
            self.territorylocation = pygame_gui.elements.UIImage(scale(pygame.Rect((1165, 400), (110, 110))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/territorylocation_grey.png").convert_alpha(),
                                                                (110,110)), manager=MANAGER)
            self.borderlocation = pygame_gui.elements.UIImage(scale(pygame.Rect((1285, 400), (110, 110))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/borderlocation_grey.png").convert_alpha(),
                                                                (110,110)), manager=MANAGER)
            
            self.camplocation.disable()
            self.territorylocation.disable()
            self.borderlocation.disable()

            self.timetext = pygame_gui.elements.UITextBox("Time:",
                                                        scale(pygame.Rect((1110, 515), (200, 80))),
                                                        object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                        manager=MANAGER)

            self.dawntime = pygame_gui.elements.UIImage(scale(pygame.Rect((1045, 580), (110, 110))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/dawntime_grey.png").convert_alpha(),
                                                                (110,110)), manager=MANAGER)
            
            self.daytime = pygame_gui.elements.UIImage(scale(pygame.Rect((1165, 580), (110, 110))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/daytime_grey.png").convert_alpha(),
                                                                (110,110)), manager=MANAGER)
            
            self.nighttime = pygame_gui.elements.UIImage(scale(pygame.Rect((1285, 580), (110, 110))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/nighttime_grey.png").convert_alpha(),
                                                                (110,110)), manager=MANAGER)
            
            self.back_button = UIImageButton(scale(pygame.Rect((50, 1290), (204, 60))), "", object_id="#back_button")

            self.confirm_mentor = UIImageButton(scale(pygame.Rect((696, 688), (208, 52))), "",
                                                tool_tip_text= "",
                                                object_id="#continue_button_small")
        
            self.previous_page_button = UIImageButton(scale(pygame.Rect((630, 1229), (68, 68))), "",
                                                    object_id="#relation_list_previous", manager=MANAGER)
            self.next_page_button = UIImageButton(scale(pygame.Rect((902, 1229), (68, 68))), "",
                                                object_id="#relation_list_next", manager=MANAGER)
            
            self.next = UIImageButton(scale(pygame.Rect((942, 680), (68, 68))), "",
                                                tool_tip_text= "Proceed without an accomplice.",
                                                object_id="#arrow_right_button", manager=MANAGER)
            
            self.prev = UIImageButton(scale(pygame.Rect((590, 680), (68, 68))), "",
                                                object_id="#arrow_left_button", manager=MANAGER)
            
            self.prev.disable()
            self.next.disable()

            self.update_selected_cat()  # Updates the image and details of selected cat
            self.update_cat_list()

        elif self.stage == 'choose murder method':
            self.the_cat = game.clan.your_cat
            self.mentor = Cat.fetch_cat(self.the_cat.mentor)
            self.selected_cat = self.cat_to_murder
            self.next = None
            self.methodinfo = None
            self.locationinfo = None
            self.locationheading = None
            self.methodheading = None
            self.timeinfo = None
            self.timeheading = None
            self.accomplice_frame = None
            self.victim_sprite = None
            self.victim_info = None
            self.victim_name = None
            self.willingnesstext = None
            self.chancetext = None

            self.list_frame = None

            self.heading = pygame_gui.elements.UITextBox("<b>Your plan</b>",
                                                        scale(pygame.Rect((300, 50), (1000, 80))),
                                                        object_id=get_text_box_theme("#text_box_34_horizcenter"),
                                                        manager=MANAGER)
            self.subtitle = pygame_gui.elements.UITextBox("Choose wisely, or you could end up dead.",
                                                        scale(pygame.Rect((300, 90), (1000, 80))),
                                                        object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                        manager=MANAGER)
           
            # Layout Images:
            self.mentor_frame = pygame_gui.elements.UIImage(scale(pygame.Rect((150, 175), (400, 540))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/victim_panel.png").convert_alpha(),
                                                                (569, 399)), manager=MANAGER)
            
            self.selected_details["selected_image"] = pygame_gui.elements.UIImage(
                                            scale(pygame.Rect((210, 190), (270, 270))),
                                            pygame.transform.scale(
                                                self.selected_cat.sprite,
                                                (270, 270)), manager=MANAGER)
           
            
            self.your_sprite = pygame_gui.elements.UIImage(
                                            scale(pygame.Rect((650, 360), (300, 300))),
                                            pygame.transform.scale(
                                                self.the_cat.sprite,
                                                (300, 300)), manager=MANAGER)
            

            self.methodtext = pygame_gui.elements.UITextBox("Method:",
                                                        scale(pygame.Rect((1110, 155), (200, 80))),
                                                        object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                        manager=MANAGER)
        
            self.attackmethod = UIImageButton(scale(pygame.Rect((987, 220), (110, 110))), "",
                                                tool_tip_text= "Attack", object_id="#attack_method_button", manager=MANAGER)
            self.poisonmethod = UIImageButton(scale(pygame.Rect((1105, 220), (110, 110))), "",
                                                tool_tip_text= "Poison", object_id="#poison_method_button", manager=MANAGER)
            self.accidentmethod = UIImageButton(scale(pygame.Rect((1220, 220), (110, 110))), "",
                                                tool_tip_text= "Accident", object_id="#accident_method_button", manager=MANAGER)
            self.predatormethod = UIImageButton(scale(pygame.Rect((1335, 220), (110, 110))), "",
                                                tool_tip_text= "Predator", object_id="#predator_method_button", manager=MANAGER)
      
            self.locationtext = pygame_gui.elements.UITextBox("Location:",
                                                        scale(pygame.Rect((1110, 335), (200, 80))),
                                                        object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                        manager=MANAGER)

            self.camplocation = UIImageButton(scale(pygame.Rect((1045, 400), (110, 110))), "",
                                                tool_tip_text= "Camp", object_id="#camp_location_button", manager=MANAGER)
            
            self.territorylocation = UIImageButton(scale(pygame.Rect((1165, 400), (110, 110))), "",
                                                tool_tip_text= "Territory", object_id="#territory_location_button", manager=MANAGER)
            
            self.borderlocation = UIImageButton(scale(pygame.Rect((1285, 400), (110, 110))), "",
                                                tool_tip_text= "Border", object_id="#border_location_button", manager=MANAGER)
            
            self.timetext = pygame_gui.elements.UITextBox("Time:",
                                                        scale(pygame.Rect((1110, 515), (200, 80))),
                                                        object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                        manager=MANAGER)

            self.dawntime = UIImageButton(scale(pygame.Rect((1045, 580), (110, 110))), "",
                                                tool_tip_text= "Dawn", object_id="#dawntime_button", manager=MANAGER)
            self.daytime = UIImageButton(scale(pygame.Rect((1165, 580), (110, 110))), "",
                                                tool_tip_text= "Day", object_id="#daytime_button", manager=MANAGER)
            self.nighttime = UIImageButton(scale(pygame.Rect((1285, 580), (110, 110))), "",
                                                tool_tip_text= "Night", object_id="#nighttime_button", manager=MANAGER)
            
            self.randomiser_button = UIImageButton(scale(pygame.Rect((773, 270), (68, 68))), "",
                                           object_id="#random_dice_button",
                                           manager=MANAGER)
            
            self.back_button = UIImageButton(scale(pygame.Rect((50, 1290), (204, 60))), "", object_id="#back_button")
            self.confirm_mentor = UIImageButton(scale(pygame.Rect((696, 688), (208, 52))), "",
                                                object_id="#continue_button_small")
        
            self.previous_page_button = UIImageButton(scale(pygame.Rect((630, 1229), (68, 68))), "",
                                                    object_id="#relation_list_previous", manager=MANAGER)
            self.next_page_button = UIImageButton(scale(pygame.Rect((902, 1229), (68, 68))), "",
                                                object_id="#relation_list_next", manager=MANAGER)
            
            self.next = UIImageButton(scale(pygame.Rect((942, 680), (68, 68))), "",
                                                tool_tip_text= "Proceed without an accomplice.",
                                                object_id="#arrow_right_button", manager=MANAGER)
            
            self.prev = UIImageButton(scale(pygame.Rect((590, 680), (68, 68))), "",
                                                tool_tip_text= "Going back a step will re-randomise your plan.",
                                                object_id="#arrow_left_button", manager=MANAGER)
            
            self.previous_page_button.hide()
            self.next_page_button.hide()

            self.next.disable()

            self.update_method_info()
            self.update_murder_buttons()

            self.update_selected_cat()  # Updates the image and details of selected cat
            # self.update_cat_list()
        else:
            self.the_cat = game.clan.your_cat
            self.mentor = Cat.fetch_cat(self.the_cat.mentor)
            # self.selected_cat = None
            self.methodheading = None
            self.methodinfo = None
            self.locationinfo = None
            self.locationheading = None
            self.timeinfo = None
            self.timeheading = None

            self.methodtext = None

            self.attackmethod = None
            self.poisonmethod = None
            self.accidentmethod = None
            self.predatormethod = None

            self.camplocation = None
            self.territorylocation = None
            self.borderlocation = None

            self.dawntime = None
            self.daytime = None
            self.nighttime = None

            self.methodtext = None
            self.locationtext = None
            self.timetext = None

            self.chancetext = None
            self.willingnesstext = None

            self.randomiser_button = None

            self.list_frame = pygame.transform.scale(image_cache.load_image("resources/images/choosing_frame.png").convert_alpha(),
                                        (1300 / 1600 * screen_x, 452 / 1400 * screen_y))


            self.heading = pygame_gui.elements.UITextBox("<b>Your accomplice</b>",
                                                        scale(pygame.Rect((300, 50), (1000, 80))),
                                                        object_id=get_text_box_theme("#text_box_34_horizcenter"),
                                                        manager=MANAGER)
            self.subtitle = pygame_gui.elements.UITextBox("Will you need help?",
                                                        scale(pygame.Rect((300, 90), (1000, 80))),
                                                        object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                        manager=MANAGER)
            
            # Layout Images:
            self.mentor_frame = pygame_gui.elements.UIImage(scale(pygame.Rect((150, 175), (400, 540))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/victim_panel.png").convert_alpha(),
                                                                (569, 399)), manager=MANAGER)
            
            self.accomplice_frame = pygame_gui.elements.UIImage(scale(pygame.Rect((1050, 175), (400, 540))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/accomplice_panel.png").convert_alpha(),
                                                                (569, 399)), manager=MANAGER)
            self.your_sprite = pygame_gui.elements.UIImage(
                                            scale(pygame.Rect((650, 360), (300, 300))),
                                            pygame.transform.scale(
                                                self.the_cat.sprite,
                                                (300, 300)), manager=MANAGER)
            
            self.victim_sprite = pygame_gui.elements.UIImage(
                                            scale(pygame.Rect((210, 190), (270, 270))),
                                            pygame.transform.scale(
                                                self.cat_to_murder.sprite,
                                                (270, 270)), manager=MANAGER)
            
            info = self.cat_to_murder.status + "\n" + \
                   self.cat_to_murder.genderalign + "\n" + self.cat_to_murder.personality.trait + "\n"

            if self.cat_to_murder.moons < 1:
                info += "???"
            else:
                info += self.cat_to_murder.skills.skill_string(short=True)

            # vicinfo

            self.victim_info = pygame_gui.elements.UITextBox(info,scale(pygame.Rect((205, 475),(300, 250))),
                                                        object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
                                                        manager=MANAGER)
            
            name = str(self.cat_to_murder.name)  # get name

            if 17 <= len(name):  # check name length
                short_name = str(name)[0:15]
                name = short_name + '...'

            self.victim_name = pygame_gui.elements.ui_label.UILabel(
                scale(pygame.Rect((205, 472), (300, 60))),
                name,
                object_id="#text_box_34_horizcenter", manager=MANAGER)

            self.back_button = UIImageButton(scale(pygame.Rect((50, 1290), (204, 60))), "", object_id="#back_button")
            
            self.confirm_mentor = UIImageButton(scale(pygame.Rect((696, 688), (208, 52))), "",
                                                object_id="#continue_button_small")
        
            self.previous_page_button = UIImageButton(scale(pygame.Rect((630, 1229), (68, 68))), "",
                                                    object_id="#relation_list_previous", manager=MANAGER)
            self.next_page_button = UIImageButton(scale(pygame.Rect((902, 1229), (68, 68))), "",
                                                object_id="#relation_list_next", manager=MANAGER)
            
            self.next = UIImageButton(scale(pygame.Rect((942, 680), (68, 68))), "",
                                                tool_tip_text= "Proceed without an accomplice.",
                                                object_id="#arrow_right_button", manager=MANAGER)
            self.prev = UIImageButton(scale(pygame.Rect((590, 680), (68, 68))), "",
                                                object_id="#arrow_left_button", manager=MANAGER)
            
            self.previous_page_button.show()
            self.next_page_button.show()


            self.update_selected_cat2()  # Updates the image and details of selected cat
            # self.update_chance_text(accomplice=None)
            self.update_cat_list2()


    def exit_screen(self):

        for ele in self.cat_list_buttons:
            self.cat_list_buttons[ele].kill()
        self.cat_list_buttons = {}

        for ele in self.apprentice_details:
            self.apprentice_details[ele].kill()
        self.apprentice_details = {}

        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}
        
        if self.heading:
            self.heading.kill()
            del self.heading

        if self.subtitle:
            self.subtitle.kill()
            del self.subtitle 

        if self.mentor_frame:
            self.mentor_frame.kill()
            del self.mentor_frame

        if self.accomplice_frame:
            self.accomplice_frame.kill()
            del self.accomplice_frame

        if self.your_sprite:
            self.your_sprite.kill()
            del self.your_sprite

        if self.victim_sprite:
            self.victim_sprite.kill()
            del self.victim_sprite

        if self.victim_info:
            self.victim_info.kill()
            del self.victim_info

        if self.victim_name:
            self.victim_name.kill()
            del self.victim_name

        if self.methodinfo:
            self.methodinfo.kill()
            del self.methodinfo

        if self.locationinfo:
            self.locationinfo.kill()
            del self.locationinfo
        
        if self.timeinfo:
            self.timeinfo.kill()
            del self.timeinfo

        if self.methodheading:
            self.methodheading.kill()
            del self.methodheading

        if self.locationheading:
            self.locationheading.kill()
            del self.locationheading

        if self.timeheading:
            self.timeheading.kill()
            del self.timeheading
        
        if self.methodtext:
            self.methodtext.kill()
            del self.methodtext

        if self.locationtext:
            self.locationtext.kill()
            del self.locationtext
        
        if self.timetext:
            self.timetext.kill()
            del self.timetext
        
        if self.attackmethod:
            self.attackmethod.kill()
            del self.attackmethod

        if self.poisonmethod:
            self.poisonmethod.kill()
            del self.poisonmethod

        if self.accidentmethod:
            self.accidentmethod.kill()
            del self.accidentmethod

        if self.predatormethod:
            self.predatormethod.kill()
            del self.predatormethod

        if self.camplocation:
            self.camplocation.kill()
            del self.camplocation
        
        if self.territorylocation:
            self.territorylocation.kill()
            del self.territorylocation

        if self.borderlocation:
            self.borderlocation.kill()
            del self.borderlocation

        if self.dawntime:
            self.dawntime.kill()
            del self.dawntime
        
        if self.daytime:
            self.daytime.kill()
            del self.daytime

        if self.nighttime:
            self.nighttime.kill()
            del self.nighttime

        if self.back_button:
            self.back_button.kill()
            del self.back_button

        if self.chancetext:
            self.chancetext.kill()
            del self.chancetext

        if self.willingnesstext:
            self.willingnesstext.kill()
            del self.willingnesstext

        if self.confirm_mentor:
            self.confirm_mentor.kill()
            del self.confirm_mentor

        if self.randomiser_button:
            self.randomiser_button.kill()
            del self.randomiser_button

        if self.previous_page_button:
            self.previous_page_button.kill()
            del self.previous_page_button
            
        if self.next_page_button:
            self.next_page_button.kill()
            del self.next_page_button
        
        if self.next:
            self.next.kill()
            del self.next

        if self.prev:
            self.prev.kill()
            del self.prev

    def find_next_previous_cats(self):
        """Determines where the previous and next buttons lead"""
        is_instructor = False
        if self.the_cat.dead and game.clan.instructor.ID == self.the_cat.ID:
            is_instructor = True

        self.previous_cat = 0
        self.next_cat = 0
        if self.the_cat.dead and not is_instructor and not self.the_cat.df:
            self.previous_cat = game.clan.instructor.ID

        if is_instructor:
            self.next_cat = 1

        for check_cat in Cat.all_cats_list:
            if check_cat.ID == self.the_cat.ID:
                self.next_cat = 1

            if self.next_cat == 0 and check_cat.ID != self.the_cat.ID and check_cat.dead == self.the_cat.dead and \
                    check_cat.ID != game.clan.instructor.ID and not check_cat.exiled and check_cat.status in \
                    ["apprentice", "medicine cat apprentice", "mediator apprentice", "queen's apprentice"] \
                    and check_cat.df == self.the_cat.df:
                self.previous_cat = check_cat.ID

            elif self.next_cat == 1 and check_cat.ID != self.the_cat.ID and check_cat.dead == self.the_cat.dead and \
                    check_cat.ID != game.clan.instructor.ID and not check_cat.exiled and check_cat.status in \
                    ["apprentice", "medicine cat apprentice", "mediator apprentice", "queen's apprentice"] \
                    and check_cat.df == self.the_cat.df:
                self.next_cat = check_cat.ID

            elif int(self.next_cat) > 1:
                break

        if self.next_cat == 1:
            self.next_cat = 0

    def print_chances(self, cat_to_murder, accomplice):
        
        # not deleting the function bc chances will need more tweaking in the future

        if self.selected_cat:
            hypothetical_agree = False
            if accomplice:
                # prints chances when selecting accomplice
                successchance = self.get_kill(game.clan.your_cat, cat_to_murder, accomplice=accomplice, accompliced=False)
                risk_chance = self.get_risk_chance(cat_to_murder, accomplice=accomplice, accompliced=False)
                discover_chance = self.get_discover_chance(self.cat_to_murder, accomplice=accomplice, accompliced=False)
                death_chance = self.get_death_chance(cat_to_murder, accomplice=accomplice, accompliced=None)
                if cat_to_murder.status == "leader":
                    leader_death_chance = self.leader_death_chance(cat_to_murder, accomplice=accomplice, accompliced=False)

                hypothetical_agree = True

                hypsuccesschance = self.get_kill(game.clan.your_cat, cat_to_murder, accomplice=accomplice, accompliced=True)
                hyprisk_chance = self.get_risk_chance(cat_to_murder, accomplice=accomplice, accompliced=True)
                hypdiscover_chance = self.get_discover_chance(self.cat_to_murder, accomplice=accomplice, accompliced=True)
                hypdeath_chance = self.get_death_chance(cat_to_murder, accomplice=accomplice, accompliced=True)
                if cat_to_murder.status == "leader":
                    hypleader_death_chance = self.leader_death_chance(cat_to_murder, accomplice=accomplice, accompliced=None)

            else:
                # prints chances when selecting a victim
                successchance = self.get_kill(game.clan.your_cat, cat_to_murder, accomplice=None, accompliced=None)
                risk_chance = self.get_risk_chance(cat_to_murder, accomplice=None, accompliced=None)
                discover_chance = self.get_discover_chance(cat_to_murder, accomplice=accomplice, accompliced=None)
                death_chance = self.get_death_chance(cat_to_murder, accomplice=None, accompliced=None)
                if cat_to_murder.status == "leader":
                    leader_death_chance = self.leader_death_chance(cat_to_murder, accomplice=None, accompliced=None)

            if not accomplice:
                print("----------------------------")
                print(f"Victim: {cat_to_murder.name}")
                print("")
                print(F"Success Chance: {successchance}/100")
                print(F"Discovery Chance: {discover_chance}/100")
                print(F"MC Injury Chance: {risk_chance}/100")
                print(F"MC Death Chance: {death_chance}/100")

                if cat_to_murder.status == "leader":
                    print(F"LEADER ALL LIVES CHANCE: {leader_death_chance}/100")

            else:
                if hypothetical_agree:
                    print("----------------------------")
                    print(f"Victim: {cat_to_murder.name}")
                    print(f"Accomplice: {accomplice.name}")
                    print("IF ACCOMPLICE AGREES:")
                    print("")
                    print(F"Success Chance: {hypsuccesschance}/100")
                    print(F"Discovery Chance: {hypdiscover_chance}/100")
                    print(F"MC Injury Chance: {hyprisk_chance}/100")
                    print(F"MC Death Chance: {hypdeath_chance}/100")

                    if cat_to_murder.status == "leader":
                        print(F"LEADER ALL LIVES CHANCE: {hypleader_death_chance}/100")

                print("----------------------------")
                print("IF ACCOMPLICE REFUSES:")
                print("")
                print(F"Success Chance: {successchance}/100")
                print(F"Discovery Chance: {discover_chance}/100")
                print(F"MC Injury Chance: {risk_chance}/100")
                print(F"MC Death Chance: {death_chance}/100")

                if cat_to_murder.status == "leader":
                    print(F"LEADER ALL LIVES CHANCE: {leader_death_chance}/100")

            if cat_to_murder.status == "leader":
                print("Discovery chances will go up if the leader doesn't lose all of their lives.")

        


    def change_cat(self, new_mentor=None, accomplice=None, accompliced=None):
        self.exit_screen()
        r = randint(0,100)
        r2 = randint(-10, 10)

        chance = self.get_kill(game.clan.your_cat, self.cat_to_murder, accomplice, accompliced)
        risk_chance = self.get_risk_chance(self.cat_to_murder, accomplice=accomplice, accompliced=accompliced)
        discover_chance = self.get_discover_chance(self.cat_to_murder, accomplice=accomplice, accompliced=accompliced)

        if game.config["murder_chance"] != -1:
            try:
                chance = game.config["murder_chance"]
            except:
                pass
        murdered = r < max(5, chance + r2)
        you = game.clan.your_cat
        cat_to_murder = self.cat_to_murder
        game.clan.murdered = True
        if murdered:
            self.choose_murder_text(you, cat_to_murder, accomplice, accompliced)
        else:
            self.handle_murder_fail(you, cat_to_murder, accomplice, accompliced)
        self.selected_cat = None

        game.switches['cur_screen'] = "events screen"

        # reset cats
        self.selected_cat = None
        self.cat_to_murder = None
    
    RESOURCE_DIR = "resources/dicts/events/lifegen_events/"

    def get_death_chance(self, cat_to_murder, accomplice, accompliced):
        """ chance for mc to bite the dust """
        # x/100
        you = game.clan.your_cat
        chance = 0

        if self.method == "attack":
            chance += 5
        elif self.method == "poison":
            if you.status != "medicine cat":
                chance += 2
            elif you.status == "medicine cat apprentice":
                chance += 1 # since medicine cats are still in training
        elif self.method == "accident":
            chance += 8
        elif self.method == "predator":
            chance += 12

        if self.location == "camp":
            chance += 1
        elif self.location == "territory":
            chance += 5
        elif self.location == "border":
            chance += 10

        if self.time == "dawn":
            chance += 3
        elif self.time == "day":
            chance += 2
        elif self.time == "night":
            chance += 10

        if accomplice and accompliced:
            chance -= 5

        if cat_to_murder.moons > 12:
            chance += 2

        if cat_to_murder.moons < 6 or self.method == "poison":
            chance = math.floor(chance / 2)

        return chance

    def get_risk_chance(self, cat_to_murder, accomplice, accompliced):
        """calculates chance for mc to be injured in the murder. out of 100"""
        you = game.clan.your_cat
        chance = 0

        you_healthy = not you.is_ill() and not you.is_injured()

        cat_healthy = not cat_to_murder.is_ill() and not cat_to_murder.is_injured()

        your_skills = []
        if you.skills.primary:
            your_skills.append(you.skills.primary.skill)
        if you.skills.secondary:
                your_skills.append(you.skills.secondary.skill)

        their_skills = []
        if cat_to_murder.skills.primary:
            their_skills.append(cat_to_murder.skills.primary.skill)
        if cat_to_murder.skills.secondary:
            their_skills.append(cat_to_murder.skills.secondary.skill)

        # GENERAL
        if you.joined_df:
            chance -= 32
        if you.age != cat_to_murder.age and you.moons > cat_to_murder.moons:
            chance -= 16
        if cat_to_murder.age == "senior":
            chance -= 16
        if you.status == cat_to_murder.status:
            chance -= 16
        if you.experience > cat_to_murder.experience:
            chance -= 16
        if accomplice and accompliced:
            chance -= 24

        if self.location == "camp":
            chance -= 24
        
        if self.time == "day":
            chance -= 24

        if self.location == "border":
            chance += 22
        if self.time == "night":
            chance += 30

        if cat_to_murder.joined_df:
            chance += 32
        if cat_to_murder.moons >= you.moons + 4:
            chance += 16
        if not you_healthy:
            chance += 16
        
        if cat_to_murder.status == "leader":
            if game.clan.leader_lives > 1:
                chance += 40
            else:
                chance += 16

        if cat_to_murder.experience > you.experience:
            chance += 16

        victim_skills_lvl1 = ["watchful", "lives in groups", "interested in oddities", "fascinated by prophecies",
                              "plays with freshkill", "oddly quiet"
                              ]
        victim_skills_lvl2 = ["good guard", "good sport", "omen seeker", "prophecy seeker",
                              "morbid fascination", "feather-light paws"
                              ]
        victim_skills_lvl3 = ["great guard", "team player", "omen sense", "prophecy interpreter",
                              "blood lover", "masterful stepper"
                              ]
        victim_skills_lvl4 = ["guardian", "insider", "omen sight", "prophet",
                              "fascinated by gore", "unseen when sneaking"
                              ]

        if any(skill in victim_skills_lvl1 for skill in their_skills):
            chance -= 5
        if any(skill in victim_skills_lvl2 for skill in their_skills):
            chance -= 10
        if any(skill in victim_skills_lvl3 for skill in their_skills):
            chance -= 15
        if any(skill in victim_skills_lvl4 for skill in their_skills):
            chance -= 20

        if self.method == "attack":
            if you.joined_df:
                chance -= 35
            if ("steps lightly" or "mossball hunter" or "avid play-fighter") in your_skills:
                chance -= 3
            if ("graceful" or "good hunter" or "good fighter") in your_skills:
                chance -= 7
            if ("elegant" or "great hunter" or "formidable fighter") in your_skills:
                chance -= 11
            if ("radiates elegance" or "renowned hunter" or "unusually strong fighter") in your_skills:
                chance -= 15
            if you.status == "warrior" and you_healthy:
                chance -= 23
            if you.age != cat_to_murder.age and you.moons > cat_to_murder.moons:
                chance -= 16

            if self.location == "border":
                chance -= 8

            if you.personality.trait == "bloodthirsty":
                chance -= 16

            if cat_to_murder.status == "warrior" and cat_healthy:
                chance += 15
                
            if you.status == "kitten":
                chance += 20
            if you.status in [
                 "mediator apprentice", "medicine cat apprentice"
                ]:
                chance += 15
            elif you.status in [
                "mediator", "medicine cat", "queen's apprentice"
                ]:
                chance += 10
            elif you.status in [
                 "queen", "apprentice"
                 ]:
                chance += 5

            if "avid play-fighter" in their_skills:
                chance += 8
            if "good fighter" in their_skills:
                chance += 12
            if "formidable fighter" in their_skills:
                chance += 18
            if "unusually strong fighter" in their_skills:
                chance += 25

            if self.location == "camp":
                chance += 8
            if cat_to_murder.personality.trait == "bloodthirsty":
                chance += 16

        if self.method == "accident":
            acc_skills_lvl_1 = ["curious wanderer", "good with directions", "constantly climbing"]
            acc_skills_lvl_2 = ["knowledgeable explorer", "good navigator", "good climber"]
            acc_skills_lvl_3 = ["brave pathfinder", "great navigator", "great climber"]
            acc_skills_lvl_4 = ["master of territories", "pathfinder", "impressive climber"]

            if any(skill in acc_skills_lvl_1 for skill in your_skills):
                chance -= 5
            if any(skill in acc_skills_lvl_2 for skill in your_skills):
                chance -= 10
            if any(skill in acc_skills_lvl_3 for skill in your_skills):
                chance -= 15
            if any(skill in acc_skills_lvl_4 for skill in your_skills):
                chance -= 20

            if self.location == "camp":
                chance -= 15

            if game.clan.biome == "Mountainous":
                chance += 10
            if cat_to_murder.status in ["warrior", "deputy", "leader"] and cat_healthy:
                chance += 11

        if self.method == "predator":

            pred_skills_lvl_1 = ["other-cat-ly whisperer", "mossball hunter"]
            pred_skills_lvl_2 = ["dog-whisperer", "good hunter"]
            pred_skills_lvl_3 = ["multilingual", "great hunter"]
            pred_skills_lvl_4 = ["listener of all voices", "renowned hunter"]

            if any(skill in pred_skills_lvl_1 for skill in your_skills):
                chance += 5
            if any(skill in pred_skills_lvl_2 for skill in your_skills):
                chance += 10
            if any(skill in pred_skills_lvl_3 for skill in your_skills):
                chance += 15
            if any(skill in pred_skills_lvl_4 for skill in your_skills):
                chance += 20

            if self.location == "camp":
                chance -= 35

            if cat_to_murder.status in ["warrior", "deputy", "leader"] and cat_healthy:
                chance += 10
            if you.status in ["queen", "mediator", "kitten", "medicine cat", "queen's apprentice", "mediator apprentice", "medicine cat apprentice"]:
                chance += 15

            if "avid play-fighter" in their_skills:
                chance += 8
            if "good fighter" in their_skills:
                chance += 12
            if "formidable fighter" in their_skills:
                chance += 18
            if "unusually strong fighter" in their_skills:
                chance += 25

        if chance >= 95:
            chance = 95
        elif chance <= 5:
            chance = 5

        # lowest possible risk chance for predator is 25, meaning a 1/4 chance, no matter how many other positive factors they have.
        if chance < 25 and self.method == "predator":
            chance = 25

        return chance
    

    def choose_murder_text(self, you, cat_to_murder, accomplice, accompliced):
        """chooses murder text. nuff said also chooses whether the mc is injured or dies"""

        with open(f"{self.RESOURCE_DIR}murder.json",
                encoding="ascii") as read_file:
            self.m_txt = ujson.loads(read_file.read())
        with open(f"{self.RESOURCE_DIR}murder_unsuccessful.json",
                encoding="ascii") as read_file:
            self.mu_txt = ujson.loads(read_file.read())

        leaddeath = randint(1,100)
       
        leader_death_chance = self.leader_death_chance(cat_to_murder,accomplice=accomplice, accompliced=accompliced)

        all_leader_lives = False

        if cat_to_murder.status == "leader":
            if leaddeath < leader_death_chance + 1:
                all_leader_lives = True


        risk = randint(1,100)
        risk_chance = self.get_risk_chance(cat_to_murder, accomplice=accomplice, accompliced=accompliced)

        deathrisk = randint(1,100)
        death_chance = self.get_death_chance(cat_to_murder, accomplice=accomplice, accompliced=accompliced)

        injury = False
        death = False

        if risk < risk_chance + 1:
            injury = True

        if deathrisk < death_chance + 1 and not injury:
            death = True
        
        if death and not injury:
            if you.status == "leader":
                game.clan.leader_lives -= 1
            you.die()
            

        if injury and not death:
            if self.method == "attack":
                owie = choice(["claw-wound", "bite-wound", "torn pelt", "sprain", "sore", "bruises", "scrapes"])
                owie2 = owie = choice(["claw-wound", "bite-wound", "torn pelt", "sprain", "sore", "bruises", "scrapes"])
                # two of em so accomplice and mc dont always get the same injury
            elif self.method == "poison":
                owie = "poisoned"
                owie2 = "poisoned"
            elif self.method == "accident":
                owie = choice(["broken bone","broken bone","broken bone","sprain", "sore", "bruises", "scrapes",
                               "paralyzed", "head damage", "broken jaw"])
                owie2 = choice(["broken bone","broken bone","broken bone","sprain", "sore", "bruises", "scrapes",
                                "paralyzed", "head damage", "broken jaw"])
            elif self.method == "predator":
                owie = choice(["bite-wound", "broken bone", "torn pelt", "mangled leg", "mangled tail"])
                owie2 = choice(["bite-wound", "broken bone", "torn pelt", "mangled leg", "mangled tail"])

            if accomplice and accompliced:
                # accomplice means you have one, accompliced means they agreed
                if randint(1,4) == 1:
                    accomplice.get_injured(owie2)

            # you.get_injured(owie)
        
        # CHOOSING TEXT
        biome = game.clan.biome.lower()
        camp = game.clan.camp_bg

        ceremony_txt = []
        possible_keys = []

        murder_events = {}

        methods = ["attack", "poison", "accident", "predator"]

        locations = ["camp", "territory", "border"]

        times = ["day", "night", "dawn"]

        camps = ["camp1", "camp2", "camp3", "camp4", "camp5", "camp6"]


        trueaccident = False
        discovered = False # this has been moved up so some tags can force a discovery (such as the kitten killing leader event).
        
        for i in self.m_txt.items():
            key = i[0]
            murder_dict = i[1]

            if "your_status" in murder_dict:
                if "adult" in murder_dict["your_status"]:
                    if you.moons < 12:
                        continue

                elif "no_kit" in murder_dict["your_status"]:
                    if you.moons < 6:
                        continue

                elif "all_apprentices" in murder_dict["your_status"]:
                    if you.moons > 12 or you.moons < 6:
                        continue

                elif "healer_cat" in murder_dict["your_status"]:
                    if you.status not in ["medicine cat", "medicine cat apprentice"]:
                        continue
                
                elif you.status not in murder_dict["your_status"]:
                    if "any" not in murder_dict["your_status"]:
                        continue

            if "victim_status" in murder_dict:
                if "adult" in murder_dict["victim_status"]:
                    if cat_to_murder.moons < 12:
                        continue

                elif "no_kit" in murder_dict["victim_status"]:
                    if cat_to_murder.moons < 6:
                        continue

                elif "all_apprentices" in murder_dict["victim_status"]:
                    if cat_to_murder.moons > 12 or cat_to_murder.moons < 6:
                        continue

                elif "healer_cat" in murder_dict["victim_status"]:
                    if cat_to_murder.status not in ["medicine cat", "medicine cat apprentice"]:
                        continue
                
                elif cat_to_murder.status not in murder_dict["victim_status"]:
                    if "any" not in murder_dict["victim_status"]:
                        continue

            if "relationship" in murder_dict and murder_dict["relationship"]:

                if "specific-values" in murder_dict["relationship"]:
                    # relationship values to determine the player characters relationship to the victim.
                    # lots of them so theres lots of room for nuance.
                    # none should be mutually exclusive outside of love vs like / light vs extreme values.
                    # this allows for things such as toxic crushes.
                    # all uses of it HAVE to have the "specific-values" tag in "relationship"
                    values = ["romantic","platonic","dislike","admiration","comfortable","jealousy","trust","toxicity"]
                    for val in values:
                        player_value_check = check_relationship_value(you, cat_to_murder, val)
                        victim_value_check = check_relationship_value(cat_to_murder, you, val)

                        if val == "platonic":
                            if ("player_platonic_love_victim" in murder_dict["relationship"] and not
                                player_value_check >= 50): # threshold for high emotions is 50.
                                continue
                            elif ("player_platonic_like_victim" in murder_dict["relationship"] and not
                                player_value_check >= 20):
                                continue

                            if ("victim_platonic_love_player" in murder_dict["relationship"] and not
                                victim_value_check >= 50):
                                continue
                            elif ("victim_platonic_like_player" in murder_dict["relationship"] and not
                                victim_value_check >= 20):
                                continue

                        if val == "romantic":
                            # and whats more romantic than murder truly
                            if ("player_romantic_love_victim" in murder_dict["relationship"] and not
                                player_value_check >= 50):
                                continue
                            elif ("player_romantic_like_victim" in murder_dict["relationship"] and not
                                player_value_check >= 20):
                                continue
                            
                            if ("victim_romantic_love_player" in murder_dict["relationship"] and not
                                victim_value_check >= 50):
                                continue
                            elif ("victim_romantic_like_player" in murder_dict["relationship"] and not
                                victim_value_check >= 20):
                                continue

                        if val == "dislike":
                            if ("player_hate_victim" in murder_dict["relationship"] and not
                                player_value_check >= 50):
                                continue
                            elif ("player_dislike_victim" in murder_dict["relationship"] and not
                                player_value_check >= 20):
                                continue
                            
                            if ("victim_hate_player" in murder_dict["relationship"] and not
                                victim_value_check >= 50):
                                continue
                            elif ("victim_dislike_player" in murder_dict["relationship"] and not
                                victim_value_check >= 20):
                                continue

                        if val == "admiration":
                            if ("player_high_admire_victim" in murder_dict["relationship"] and not
                                player_value_check >= 50):
                                continue
                            elif ("player_low_admire_victim" in murder_dict["relationship"] and not
                                player_value_check >= 20):
                                continue
                            
                            if ("victim_high_admire_player" in murder_dict["relationship"] and not
                                victim_value_check >= 50):
                                continue
                            elif ("victim_low_admire_player" in murder_dict["relationship"] and not
                                victim_value_check >= 20):
                                continue

                        if val == "jealousy":
                            if ("player_envy_victim" in murder_dict["relationship"] and not
                                player_value_check >= 50):
                                continue
                            elif ("player_jealous_victim" in murder_dict["relationship"] and not
                                player_value_check >= 20):
                                continue
                            
                            if ("victim_envy_player" in murder_dict["relationship"] and not
                                victim_value_check >= 50):
                                continue
                            elif ("victim_jealous_player" in murder_dict["relationship"] and not
                                victim_value_check >= 20):
                                continue

                        if val == "trust":
                            if ("player_high_trust_victim" in murder_dict["relationship"] and not
                                player_value_check >= 50):
                                continue
                            elif ("player_low_trust_victim" in murder_dict["relationship"] and not
                                player_value_check >= 20):
                                continue
                            
                            if ("victim_high_trust_player" in murder_dict["relationship"] and not
                                victim_value_check >= 50):
                                continue
                            elif ("victim_low_trust_player" in murder_dict["relationship"] and not
                                victim_value_check >= 20):
                                continue

                        if val == "respect":
                            if ("player_high_respect_victim" in murder_dict["relationship"] and not
                                player_value_check >= 50):
                                continue
                            elif ("player_low_respect_victim" in murder_dict["relationship"] and not
                                player_value_check >= 20):
                                continue
                            
                            if ("victim_high_respect_player" in murder_dict["relationship"] and not
                                victim_value_check >= 50):
                                continue
                            elif ("victim_low_respect_player" in murder_dict["relationship"] and not
                                victim_value_check >= 20):
                                continue

                        if val == "toxicity":
                            # toxicity check. remember to use the toxic tag as well.
                            if ("player_toxic_to_victim" in murder_dict["relationship"] and not
                                player_value_check >= 50):
                                continue
                            elif ("player_bad_for_victim" in murder_dict["relationship"] and not
                                player_value_check >= 20):
                                continue
                            
                            if ("victim_toxic_to_player" in murder_dict["relationship"] and not
                                victim_value_check >= 50):
                                continue
                            elif ("victim_bad_for_player" in murder_dict["relationship"] and not
                                victim_value_check >= 20):
                                continue
                        
                
                if "mates" in murder_dict["relationship"]:
                    if cat_to_murder not in you.mates:
                        continue
                if "siblings" in murder_dict["relationship"]:
                    if cat_to_murder.ID not in you.inheritance.get_siblings():
                        continue

                if "your_parent" in murder_dict["relationship"]:
                    if you.parent1:
                        if cat_to_murder.ID != you.parent1:
                            continue
                    if you.parent2:
                        if cat_to_murder.ID != you.parent2:
                            continue
                    if cat_to_murder.ID not in you.inheritance.get_adoptive_parents():
                        continue

                if "your_kit" in murder_dict["relationship"]:
                    if (
                        cat_to_murder.ID not in you.inheritance.get_blood_kits() and
                        cat_to_murder.ID not in you.inheritance.get_not_blood_kits()
                        ):
                        continue

                if "your_apprentice" in murder_dict["relationship"]:
                    if cat_to_murder.mentor != game.clan.your_cat.ID:
                        continue
                
                if "your_mentor" in murder_dict["relationship"]:
                    if game.clan.your_cat.mentor != cat_to_murder.ID:
                        continue

                        

            if "biome" in murder_dict and murder_dict["biome"]:
                if biome and biome not in murder_dict["biome"]:
                    continue
                if any(i in tags for i in camps) and camp not in murder_dict["biome"]:
                    continue

            if "strategy" in murder_dict and murder_dict["strategy"]:
                tags = [i for i in murder_dict["strategy"]]

                if any(i in tags for i in methods) and self.method not in murder_dict["strategy"]:
                    continue
                if any(i in tags for i in locations) and self.location not in murder_dict["strategy"]:
                    continue
                if any(i in tags for i in times) and self.time not in murder_dict["strategy"]:
                    continue

            # tags!
            # this includes all_lives, accomplice tags, and injury/death tags.
            # perhaps skills and clusters in the future.

            if "tags" in murder_dict and murder_dict["tags"]:
                if (
                    (all_leader_lives and cat_to_murder.status == "leader")
                    or (not all_leader_lives and cat_to_murder.status == "leader"and game.clan.leader_lives == 1)
                    ):
                    if "all_lives" not in murder_dict["tags"]:
                        continue
                else:
                    if "all_lives" in murder_dict["tags"]:
                        continue

                if injury:
                    if "injury" not in murder_dict["tags"]:
                        continue
                elif death:
                    if "death" not in murder_dict["tags"]:
                        continue

                if not injury and not death:
                    if "injury" in murder_dict["tags"]:
                        continue
                    if "death" in murder_dict["tags"]:
                        continue

                if accomplice and accompliced: # accomplice agreed
                    if "alone" in murder_dict["tags"]:
                        continue
                    if "accomplice_refused" in murder_dict["tags"]:
                        continue
                elif accomplice: # acc refused
                    if "alone" in murder_dict["tags"]:
                        continue
                    if "accomplice_agreed" in murder_dict["tags"]:
                        continue
                elif not accomplice and not accompliced:
                    if "accomplice_refused" in murder_dict["tags"]:
                        continue
                    if "accomplice_agreed" in murder_dict["tags"]:
                        continue
                
                # NEONPINK TAGS -------------------------------------------------------------------------
                # roles exist
                if "medcats_in_clan" in murder_dict["tags"] and not get_alive_status_cats(Cat, [
                      "medicine cat apprentice", "medicine cat"
                      ], includePlayer=False):
                    continue
                if "leader_in_clan" in murder_dict["tags"] and not get_alive_status_cats(Cat, [
                      "leader"
                      ], includePlayer=False):
                    continue
                if "kit_in_clan" in murder_dict["tags"] and not get_alive_status_cats(Cat, [
                      "kitten"
                      ], includePlayer=False):
                    continue

                # seasons
                if "leaf-bare" in murder_dict["tags"] and not str(game.clan.current_season) == "Leaf-bare":
                    # if the current season string isnt "Leaf-bare", basically.
                    continue
                if "leaf-fall" in murder_dict["tags"] and not str(game.clan.current_season) == "Leaf-fall":
                    continue
                if "greenleaf" in murder_dict["tags"] and not str(game.clan.current_season) == "Greenleaf":
                    continue
                if "newleaf" in murder_dict["tags"] and not str(game.clan.current_season) == "Newleaf":
                    continue

                # game settings
                if "toxic" in murder_dict["tags"] and not game.settings.get("toxic relationships"):
                    # prevent toxic murders from appearing if the toxic relationships setting is off.
                    continue
                if "gore" in murder_dict["tags"] and not game.settings.get("gore"):
                    # just in case! for especially descriptive murders
                    continue

                # these tags actively do things. right here. bam
                if "guilt" in murder_dict["tags"]:
                    # force-gives guilt, regardless of / in addition to other injuries
                    you.get_injured("guilt")
                if "true_accident" in murder_dict["tags"]:
                    # to prevent shunning if something was an actual, legitimate accident.
                    # not to be used for EVERY genuine accident- only for some
                    # (such as the apprentice friends attacked by dogs event).
                    # THIS SHOULD BE RARE, AS IT WAS STILL THE PLAYER'S CHOICE.
                    trueaccident = True
                if "always_discovered" in murder_dict["tags"]:
                    discovered = True
                

            elif "tags" in murder_dict and not murder_dict["tags"]:
                # injury and death outcomes cannot get events with empty tags
                if injury:
                    continue
                if death:
                    continue

            possible_keys.append(key)
            
            murder_events.update({key: murder_dict})

        print("POSSIBLE KEYS:", possible_keys)

        options = []
        for i in murder_events.items():
            options.append(i)

        chosen_event = choice(options)

        if "texts" in chosen_event[1]:
            if chosen_event[1]["texts"]:
                for event in chosen_event[1]["texts"]:
                    ceremony_txt.append(event)
            else:
                print("Blank murder text for", chosen_event[0])
                return
            
        if injury:
            if "tags" in chosen_event[1] and chosen_event[1]["tags"]:
                if injury:
                    for t in chosen_event[1]["tags"]:
                        if any(t in chosen_event[1] for t in INJURIES):
                            if t in INJURIES:
                                you.get_injured(t)
                        else:
                            you.get_injured(owie)

        ceremony_txt = choice(ceremony_txt)



        other_clan = choice(game.clan.all_clans)
        ceremony_txt = ceremony_txt.replace('c_n', game.clan.name)
        ceremony_txt = ceremony_txt.replace("o_c", str(other_clan.name))
    
        medcats = []
        for cat in Cat.all_cats_list:
            if "medicine cat" in cat.status and not cat.dead and not cat.outside and cat.status != you.status:
                medcats.append(cat)

        kits = []
        for cat in Cat.all_cats_list:
            if cat.status == "kitten" and not cat.dead and not cat.outside and cat.status != you.status:
                kits.append(cat)

        warriors = []
        for cat in Cat.all_cats_list:
            if cat.status == "warrior" and not cat.dead and not cat.outside and cat.status != you.status:
                medcats.append(cat)

        if len(medcats) > 0:
            random_medcat = choice(medcats)
            random_medcat_prns = choice(random_medcat.pronouns)
        elif len(warriors) > 0:
            random_medcat = choice(warriors)
            random_medcat_prns = choice(random_medcat.pronouns)
        elif game.clan.leader and game.clan.leader.ID != you.ID:
            random_medcat = game.clan.leader
            random_medcat_prns = choice(game.clan.leader.pronouns)
        else:
            random_medcat = self.cat_to_murder
            random_medcat_prns = choice(self.cat_to_murder.pronouns)
            # just trying to avoid errors if theres no medcats or anyone else in the clan lol.
            # for that one event that mentions a medcat


        # NEONPINK: get random kit!
        if len(kits) > 0:
            random_kit = choice(kits)
            random_kit_prns = choice(kits.pronouns)
        else:
            random_kit = self.cat_to_murder
            random_kit_prns = choice(self.cat_to_murder.pronouns)

        replace_dict = {
            "v_c": (str(self.cat_to_murder.name), choice(self.cat_to_murder.pronouns)),
            "l_n": (str(game.clan.leader.name), choice(game.clan.leader.pronouns)),
            "y_c": (str(game.clan.your_cat.name), choice(game.clan.your_cat.pronouns)),
            "r_m": (str(random_medcat.name), random_medcat_prns),
            "r_k":(str(random_kit.name), random_kit_prns)
        }

        if accomplice:
            replace_dict.update({"a_n": (str(accomplice.name), choice(accomplice.pronouns))})

        ceremony_txt = process_text(ceremony_txt, replace_dict)

        if cat_to_murder.status == 'leader' and all_leader_lives:
            game.clan.leader_lives = 0
        
        game.cur_events_list.insert(0, Single_Event(ceremony_txt))

        discover_chance = self.get_discover_chance(cat_to_murder, accomplice, accompliced)
        discovery_num = randint(1,10)

        if not all_leader_lives:
            game.clan.leader_lives -= 1
            if discover_chance < 7:
                discover_chance = randint(7,9)
        # if u kill the leader n they wake up like an hour later Yeah ur probably gonna get caught
        cat_to_murder.die()
        # discover_chance = 3
        # discovery_num = 1
        # ^^ shun debug

        if (discovery_num < (discover_chance + 1)) and not trueaccident:
            discovered = True
        else:
            discovered = False
            
        if discovered:
            if accomplice and accompliced:
                if game.clan.your_cat.dead:
                    game.cur_events_list.insert(1, Single_Event(
                        "You and " + str(accomplice.name) + " murdered " + str(cat_to_murder.name) +
                        ", but only your accomplice made it out alive."))
                else:
                    game.cur_events_list.insert(1, Single_Event(
                            "You successfully murdered "+ str(cat_to_murder.name) + " with the help of " +
                            str(accomplice.name) + "."))
                History.add_death(
                    cat_to_murder, f"{you.name} and {accomplice.name} murdered this cat.")
                History.add_murders(
                    cat_to_murder, accomplice, True, f"{you.name} murdered this cat along with {accomplice.name}.")
                History.add_murders(
                    cat_to_murder, you, True, f"{you.name} murdered this cat with the help of {accomplice.name}.")
                
                accguiltchance = randint(1,2)
                if accguiltchance == 1:
                    accomplice.get_injured("guilt")

                youguiltchance = randint(1,4)
                if youguiltchance == 1:
                    accomplice.get_injured("guilt")

            else:
                if game.clan.your_cat.dead:
                    game.cur_events_list.insert(1, Single_Event("You successfully murdered "+ str(cat_to_murder.name) + " at the cost of your own life."))
                else:
                    game.cur_events_list.insert(1, Single_Event("You successfully murdered "+ str(cat_to_murder.name) + "."))
                History.add_death(cat_to_murder, f"{you.name} murdered this cat.")
                History.add_murders(cat_to_murder, you, True, f"{you.name} murdered this cat.")
            self.choose_discover_punishment(you, cat_to_murder, accomplice, accompliced)
        else:
            if accomplice:
                if accompliced:
                    History.add_death(
                        cat_to_murder, f"{you.name} and {accomplice.name} murdered this cat.")
                    History.add_murders(
                        cat_to_murder, you, True, f"{you.name} murdered this cat along with {accomplice.name}.")
                    History.add_murders(
                        cat_to_murder, accomplice, True, f"{you.name} murdered this cat along with {accomplice.name}.")
                    
                    if game.clan.your_cat.dead:
                        game.cur_events_list.insert(1, Single_Event(
                            "You and " + str(accomplice.name) + " successfully murdered " + str(self.cat_to_murder.name) + 
                            " at the cost of your own life. It seems that no cat knows the truth."))
                    else:
                        game.cur_events_list.insert(1, Single_Event(
                            "You successfully murdered "+ str(cat_to_murder.name) + " along with " + str(accomplice.name) + 
                            ". It seems no one is aware of your actions."))

                    if game.clan.your_cat.dead:
                        accomplice.get_injured("guilt")
                    else:
                        accguiltchance = randint(1,4)
                        if accguiltchance == 1:
                            accomplice.get_injured("guilt")

                        youguiltchance = randint(1,6)
                        if youguiltchance == 1:
                            accomplice.get_injured("guilt")

                else:
                    History.add_death(cat_to_murder, f"{you.name} murdered this cat.")
                    History.add_murders(cat_to_murder, you, True, f"{you.name} murdered this cat.")
                    
                    if game.clan.your_cat.dead:
                        game.cur_events_list.insert(1, Single_Event(
                            "You successfully murdered "+ str(cat_to_murder.name) + 
                            " at the cost of your own life. " + str(accomplice.name) + 
                            " chose not to help. It seems that no other cat knows the truth."))
                    else:
                        game.cur_events_list.insert(1, Single_Event(
                            "You successfully murdered "+ str(cat_to_murder.name) + " but " + str(accomplice.name) + 
                            " chose not to help. It seems no one is aware of your actions."))
            else:
                History.add_death(cat_to_murder, f"{you.name} murdered this cat.")
                History.add_murders(cat_to_murder, you, True, f"{you.name} murdered this cat.")
                
                if game.clan.your_cat.dead:
                    game.cur_events_list.insert(1, Single_Event(
                        "You successfully murdered "+ str(cat_to_murder.name) + 
                        " at the cost of your own life. It seems that no cat knows the truth."))
                else:
                    game.cur_events_list.insert(1, Single_Event(
                        "You successfully murdered "+ str(cat_to_murder.name) + 
                        ". It seems no one is aware of your actions."))

        self.stage = "choose murder cat"
        
          
    def choose_discover_punishment(self, you, cat_to_murder, accomplice, accompliced):
        """determines punishment text, shunned and guilt outcomes"""
        # 1 = you punished, 2 = accomplice punished, 3 = both punished
        if game.clan.your_cat.dead:
            if randint (1,2) == 1:
                punishment_chance = 2
            else:
                return
        else:
            punishment_chance = randint(1,3)

        if not accomplice or not accompliced:
            punishment_chance = 1
        if punishment_chance == 1:
            if accomplice and not accompliced:
                a_s = randint(1,2)
                if (a_s == 1): # if the accomplice decides to tattle on the player
                    randomstring = randint(0,4)
                    if (randomstring == 0 and accomplice.status != "leader" and
                    get_alive_status_cats(Cat, ["leader"], includePlayer=False)
                    # makes sure there IS a leader to report to, because otherwise that's awkward.
                    ):
                        game.cur_events_list.insert(2, Single_Event(
                        f"Shocked at your request to be an accomplice to murder, " +
                        "{accomplice.name} reports your actions to " + (str(game.clan.leader.name)) + ".")
                        # using the leader's name makes it a tad more personal. teehee!
                        )
                    elif randomstring == 0: # but no leader!
                        game.cur_events_list.insert(2, Single_Event(
                        f"Stunned by your request to be an accomplice to murder, " +
                        "{accomplice.name} reports your actions to the rest of the clan.")
                        )
                    elif randomstring == 1:
                        game.cur_events_list.insert(2, Single_Event(
                        f"When you suggested {accomplice.name} help you," + # PRONOUNS PLEASSSSSE...............
                        " {accomplice.name} seemed " +
                        "on board... until later, when you learned {accomplice.name} talked about you " +
                        "behind your back. Now the whole clan knows what you've done.")
                        )
                    elif randomstring == 2:
                        game.cur_events_list.insert(2, Single_Event(
                        f"{accomplice.name} ran around camp, yowling what you did to everyone who'd hear.")
                        )
                    else:
                        game.cur_events_list.insert(2, Single_Event(
                        f"That rotten {accomplice.name} not only turned you down, but told others what" +
                        " you had decided to do. It seems trusting them was a mistake.")
                        )
                # if you dont die, youre shunned now. sucks to suck
                # this should be changed in the future- killing abusers should not get you shunned. :3
                if not you.dead:
                    you.shunned = 1

            txt = ""
            if game.clan.your_cat.dead:
                # if game.clan.your_cat.status in ['kitten', 'leader', 'deputy', 'medicine cat']:
                #     txt = choice(self.mu_txt["murder_discovered dead " + game.clan.your_cat.status])
                # else:
                #     txt = choice(self.mu_txt["murder_discovered dead general"])
                txt = choice(self.mu_txt["murder_discovered dead general"])
            else:
                if game.clan.your_cat.status in ['kitten', 'leader', 'deputy', 'medicine cat']:
                    txt = choice(self.mu_txt["murder_discovered " + game.clan.your_cat.status])
                else:
                    txt = choice(self.mu_txt["murder_discovered general"])
            txt = txt.replace('v_c', str(cat_to_murder.name))
            game.cur_events_list.insert(2, Single_Event(txt))

            if not you.dead:
                you.shunned = 1
            you.faith -= 0.5

        elif punishment_chance == 2:
            if game.clan.your_cat.dead:
                txt = f"After your and v_c's deaths, {accomplice.name} is blamed for both of them."

            else:
                txt = f"{accomplice.name} is blamed for the murder of v_c. However, you were not caught."
            txt = txt.replace('v_c', str(cat_to_murder.name))
            game.cur_events_list.insert(2, Single_Event(txt))
            if not accomplice.dead:
                accomplice.shunned = 1
            accomplice.faith -= 0.5

        else:
            txt = (f"The unsettling truth of v_c's death is discovered, with you and {accomplice.name} responsible." +
                   "The Clan decides both of your punishments.")
            txt = txt.replace('v_c', str(cat_to_murder.name))
            game.cur_events_list.insert(2, Single_Event(txt))
            if not you.dead:
                you.shunned = 1
            if not accomplice.dead:
                accomplice.shunned = 1
            accomplice.faith -= 0.5
        
        if punishment_chance == 1 or punishment_chance == 3:
            kit_punishment = ["You are assigned counseling by the Clan's medicine cat to help you understand the severity of your actions and to guide you to make better decisions in the future.",
                                "You are to be kept in the nursery under the watchful eye of the queens at all times until you become an apprentice."]
            gen_punishment = ["You are assigned counseling by the Clan's medicine cat to help you understand the severity of your actions and to guide you to make better decisions in the future.",
                                "You will be required to take meals last and are forced to sleep in a separate den away from your clanmates.",
                                "You are assigned to several moons of tasks that include cleaning out nests, checking elders for ticks, and other chores alongside your normal duties.",
                                "You are assigned a mentor who will better educate you about the Warrior Code and the sacredness of life."]
            # demote_leader = ["Your lives will be stripped away and you will be demoted to a warrior, no longer trusted to be the Clan's leader."]
            # demote_deputy = ["The Clan decides that you will be demoted to a warrior, no longer trusting you as their deputy."]
            # demote_medicine_cat = ["The Clan decides that you will be demoted to a warrior, no longer trusting you as their medicine cat."]
            # exiled = ["The Clan decides that they no longer feel safe with you as a Clanmate. You will be exiled from the Clan."]
            
            if you.status == 'kitten' or you.status == 'newborn':
                game.cur_events_list.insert(3, Single_Event(choice(kit_punishment)))
            elif you.status == 'leader':
                lead_choice = randint(1,3)
                if lead_choice == 1:
                    game.cur_events_list.insert(3, Single_Event(choice(gen_punishment)))
            elif you.status == 'deputy':
                lead_choice = randint(1,3)
                if lead_choice == 1:
                    game.cur_events_list.insert(3, Single_Event(choice(gen_punishment)))
            elif you.status == 'medicine cat':
                lead_choice = randint(1,3)
                if lead_choice == 1:
                    game.cur_events_list.insert(3, Single_Event(choice(gen_punishment)))
            else:
                lead_choice = randint(1,5)
                if lead_choice in [1, 2, 3, 4]:
                    game.cur_events_list.insert(3, Single_Event(choice(gen_punishment)))
        
        if accomplice and accompliced and (punishment_chance == 2 or punishment_chance == 3):
            a_n = str(accomplice.name)
            kit_punishment = [f"{a_n} is assigned counseling by the Clan's medicine cat to help them understand the severity of their actions and to guide them to make better decisions in the future.",
                            f"{a_n} is to be kept in the nursery under the watchful eye of the queens at all times until they become an apprentice."]
            gen_punishment = [f"{a_n} is assigned counseling by the Clan's medicine cat to help them understand the severity of their actions and to guide them to make better decisions in the future.",
                                f"{a_n} is required to take meals last and is forced to sleep in a separate den away from their clanmates.",
                                f"{a_n} is assigned to several moons of tasks that include cleaning out nests, checking elders for ticks, and other chores alongside their normal duties.",
                                f"{a_n} is assigned a mentor who will better educate them about the Warrior Code and the sacredness of life."]
            
            # demote_leader = [f"{a_n}'s lives will be stripped away and they will be demoted to a warrior, no longer trusted to be the Clan's leader."]
            # demote_deputy = [f"The Clan decides that {a_n} will be demoted to a warrior, no longer trusting them as their deputy."]
            # demote_medicine_cat = [f"The Clan decides that {a_n} will be demoted to a warrior, no longer trusting them as their medicine cat."]
            # exiled = [f"The Clan decides that they no longer feel safe with {a_n} as a Clanmate. They will be exiled from the Clan."]

            if accomplice.status == 'kitten' or accomplice.status == 'newborn':
                game.cur_events_list.insert(3, Single_Event(self.adjust_txt(choice(kit_punishment), accomplice, cat_to_murder)))
            elif accomplice.status == 'leader':
                lead_choice = randint(1,3)
                if lead_choice == 1:
                    game.cur_events_list.insert(3, Single_Event(self.adjust_txt(choice(gen_punishment), accomplice, cat_to_murder)))
                
            elif accomplice.status == 'deputy':
                lead_choice = randint(1,3)
                if lead_choice == 1:
                    game.cur_events_list.insert(3, Single_Event(self.adjust_txt(choice(gen_punishment), accomplice, cat_to_murder)))
               
            elif accomplice.status == 'medicine cat':
                lead_choice = randint(1,3)
                if lead_choice == 1:
                    game.cur_events_list.insert(3, Single_Event(self.adjust_txt(choice(gen_punishment), accomplice, cat_to_murder)))
                
            else:
                lead_choice = randint(1,5)
                if lead_choice in [1, 2, 3, 4]:
                    game.cur_events_list.insert(3, Single_Event(self.adjust_txt(choice(gen_punishment), accomplice, cat_to_murder)))

    def adjust_txt(self, text, accomplice, victim):
        process_text_dict = {}
        process_text_dict["a_n"] = accomplice
        process_text_dict["v_c"] = victim
        for abbrev in process_text_dict.keys():
            abbrev_cat = process_text_dict[abbrev]
            process_text_dict[abbrev] = (abbrev_cat, choice(abbrev_cat.pronouns))
        text = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), text)
        text = text.replace("a_n", str(accomplice.name))
        text = text.replace("v_c", str(victim.name))
        return text

    def leader_death_chance(self, cat_to_murder, accomplice, accompliced):
        """calculates chance for leader to lose all of their lives if the murder succeeds. out of 100"""
        chance = 50
        if cat_to_murder.status != "leader":
            return
        
        if game.clan.leader_lives == 1:
            chance = 100
        else:
            add = int(game.clan.leader_lives) * 5
            chance -= add

        if cat_to_murder.is_ill() or cat_to_murder.is_injured():
            chance += 8

        if accomplice and accompliced:
            chance += chance * math.floor(1/3)

        return chance
        
    
    def get_discover_chance(self, cat_to_murder, accomplice, accompliced):
        """calculates chance for murder discovery out of 100"""
        chance = 20
        # location chances
        if self.location == "camp":
            chance += 10
            if self.method == "attack":
                chance += 10

            if self.method == "poison":
                if game.clan.your_cat.status == "medicine cat":
                    chance += 0
                else:
                    chance += 20
            if self.method == "accident":
                chance += 30
            if self.method == "predator":
                chance += 30

            if self.time == "day":
                chance -= 10

        elif self.location == "territory":
            chance -= 10
            if self.method == "attack":
                chance += 10
            if self.method == "poison":
                if game.clan.your_cat.status == "medicine cat":
                    chance += 20
                else:
                    chance += 30
            if self.method == "accident":
                chance -= 1
            if self.method == "predator":
                chance -= 30

        elif self.location == "border":
            chance -= 30
            if self.method == "attack":
                chance -= 20
            if self.method == "poison":
                chance += 30
            if self.method == "accident":
                chance -= 30
            if self.method == "predator":
                chance -= 40

            if game.clan.war.get("at_war", True):
                chance -= 30

        if self.time == "dawn":
            if self.method == "attack":
                chance += 30
            if self.method == "accident":
                chance += 20
            if self.method == "predator":
                chance -= 20

        if self.time == "day":
            if self.method == "attack":
                chance += 60
            if self.method == "poison":
                if game.clan.your_cat.status != "medicine cat":
                    chance += 30
            if self.method == "accident":
                chance += 10
            if self.method == "predator":
                chance += 20

        if self.time == "night":
            if self.method == "attack":
                chance += 20
            if self.method == "predator":
                chance += 10

        if chance < 5:
            chance = 5
        if chance >= 95:
            chance = 95

        return chance

    def handle_murder_fail(self, you, cat_to_murder, accomplice, accompliced):
        """ handles murders failing and victims becoming accidentally injured/sick as a result """
        c_m = str(cat_to_murder.name)
        c_m_pronouns = str(cat_to_murder.pronouns)

        victim_injury_chance = 8

        self.print_chances(cat_to_murder, accomplice)

        discover_chance = randint(1,2)
        fail_texts = []
        if discover_chance == 1:
            fail_texts = ["You attempted to murder "+ c_m + ", but were unsuccessful. They were oblivious of your attempt.",
                            "You attempted to murder "+ c_m + ", but they sidestepped the peril you'd arranged. They remained oblivious to your intent.",
                            "You made an effort to end "+ c_m + "'s life, but fortune favored them. They were none the wiser of your deadly plot.",
                            "Your plot to murder "+ c_m + " fell through, and they went about their day, unaware of the fate you'd intended for them.",
                            "Despite your best efforts, "+ c_m + " remained unscathed. They continued on, blissfully ignorant of your lethal plan.",
                            "Your attempt to kill "+ c_m + " proved futile, and they stayed clueless about your ominous intentions."]
        else:
            victim_injury_chance = randint(1,5)
            if accomplice and accompliced:
                fail_texts = [f"You attempted to murder {c_m}, but your plot was unsuccessful. They appear to be slightly wary of you and {accomplice.name} now.",
                                f"Your effort to end {c_m}'s life was thwarted, and they now seem a bit more cautious around you and {accomplice.name}.",
                                f"Despite your intent to murder {c_m}, they remained unscathed. They now look at you and {accomplice.name} with a hint of suspicion.",
                                f"You and {accomplice.name} tried to kill " + c_m + ", but they survived. {PRONOUN/c_m/subject} now {VERB/v_c/seem/seems} to watch you both with wary eyes.",
                                f"Your plot to murder {c_m} fell through, and they remain alive, now showing signs of mild suspicion towards you and {accomplice.name}."]
                cat_to_murder.relationships[you.ID].dislike += randint(1,20)
                cat_to_murder.relationships[you.ID].platonic_like -= randint(1,15)
                cat_to_murder.relationships[you.ID].comfortable -= randint(1,15)
                cat_to_murder.relationships[you.ID].trust -= randint(1,15)
                cat_to_murder.relationships[you.ID].admiration -= randint(1,15)
                cat_to_murder.relationships[accomplice.ID].dislike += randint(1,20)
                cat_to_murder.relationships[accomplice.ID].platonic_like -= randint(1,15)
                cat_to_murder.relationships[accomplice.ID].comfortable -= randint(1,15)
                cat_to_murder.relationships[accomplice.ID].trust -= randint(1,15)
                cat_to_murder.relationships[accomplice.ID].admiration -= randint(1,15)                
            else:
                fail_texts = ["You attempted to murder "+ c_m + ", but your plot was unsuccessful. They appear to be slightly wary now.",
                                "Your effort to end "+ c_m + "'s life was thwarted, and they now seem a bit more cautious around you.",
                                "Despite your intent to murder "+ c_m + ", they remained unscathed. They look at you now with a hint of suspicion.",
                                "You tried to kill "+ c_m + ", but they survived. They now seem to watch you with wary eyes.",
                                "Your plot to murder "+ c_m + " fell through, and they remain alive, now showing signs of mild suspicion towards you."]
                cat_to_murder.relationships[you.ID].dislike += randint(1,20)
                cat_to_murder.relationships[you.ID].platonic_like -= randint(1,15)
                cat_to_murder.relationships[you.ID].comfortable -= randint(1,15)
                cat_to_murder.relationships[you.ID].trust -= randint(1,15)
                cat_to_murder.relationships[you.ID].admiration -= randint(1,15)

        text = choice(fail_texts)

        if victim_injury_chance == 1:
            if self.method == "attack":
                owie = choice(["claw-wound", "torn pelt", "scrapes"])
            elif self.method == "poison":
                owie = choice(["poisoned", "stomachache", "diarrhea"])
            elif self.method == "accident":
                owie = choice(["broken bone","broken bone", "sprain", "sore", "bruises", "scrapes"])
            elif self.method == "predator":
                owie = choice(["bite-wound", "broken bone", "torn pelt", "mangled leg", "mangled tail"])

            cat_to_murder.get_injured(owie)

            if self.method == "poison":
                text = text + f" Your murder attempt has left {c_m} ill."
            else:
                text = text + f" Your murder attempt life has left {c_m} injured."

        game.cur_events_list.insert(0, Single_Event(text))
        
    
    status_chances = {
        'warrior': 20,
        'medicine cat': 20,
        'mediator': 17,
        'apprentice': 15,
        'medicine cat apprentice': 13,
        'mediator apprentice': 10,
        "queen": 13,
        "queen's apprentice": 13,
        'deputy': 25,
        'leader': 30,
        'elder': 13,
        'kitten': 5,
    }

    skill_chances = {
        'warrior': -5,
        'medicine cat': -5,
        'mediator': 0,
        'apprentice': 5,
        'medicine cat apprentice': 5,
        'mediator apprentice': 5,
        "queen's apprentice": 10,
        'queen': 5,
        'deputy': -10,
        'leader': -15,
        'elder': 5,
        'kitten': 30
    }

    murder_skills = ["quick witted", "avid play-fighter", "oddly observant","never sits still"]
    good_murder_skills = ["clever", "good fighter", "natural intuition","fast runner"]
    great_murder_skills = ["very clever", "formidable fighter", "keen eye","incredible runner"]
    best_murder_skills = ["incredibly clever", "unusually strong fighter", "unnatural senses","fast as the wind"]

    def get_kill(self, you, cat_to_murder, accomplice, accompliced):
        chance = self.status_chances.get(you.status, 0)

        you_healthy = not you.is_ill() and not you.is_injured()
        if accomplice:
            accomplice_healthy = not accomplice.is_ill() and not accomplice.is_injured()
        cat_healthy = not cat_to_murder.is_ill() and not cat_to_murder.is_injured()

        # GENERAL CHANCES
        # skill chances from original murderscreen
        your_skills = []
        if you.skills.primary:
            your_skills.append(you.skills.primary.skill)
        if you.skills.secondary:
            your_skills.append(you.skills.secondary.skill)

        their_skills = []
        if cat_to_murder.skills.primary:
            their_skills.append(cat_to_murder.skills.primary.skill)
        if cat_to_murder.skills.secondary:
            their_skills.append(cat_to_murder.skills.secondary.skill)

        accomp_skills = []
        if accomplice:
            if accomplice.skills.primary:
                accomp_skills.append(accomplice.skills.primary.skill)
            if accomplice.skills.secondary:
                accomp_skills.append(accomplice.skills.secondary.skill)

        if any(skill in self.murder_skills for skill in your_skills):
            chance += 5
        if any(skill in self.good_murder_skills for skill in your_skills):
            chance += 10
        if any(skill in self.great_murder_skills for skill in your_skills):
            chance += 15
        if any(skill in self.best_murder_skills for skill in your_skills):
            chance += 20

        chance += self.skill_chances.get(cat_to_murder.status, 0)
        
        if any(skill in self.murder_skills for skill in their_skills):
            chance -= 5
        if any(skill in self.good_murder_skills for skill in their_skills):
            chance -= 10
        if any(skill in self.great_murder_skills for skill in their_skills):
            chance -= 15
        if any(skill in self.best_murder_skills for skill in their_skills):
            chance -= 20

        # new stuff
        # raises chances:
        if you.joined_df:
            chance += 15
        if you.age != cat_to_murder.age and you.moons > cat_to_murder.moons:
            chance += 10
        if cat_to_murder.age == "senior":
            chance += 10
        if you.status == cat_to_murder.status:
            chance += 5
        if not cat_healthy:
            chance += 10
        if you.experience > cat_to_murder.experience:
            chance += 20
        if accomplice and accompliced:
            chance += 15
            if accomplice.personality.trait == "bloodthirsty":
                chance += 10
            if accomplice.status == "warrior" and accomplice_healthy:
                chance += 15
            if accomplice.status in ["leader", "deputy"] and accomplice_healthy:
                chance += 25
        

        if you.history:
            if you.history.murder:
                if "is_murderer" in you.history.murder:
                    if len(you.history.murder["is_murderer"]) > 0:
                        for i in range(len(you.history.murder["is_murderer"])):
                            chance += 5


        if cat_to_murder.relationships[you.ID].platonic_like > 20 and cat_to_murder.relationships[you.ID].platonic_like < 50:
            chance += 10
        elif cat_to_murder.relationships[you.ID].platonic_like >= 50:
            chance += 15

        if self.time == "night":
            chance += 10

        if cat_to_murder.joined_df:
            chance -= 10
        if cat_to_murder.moons >= you.moons + 4:
            chance -= 10
        if not you_healthy:
            chance -= 10

        if cat_to_murder.status == "leader" and cat_to_murder.shunned == 0 and cat_healthy:
            chance -= 10

        if cat_to_murder.moons < 6:
            for cat in Cat.all_cats_list:
                if cat.ID != you.ID:
                    if cat.status == "queen":
                        chance -= 5
                    if cat.ID == (cat_to_murder.parent1 or cat_to_murder.parent2) or cat.ID in cat_to_murder.adoptive_parents:
                        chance -= 5

        if cat_to_murder.experience > you.experience:
            chance -= 5

        victim_skills_lvl1 = ["watchful", "lives in groups", "interested in oddities", "fascinated by prophecies"]
        victim_skills_lvl2 = ["good guard", "good sport", "omen seeker", "prophecy seeker"]
        victim_skills_lvl3 = ["great guard", "team player", "omen sense", "prophecy interpreter"]
        victim_skills_lvl4 = ["guardian", "insider", "omen sight", "prophet"]

        if any(skill in victim_skills_lvl1 for skill in their_skills):
            chance -= 5
        if any(skill in victim_skills_lvl2 for skill in their_skills):
            chance -= 10
        if any(skill in victim_skills_lvl3 for skill in their_skills):
            chance -= 15
        if any(skill in victim_skills_lvl4 for skill in their_skills):
            chance -= 20
            
        if self.location != "camp":
            if "picky nest builder" in their_skills:
                chance -= 3
            if "steady paws" in their_skills:
                chance -= 7
            if "den builder" in their_skills:
                chance -= 11
            if "campkeeper" in their_skills:
                chance -= 15

        if cat_to_murder.status in ["queen", "queen's apprentice", "medicine cat", "medicine cat apprentice", "kitten"] and self.location != "camp":
            chance -= 8

        if cat_to_murder.history:
            if cat_to_murder.history.murder:
                if "is_murderer" in cat_to_murder.history.murder:
                    if len(cat_to_murder.history.murder["is_murderer"]) > 0:
                        for i in range(len(cat_to_murder.history.murder["is_murderer"])):
                            chance -= 5

        if cat_to_murder.relationships[you.ID].dislike > 20 and cat_to_murder.relationships[you.ID].platonic_like < 50:
            chance -= 10
        elif cat_to_murder.relationships[you.ID].dislike >= 50:
            chance -= 15

        if self.time == "day":
            chance -= 10

        # METHOD CHANCES
        # ATTACK
        if self.method == "attack":

            # raises chances ----------------------------------------------------------------------------

            if you.joined_df:
                chance += 15

            if ("steps lightly" or "mossball hunter" or "avid play-fighter" or
                "plays with freshkill"
                ) in your_skills:
                chance += 3

            if ("graceful" or "good hunter" or "good fighter" or
                "morbid fascination"
                ) in your_skills:
                chance += 7

            if ("elegant" or "great hunter" or "formidable fighter" or
                "blood lover"
                ) in your_skills:
                chance += 11

            if ("radiates elegance" or "renowned hunter" or "unusually strong fighter" or
                "fascinated by gore"
                ) in your_skills:
                chance += 15

            if you.status == "warrior":
                chance += 10
            if you.age != cat_to_murder.age and you.moons > cat_to_murder.moons:
                chance += 10

            if self.location == "border":
                chance += 15

            if you.personality.trait == "bloodthirsty":
                chance += 10

            # lowers chances ----------------------------------------------------------------------------

            if cat_to_murder.status == "warrior":
                chance -= 10
            if you.status in ["mediator", "mediator apprentice", "queen", "queen's apprentice", "medicine cat",
                              "medicine cat apprentice", "kitten"]:
                chance -= 10
            
            if ("avid play-fighter" or
                "plays with freshkill"
                ) in their_skills:
                chance -= 3

            if ("good fighter" or
                "plays with freshkill"
                ) in their_skills:
                chance -= 7

            if ("formidable fighter" or
                "plays with freshkill"
                ) in their_skills:
                chance -= 11

            if ("unusually strong fighter" or
                "plays with freshkill"
                ) in their_skills:
                chance -= 15

            if self.location == "camp":
                chance -= 15
            if cat_to_murder.personality.trait == "bloodthirsty":
                chance -= 10



        if self.method == "poison":

            # raises chances ----------------------------------------------------------------------------
            if you.status == "medicine cat apprentice":
                if you.moons < 19:
                    chance += (you.moons - 6) * 2
                    #   starting at moon 6 (starting apprenticeship), chances should go up.
                    #   7 +2, 8 +4, 9 +6, 10 +8, 11 +10, 12 +12, 13 +14, 14 +16, 15 +18, 16 +20, 17 +22, 18 +24
                else :
                    chance += 25
                    #   to prevent the above from being exploited
            if you.status == "medicine cat":
                chance += 25
            
            if cat_to_murder.is_ill() or cat_to_murder.is_injured():
                chance += 15

            if ("always learning" or "tidy" or "interested in herbs") in your_skills:
                chance += 3

            if ("well-versed" or "fur-care enthusiast" or "good healer") in your_skills:
                chance += 7

            if ("incredibly knowledgeable" or "meticulous cleaner" or "great healer") in your_skills:
                chance += 11

            if ("polymath" or "master of aesthetics" or "fantastic healer") in your_skills:
                chance += 15
            

            if self.location == "camp":
                chance += 20
            if self.location == "territory":
                chance += 15

            # lowers chances ----------------------------------------------------------------------------
            if cat_to_murder.status in ["medicine cat", "medicine cat apprentice"]:
                chance -= 15
            if not cat_to_murder.is_ill() and not cat_to_murder.is_injured():
                chance -= 10
            if you.status not in ["medicine cat", "medicine cat apprentice"]:
                chance -= 20

            if self.location == "border":
                chance -= 10



        if self.method == "accident":
            # raises chances ----------------------------------------------------------------------------
            if accomplice and accompliced:
                chance += 10


            acc_skills_lvl_1 = ["curious wanderer", "good with directions", "constantly climbing"
                                ]
            acc_skills_lvl_2 = ["knowledgeable explorer", "good navigator", "good climber"
                                ]
            acc_skills_lvl_3 = ["brave pathfinder", "great navigator", "great climber"
                                ]
            acc_skills_lvl_4 = ["master of territories", "pathfinder", "impressive climber"
                                ]
            # ????????? why does this section do this. fix it.

            if any(skill in acc_skills_lvl_1 for skill in your_skills):
                chance += 5
            if any(skill in acc_skills_lvl_2 for skill in your_skills):
                chance += 10
            if any(skill in acc_skills_lvl_3 for skill in your_skills):
                chance += 15
            if any(skill in acc_skills_lvl_4 for skill in your_skills):
                chance += 20

            if cat_to_murder.status in ["kitten", "queen", "apprentice", "queen's apprentice", "medicine cat apprentice", "mediator apprentice"] and \
                not cat_to_murder.skills.meets_skill_requirement(SkillPath.EXPLORER) and\
                not cat_to_murder.skills.meets_skill_requirement(SkillPath.NAVIGATOR) and\
                not cat_to_murder.skills.meets_skill_requirement(SkillPath.CLIMBER):
                chance += 10
            if you.age == cat_to_murder.age and you.age in ["kitten", "adolescent"]:
                chance += 10

            if game.clan.biome == "Mountainous":
                chance += 10

            if self.location == "territory":
                chance += 15

            # lowers chances ----------------------------------------------------------------------------
            if any(skill in acc_skills_lvl_1 for skill in their_skills):
                chance -= 5
            if any(skill in acc_skills_lvl_2 for skill in their_skills):
                chance -= 10
            if any(skill in acc_skills_lvl_3 for skill in their_skills):
                chance -= 15
            if any(skill in acc_skills_lvl_4 for skill in their_skills):
                chance -= 20
            
            if cat_to_murder.status in ["warrior", "deputy", "leader"]:
                chance -= 15
            if you.moons >= 12 and cat_to_murder.moons >= 12:
                chance -= 10

            if self.location == "camp":
                chance -= 15

        if self.method == "predator":
            # raises chances ----------------------------------------------------------------------------
            chance += 20
            if accomplice and accompliced:
                chance += 10
                if "other-cat-ly whisperer" in accomp_skills:
                    chance += 5
                if "dog-whisperer" in accomp_skills:
                    chance += 10
                if "multilingual" in accomp_skills:
                    chance += 15
                if "listener of all voices" in accomp_skills:
                    chance += 20

            if cat_to_murder.moons < 6:
                chance += 20
            if self.location in ["territory", "border"]:
                chance += 15

            if "other-cat-ly whisperer" in your_skills:
                chance += 5
            if "dog-whisperer" in your_skills:
                chance += 10
            if "multilingual" in your_skills:
                chance += 15
            if "listener of all voices" in your_skills:
                chance += 20

            # lowers chances ----------------------------------------------------------------------------
            if cat_to_murder.moons >= 12:
                chance -= 10
            if cat_to_murder.status in ["warrior", "deputy", "leader"]:
                chance -= 10
            if you.status in ["queen", "mediator", "kitten", "medicine cat", "queen's apprentice", "mediator apprentice", "medicine cat apprentice"]:
                chance -= 15

            if "watchful" in their_skills:
                chance -= 7
            if "good guard" in their_skills:
                chance -= 11
            if "great guard" in their_skills:
                chance -= 16
            if "guardian" in their_skills:
                chance -= 23

            if "avid play-fighter" in their_skills:
                chance -= 3
            if "good fighter" in their_skills:
                chance -= 8
            if "formidable fighter" in their_skills:
                chance -= 13
            if "unusually strong fighter" in their_skills:
                chance -= 18

            if self.location == "camp":
                chance -= 10

            if "other-cat-ly whisperer" in their_skills:
                chance += 5
            if "dog-whisperer" in their_skills:
                chance += 10
            if "multilingual" in their_skills:
                chance += 15
            if "listener of all voices" in their_skills:
                chance += 20

        if you.moons < 6:
            chance = chance * math.ceil(2/3)

        if cat_to_murder.moons < 6:
            chance = chance * math.ceil(4/3)

        if accomplice and accompliced:
            chance = chance * math.floor(6/5)

        if chance <= 0:
            chance = 5

        if chance > 95:
            chance = 95

        return chance
    
    def update_method_info(self):

        if self.methodinfo:
            self.methodinfo.kill()
            del self.methodinfo

        if self.methodheading:
            self.methodheading.kill()
            del self.methodheading
        
        if self.locationinfo:
            self.locationinfo.kill()
            del self.locationinfo

        if self.locationheading:
            self.locationheading.kill()
            del self.locationheading

        if self.timeinfo:
            self.timeinfo.kill()
            del self.timeinfo

        if self.timeheading:
            self.timeheading.kill()
            del self.timeheading

        # METHOD INFO
        if self.method == "attack":
            self.methodheading = pygame_gui.elements.UITextBox("<b>An Attack</b>",
                                                scale(pygame.Rect((250, 770), (1100, 100))),
                                                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                                                manager=MANAGER)
            self.methodinfo = pygame_gui.elements.UITextBox("A flashy choice for those who aren't afraid to use their claws.",
                                                scale(pygame.Rect((250, 820), (1100, 300))),
                                                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                manager=MANAGER)
        elif self.method == "poison":
            self.methodheading = pygame_gui.elements.UITextBox("<b>A Poisoning</b>",
                                                scale(pygame.Rect((250, 770), (1100, 100))),
                                                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                                                manager=MANAGER)
            self.methodinfo = pygame_gui.elements.UITextBox("A simple, discreet method, as long as you have the knowledge to pull it off.",
                                                scale(pygame.Rect((250, 820), (1100, 300))),
                                                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                manager=MANAGER)
    
        elif self.method == "accident":
            self.methodheading = pygame_gui.elements.UITextBox("<b>An \"Accident\"</b>",
                                                scale(pygame.Rect((250, 770), (1100, 100))),
                                                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                                                manager=MANAGER)
            self.methodinfo = pygame_gui.elements.UITextBox("A rough strategy for those who are great at feigning innocence.",
                                                scale(pygame.Rect((250, 820), (1100, 300))),
                                                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                manager=MANAGER)

        elif self.method == "predator":
            self.methodheading = pygame_gui.elements.UITextBox("<b>Lure a Predator</b>",
                                                scale(pygame.Rect((250, 770), (1100, 100))),
                                                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                                                manager=MANAGER)
            self.methodinfo = pygame_gui.elements.UITextBox("A risky technique for those who don't want to get their own paws dirty.",
                                                scale(pygame.Rect((250, 820), (1100, 300))),
                                                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                manager=MANAGER)
        # LOCATION INFO
        if self.location == "camp":
            if self.method == "predator":
                insert = "To"
            else:
                insert = "In"
                
            self.locationheading = pygame_gui.elements.UITextBox(f"<b>{insert} Camp</b>",
                                                scale(pygame.Rect((250, 920), (1100, 100))),
                                                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                                                manager=MANAGER)
            self.locationinfo = pygame_gui.elements.UITextBox("For a kill closer to home.",
                                                scale(pygame.Rect((250, 970), (1100, 300))),
                                                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                manager=MANAGER)
    
        elif self.location == "territory":
            if self.method == "predator":
                insert = "To"
            else:
                insert = "In"
            self.locationheading = pygame_gui.elements.UITextBox(f"<b>{insert} the Territory</b>",
                                                scale(pygame.Rect((250, 920), (1100, 100))),
                                                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                                                manager=MANAGER)
            self.locationinfo = pygame_gui.elements.UITextBox("Who knows what could happen out there?",
                                                scale(pygame.Rect((250, 970), (1100, 300))),
                                                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                manager=MANAGER)

        elif self.location == "border":
            if self.method == "predator":
                insert = "To"
            else:
                insert = "At"
                
            self.locationheading = pygame_gui.elements.UITextBox(f"<b>{insert} the Border</b>",
                                                scale(pygame.Rect((250, 920), (1100, 100))),
                                                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                                                manager=MANAGER)
            self.locationinfo = pygame_gui.elements.UITextBox("The border is a dangerous place.",
                                                scale(pygame.Rect((250, 970), (1100, 300))),
                                                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                manager=MANAGER)
        # TIME INFO 
        if self.time == "dawn":
            self.timeheading = pygame_gui.elements.UITextBox("<b>At Dawn</b>",
                                                scale(pygame.Rect((250, 1070), (1100, 100))),
                                                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                                                manager=MANAGER)
            self.timeinfo = pygame_gui.elements.UITextBox("The early bird gets the worm!",
                                                scale(pygame.Rect((250, 1120), (1100, 300))),
                                                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                manager=MANAGER)
    
        elif self.time == "day":
            self.timeheading = pygame_gui.elements.UITextBox("<b>During the Day</b>",
                                                scale(pygame.Rect((250, 1070), (1100, 100))),
                                                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                                                manager=MANAGER)
            self.timeinfo = pygame_gui.elements.UITextBox("Want to strike in broad daylight?",
                                                scale(pygame.Rect((250, 1120), (1100, 300))),
                                                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                manager=MANAGER)

        elif self.time == "night":
            self.timeheading = pygame_gui.elements.UITextBox("<b>At Night</b>",
                                                scale(pygame.Rect((250, 1070), (1100, 100))),
                                                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                                                manager=MANAGER)
            self.timeinfo = pygame_gui.elements.UITextBox("Take advantage of the darkness.",
                                                scale(pygame.Rect((250, 1120), (1100, 300))),
                                                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                manager=MANAGER)
            
    def update_chance_text(self, cat_to_murder, accomplice):
        if self.chancetext:
            self.chancetext.kill()
            del self.chancetext

        if self.willingnesstext:
            self.willingnesstext.kill()
            del self.willingnesstext

        if self.selected_cat:
            if (not self.selected_cat.dead and not self.selected_cat.outside):
                if (game.clan.your_cat.skills.meets_skill_requirement(SkillPath.PROPHET) or\
                    game.clan.your_cat.skills.meets_skill_requirement(SkillPath.CLEVER) or\
                    game.clan.your_cat.skills.meets_skill_requirement(SkillPath.SENSE) or\
                    game.clan.your_cat.skills.meets_skill_requirement(SkillPath.OMEN) or\
                    game.clan.your_cat.skills.meets_skill_requirement(SkillPath.INSIGHTFUL)):
                    c_text = ""
                    if accomplice:
                        chance = self.get_kill(game.clan.your_cat, self.cat_to_murder, self.selected_cat, True)
                    else:
                        chance = self.get_kill(game.clan.your_cat, cat_to_murder, None, False)

                    risk_chance = self.get_risk_chance(self.selected_cat, accomplice=None, accompliced=None)
                    discover_chance = self.get_discover_chance(self.selected_cat, accomplice=None, accompliced=False)

                    if chance < 20:
                        c_text = "very low"
                    elif chance < 30:
                        c_text = "low"
                    elif chance < 50:
                        c_text = "average"
                    elif chance < 80:
                        c_text = "high"
                    else:
                        c_text = "very high"

                    insert = ""

                    if accomplice:
                        insert = "possible success chance: "
                    else:
                        insert = "success chance: "


                    if game.settings['dark mode']:
                        self.chancetext = pygame_gui.elements.UITextBox(insert + c_text, scale(pygame.Rect((248, 610),(210, 250))),
                                                                        object_id="#text_box_22_horizcenter_vertcenter_spacing_95_dark", manager=MANAGER)

                    else:
                        self.chancetext = pygame_gui.elements.UITextBox(insert + c_text, scale(pygame.Rect((248, 610),(210, 250))),
                                                                        object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
                                                                        manager=MANAGER)
                        
                if self.stage == "choose accomplice":
                    if self.selected_cat is not None:
                        a_text = ""
                        chance = self.get_kill(game.clan.your_cat, self.cat_to_murder, accomplice=self.selected_cat, accompliced=False)

                        chance = self.get_accomplice_chance(game.clan.your_cat, self.selected_cat, self.cat_to_murder)
                        
                        if game.config["accomplice_chance"] != -1:
                            try:
                                chance = game.config["accomplice_chance"]
                            except:
                                pass
                        if chance < 20:
                            a_text = "very low"
                        elif chance < 30:
                            a_text = "low"
                        elif chance < 50:
                            a_text = "average"
                        elif chance < 80:
                            a_text = "high"
                        else:
                            a_text = "very high"

                        if game.settings['dark mode']:
                            self.willingnesstext = pygame_gui.elements.UITextBox("willingness: " + a_text,
                                                                                                    scale(pygame.Rect((1145, 610),
                                                                                                                        (210, 250))),
                                                                                                    object_id="#text_box_22_horizcenter_vertcenter_spacing_95_dark",
                                                                                                    manager=MANAGER)

                        else:
                            self.willingnesstext = pygame_gui.elements.UITextBox("willingness: " + a_text,
                                                                                                scale(pygame.Rect((1145, 610),
                                                                                                                    (210, 250))),
                                                                                                object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
                                                                                                manager=MANAGER)
                else:
                    if game.settings['dark mode']:
                        self.willingnesstext = pygame_gui.elements.UITextBox("" ,
                                                                                                scale(pygame.Rect((1145, 610),
                                                                                                                    (210, 250))),
                                                                                                object_id="#text_box_22_horizcenter_vertcenter_spacing_95_dark",
                                                                                                manager=MANAGER)

                    else:
                        self.willingnesstext = pygame_gui.elements.UITextBox("",
                                                                                            scale(pygame.Rect((1145, 610),
                                                                                                                (210, 250))),
                                                                                            object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
                                                                                            manager=MANAGER)
        else:
            self.willingnesstext = None
            self.chancetext = None

    def update_selected_cat(self):
        """Updates the image and information on the currently selected mentor"""
        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}

        if self.selected_cat and not self.selected_cat.dead:
            self.confirm_mentor.enable()

            self.selected_details["selected_image"] = pygame_gui.elements.UIImage(
                scale(pygame.Rect((210, 190), (270, 270))),
                pygame.transform.scale(
                    self.selected_cat.sprite,
                    (270, 270)), manager=MANAGER)

            info = self.selected_cat.status + "\n" + \
                   self.selected_cat.genderalign + "\n" + self.selected_cat.personality.trait + "\n"

            if self.selected_cat.moons < 1:
                info += "???"
            else:
                info += self.selected_cat.skills.skill_string(short=True)

            # vicinfo
            
            self.selected_details["selected_info"] = pygame_gui.elements.UITextBox(info,
                                                                                   scale(pygame.Rect((205, 475),
                                                                                                     (300, 250))),
                                                                                   object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
                                                                                   manager=MANAGER)

            name = str(self.selected_cat.name)  # get name
            if 17 <= len(name):  # check name length
                short_name = str(name)[0:15]
                name = short_name + '...'
            self.selected_details["victim_name"] = pygame_gui.elements.ui_label.UILabel(
                scale(pygame.Rect((205, 472), (300, 60))),
                name,
                object_id="#text_box_34_horizcenter", manager=MANAGER)
            
            self.update_chance_text(self.selected_cat, accomplice=None)
        elif self.selected_cat and self.selected_cat.dead:
            self.stage = "choose murder cat"
            self.confirm_mentor.disable()
        else:
            self.confirm_mentor.disable()
            

    def get_accomplice_chance(self, you, accomplice, cat_to_murder):
        chance = 10
        if accomplice is not None:
            if accomplice.relationships[you.ID].platonic_like > 10:
                chance += 10
            if accomplice.relationships[you.ID].dislike < 10:
                chance += 10
            if accomplice.relationships[you.ID].romantic_love > 10:
                chance += 10
            if accomplice.relationships[you.ID].comfortable > 10:
                chance += 10
            if accomplice.relationships[you.ID].trust > 10:
                chance += 10
            if accomplice.relationships[you.ID].admiration > 10:
                chance += 10
            if you.status in ['medicine cat', 'mediator', 'deputy', 'leader']:
                chance += 10
            if accomplice.status in ['medicine cat', 'mediator', 'deputy', 'leader']:
                chance -= 20
            if accomplice.ID in game.clan.your_cat.mate:
                chance += 50
            if game.clan.your_cat.is_related(accomplice, False):
                chance += 30

            #relationship to the victim
            # TODO: make these chances better lol
            if cat_to_murder.ID in accomplice.relationships:
                chance += accomplice.relationships[self.cat_to_murder.ID].dislike / 2
                chance -= accomplice.relationships[self.cat_to_murder.ID].platonic_like
                chance -= accomplice.relationships[self.cat_to_murder.ID].romantic_love

        return chance
                    
    def update_selected_cat2(self):
        """Updates the image and information on the currently selected mentor"""
        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}

        if self.selected_cat and self.selected_cat.ID != self.cat_to_murder.ID and not self.selected_cat.dead:
            self.selected_details["selected_image"] = pygame_gui.elements.UIImage(
                scale(pygame.Rect((1120, 190), (270, 270))),
                pygame.transform.scale(
                    self.selected_cat.sprite,
                    (300, 300)), manager=MANAGER)

            info = self.selected_cat.status + "\n" + \
                   self.selected_cat.genderalign + "\n" + self.selected_cat.personality.trait + "\n"
            
            if self.selected_cat.moons < 1:
                info += "???"
            else:
                info += self.selected_cat.skills.skill_string(short=True)
            
            self.selected_details["selected_info_acc"] = pygame_gui.elements.UITextBox(info,
                                                                                   scale(pygame.Rect((1102, 475),
                                                                                                     (300, 250))),
                                                                                   object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
                                                                                   manager=MANAGER)

            name = str(self.selected_cat.name)  # get name
            if 17 <= len(name):  # check name length
                short_name = str(name)[0:15]
                name = short_name + '...'
            self.selected_details["mentor_name"] = pygame_gui.elements.ui_label.UILabel(
                scale(pygame.Rect((1105, 472), (300, 60))),
                name,
                object_id="#text_box_34_horizcenter", manager=MANAGER)
        
        if self.selected_cat:
            self.update_chance_text(self.cat_to_murder, accomplice=self.selected_cat)
            
            

    def update_cat_list(self):
        """Updates the cat sprite buttons. """
        valid_mentors = self.chunks(self.get_valid_cats(), 30)

        # If the number of pages becomes smaller than the number of our current page, set
        #   the current page to the last page
        if self.current_page > len(valid_mentors):
            self.list_page = len(valid_mentors)

        # Handle which next buttons are clickable.
        if len(valid_mentors) <= 1:
            self.previous_page_button.disable()
            self.next_page_button.disable()
        elif self.current_page >= len(valid_mentors):
            self.previous_page_button.enable()
            self.next_page_button.disable()
        elif self.current_page == 1 and len(valid_mentors) > 1:
            self.previous_page_button.disable()
            self.next_page_button.enable()
        else:
            self.previous_page_button.enable()
            self.next_page_button.enable()
        display_cats = []
        if valid_mentors:
            display_cats = valid_mentors[self.current_page - 1]

        # Kill all the currently displayed cats.
        for ele in self.cat_list_buttons:
            self.cat_list_buttons[ele].kill()
        self.cat_list_buttons = {}

        pos_x = 0
        pos_y = 40
        i = 0
        for cat in display_cats:
            self.cat_list_buttons["cat" + str(i)] = UISpriteButton(
                scale(pygame.Rect((200 + pos_x, 800 + pos_y), (100, 100))),
                cat.sprite, cat_object=cat, manager=MANAGER)
            pos_x += 120
            if pos_x >= 1100:
                pos_x = 0
                pos_y += 120
            i += 1
            
    def update_cat_list2(self):
        """Updates the cat sprite buttons. """
        valid_mentors = self.chunks(self.get_valid_cats2(), 30)

        # If the number of pages becomes smaller than the number of our current page, set
        #   the current page to the last page
        if self.current_page > len(valid_mentors):
            self.list_page = len(valid_mentors)

        # Handle which next buttons are clickable.
        if len(valid_mentors) <= 1:
            self.previous_page_button.disable()
            self.next_page_button.disable()
        elif self.current_page >= len(valid_mentors):
            self.previous_page_button.enable()
            self.next_page_button.disable()
        elif self.current_page == 1 and len(valid_mentors) > 1:
            self.previous_page_button.disable()
            self.next_page_button.enable()
        else:
            self.previous_page_button.enable()
            self.next_page_button.enable()
        display_cats = []
        if valid_mentors and len(valid_mentors) > self.current_page - 1:
            display_cats = valid_mentors[self.current_page - 1]

        # Kill all the currently displayed cats.
        for ele in self.cat_list_buttons:
            self.cat_list_buttons[ele].kill()
        self.cat_list_buttons = {}

        pos_x = 0
        pos_y = 40
        i = 0
        for cat in display_cats:
            self.cat_list_buttons["cat" + str(i)] = UISpriteButton(
                scale(pygame.Rect((200 + pos_x, 800 + pos_y), (100, 100))),
                cat.sprite, cat_object=cat, manager=MANAGER)
            pos_x += 120
            if pos_x >= 1100:
                pos_x = 0
                pos_y += 120
            i += 1


    def get_valid_cats(self):
        valid_mentors = []

        for cat in Cat.all_cats_list:
            if not cat.dead and not cat.outside and not cat.ID == game.clan.your_cat.ID and not cat.moons == 0:
                valid_mentors.append(cat)
        
        return valid_mentors

    def get_valid_cats2(self):
        valid_mentors = []
        for cat in Cat.all_cats_list:
            if not cat.dead and not cat.outside and cat.ID != game.clan.your_cat.ID and cat.ID != self.cat_to_murder.ID and not cat.moons == 0:
                valid_mentors.append(cat)
        
        return valid_mentors

    def on_use(self):
        # Due to a bug in pygame, any image with buttons over it must be blited
        if self.list_frame:
            screen.blit(self.list_frame, (150 / 1600 * screen_x, 790 / 1400 * screen_y))

    def chunks(self, L, n):
        return [L[x: x + n] for x in range(0, len(L), n)]
