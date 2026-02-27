from random import choice, randrange
import pygame_gui
import random
from .Screens import Screens
from re import sub

import pygame
import pygame_gui

from scripts.utility import get_text_box_theme, scale, generate_sprite
from scripts.housekeeping.version import get_version_info
from scripts.clan import Clan
from scripts.cat.cats import create_example_cats, Cat, Personality
from scripts.cat.skills import Skill, SkillPath
from scripts.cat.pelts import Pelt
from scripts.cat.cats import create_example_cats, create_cat, Cat
from scripts.cat.names import names
from scripts.clan import Clan
from scripts.game_structure import image_cache
from scripts.game_structure.game_essentials import game, screen, screen_x, screen_y, MANAGER
from scripts.patrol.patrol import Patrol
from scripts.cat.skills import SkillPath
from scripts.game_structure.game_essentials import (
    game,
    screen,
    screen_x,
    screen_y,
    MANAGER,
)
from scripts.game_structure.ui_elements import UIImageButton, UISpriteButton
from scripts.patrol.patrol import Patrol
from scripts.utility import get_text_box_theme, scale
from .Screens import Screens
from ..cat.sprites import sprites
from ..game_structure.windows import SymbolFilterWindow


class NewLifeScreen(Screens):
    # UI images
    clan_frame_img = pygame.transform.scale(pygame.image.load(
        'resources/images/pick_clan_screen/clan_name_frame.png').convert_alpha(), (432, 100))
    name_clan_img = pygame.transform.scale(pygame.image.load(
        'resources/images/pick_clan_screen/name_clan_light.png').convert_alpha(), (1600, 1400))
    leader_img = pygame.transform.scale(pygame.image.load(
        'resources/images/pick_clan_screen/choose cat.png').convert_alpha(), (1600, 1400))
    leader_img_dark = pygame.transform.scale(pygame.image.load(
        'resources/images/pick_clan_screen/choose cat dark.png').convert_alpha(), (1600, 1400))
    deputy_img = pygame.transform.scale(pygame.image.load(
        'resources/images/pick_clan_screen/deputy_light.png').convert_alpha(), (1600, 1400))
    medic_img = pygame.transform.scale(pygame.image.load(
        'resources/images/pick_clan_screen/med_light.png').convert_alpha(), (1600, 1400))
    clan_img = pygame.transform.scale(pygame.image.load(
        'resources/images/pick_clan_screen/clan_light.png').convert_alpha(), (1600, 1400))
    bg_preview_border = pygame.transform.scale(
        pygame.image.load("resources/images/bg_preview_border.png").convert_alpha(), (466, 416))
    
    your_name_img = pygame.transform.scale(pygame.image.load(
        'resources/images/pick_clan_screen/Your name screen.png').convert_alpha(), (1600, 1400))
    your_name_img_dark = pygame.transform.scale(pygame.image.load(
        'resources/images/pick_clan_screen/Your name screen darkmode.png').convert_alpha(), (1600, 1400))
    your_name_txt1 = pygame.transform.scale(pygame.image.load(
        'resources/images/pick_clan_screen/your name text1.png').convert_alpha(), (796, 52))
    your_name_txt2 = pygame.transform.scale(pygame.image.load(
        'resources/images/pick_clan_screen/your name text2.png').convert_alpha(), (536, 52))
    
    #images for the customizing screen
    sprite_preview_bg = pygame.transform.scale(pygame.image.load(
        'resources/images/sprite_preview.png').convert_alpha(), (1600, 1400))
    
    sprite_preview_bg_dark = pygame.transform.scale(pygame.image.load(
        'resources/images/sprite_preview_dark.png').convert_alpha(), (1600, 1400))
    
    poses_bg = pygame.transform.scale(pygame.image.load(
        'resources/images/poses_bg.png').convert_alpha(), (1600, 1400))
    
    poses_bg_dark = pygame.transform.scale(pygame.image.load(
        'resources/images/poses_bg_dark.png').convert_alpha(), (1600, 1400))
    
    choice_bg = pygame.transform.scale(pygame.image.load(
        'resources/images/custom_choice_bg.png').convert_alpha(), (1600, 1400))
    
    choice_bg_dark = pygame.transform.scale(pygame.image.load(
        'resources/images/custom_choice_bg_dark.png').convert_alpha(), (1600, 1400))
    

    def __init__(self, name=None):
        super().__init__(name)
        # current page for symbol choosing
        self.current_page = 1

        self.rolls_left = game.config["clan_creation"]["rerolls"]
        self.menu_warning = None
        self.selected_cat = None
        self.your_cat = None
        self.elements = {}
        self.tabs = {}
        self.symbol_buttons = {}
        self.sub_screen = 'choose leader'
        self.current_members = []

    def screen_switches(self):
        self.sub_screen = 'choose leader'
        self.custom_cat = None
        self.elements = {}
        self.pname="SingleColour"
        self.length="short"
        self.colour="WHITE"
        self.white_patches=None
        self.eye_color="BLUE"
        self.eye_colour2="BLUE"
        self.tortiebase=None
        self.tortiecolour=None
        self.pattern=None
        self.tortiepattern=None
        self.vitiligo=None
        self.points=None
        self.paralyzed=False
        self.opacity=100
        self.scars=[]
        self.tint="None"
        self.skin="BLACK"
        self.white_patches_tint="None"
        self.kitten_sprite=0
        self.reverse=False
        self.skill = "Random"
        self.accessories=[]
        self.inventory = []
        self.sex = "male"
        self.personality = "troublesome"
        self.accessory = None
        self.permanent_condition = None
        self.preview_age = "kitten"
        self.page = 0
        self.adolescent_pose = 0
        self.adult_pose = 0
        self.elder_pose = 0
        self.faith = "flexible"
        game.choose_cats = {}
        self.skills = []
        for skillpath in SkillPath:
            for skill in skillpath.value:
                self.skills.append(skill)
        # Buttons that appear on every screen.
        self.menu_warning = pygame_gui.elements.UITextBox(
            '',
            scale(pygame.Rect((50, 50), (1200, -1))),
            object_id=get_text_box_theme("#text_box_22_horizleft"),
            manager=MANAGER,
        )
        self.main_menu = UIImageButton(
            scale(pygame.Rect((50, 100), (306, 60))),
            "",
            object_id="#main_menu_button",
            manager=MANAGER,
        )
        for c in list(Cat.all_cats.keys()):
            self.current_members.append(c)
        self.hide_menu_buttons()
        create_example_cats()
        self.open_choose_leader()

    def handle_event(self, event):
        if self.sub_screen == 'customize cat':
            self.handle_customize_cat_event(event)
        elif event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.main_menu:
                self.change_screen('start screen')
            if self.sub_screen == 'choose name':
                self.handle_choose_name_event(event)
            elif self.sub_screen == 'choose leader':
                self.handle_choose_leader_event(event)
            elif self.sub_screen == "saved screen":
                self.handle_saved_clan_event(event)

    def handle_choose_leader_event(self, event):
        if event.ui_element in [
            self.elements["roll1"],
            self.elements["roll2"],
            self.elements["roll3"],
            self.elements["dice"],
        ]:
            self.elements["select_cat"].hide()
            create_example_cats()  # create new cats
            self.selected_cat = None  # Your selected cat now no longer exists. Sad. They go away.
            self.refresh_cat_images_and_info()  # Refresh all the images.
            self.rolls_left -= 1
            if game.config["clan_creation"]["rerolls"] == 3:
                event.ui_element.disable()
            else:
                self.elements["reroll_count"].set_text(str(self.rolls_left))
                if self.rolls_left == 0:
                    event.ui_element.disable()

        elif event.ui_element in [self.elements["cat" + str(u)] for u in range(0, 12)]:
            self.selected_cat = event.ui_element.return_cat_object()
            self.refresh_cat_images_and_info(self.selected_cat)
            self.refresh_text_and_buttons()
        elif event.ui_element == self.elements['select_cat']:
            self.your_cat = self.selected_cat
            self.selected_cat = None
            self.open_name_cat()
        elif event.ui_element == self.elements['customize']:
            self.open_customize_cat()
        elif event.ui_element == self.elements['previous_step']:
            self.selected_cat = None
            self.delete_example_cats()
            self.change_screen("events screen")

    def refresh_text_and_buttons(self):
        """Refreshes the button states and text boxes"""
        if self.sub_screen == "game mode":
            # Set the mode explanation text
            if self.game_mode == "classic":
                display_text = self.classic_mode_text
                display_name = "Classic Mode"
            elif self.game_mode == "expanded":
                display_text = self.expanded_mode_text
                display_name = "Expanded Mode"
            elif self.game_mode == "cruel season":
                display_text = self.cruel_mode_text
                display_name = "Cruel Season"
            else:
                display_text = ""
                display_name = "ERROR"
            self.elements["mode_details"].set_text(display_text)
            self.elements["mode_name"].set_text(display_name)

            # Update the enabled buttons for the game selection to disable the
            # buttons for the mode currently selected. Mostly for aesthetics, and it
            # make it very clear which mode is selected.
            if self.game_mode == "classic":
                self.elements["classic_mode_button"].disable()
                self.elements["expanded_mode_button"].enable()
                self.elements["cruel_mode_button"].enable()
            elif self.game_mode == "expanded":
                self.elements["classic_mode_button"].enable()
                self.elements["expanded_mode_button"].disable()
                self.elements["cruel_mode_button"].enable()
            elif self.game_mode == "cruel season":
                self.elements["classic_mode_button"].enable()
                self.elements["expanded_mode_button"].enable()
                self.elements["cruel_mode_button"].disable()
            else:
                self.elements["classic_mode_button"].enable()
                self.elements["expanded_mode_button"].enable()
                self.elements["cruel_mode_button"].enable()

            # Don't let the player go forwards with cruel mode, it's not done yet.
            if self.game_mode == "cruel season":
                self.elements["next_step"].disable()
            else:
                self.elements["next_step"].enable()
        # Show the error message if you try to choose a child for leader, deputy, or med cat.
        elif self.sub_screen in ['choose leader', 'choose deputy', 'choose med cat']:
            self.elements['select_cat'].show()
        # Refresh the choose-members background to match number of cat's chosen.
        elif self.sub_screen == "choose members":
            if len(self.members) == 0:
                self.elements["background"].set_image(
                    pygame.transform.scale(
                        pygame.image.load(
                            "resources/images/pick_clan_screen/clan_none_light.png"
                        ).convert_alpha(),
                        (1600, 1400),
                    )
                )
                self.elements["next_step"].disable()
            elif len(self.members) == 1:
                self.elements["background"].set_image(
                    pygame.transform.scale(
                        pygame.image.load(
                            "resources/images/pick_clan_screen/clan_one_light.png"
                        ).convert_alpha(),
                        (1600, 1400),
                    )
                )
                self.elements["next_step"].disable()
            elif len(self.members) == 2:
                self.elements["background"].set_image(
                    pygame.transform.scale(
                        pygame.image.load(
                            "resources/images/pick_clan_screen/clan_two_light.png"
                        ).convert_alpha(),
                        (1600, 1400),
                    )
                )
                self.elements["next_step"].disable()
            elif len(self.members) == 3:
                self.elements["background"].set_image(
                    pygame.transform.scale(
                        pygame.image.load(
                            "resources/images/pick_clan_screen/clan_three_light.png"
                        ).convert_alpha(),
                        (1600, 1400),
                    )
                )
                self.elements["next_step"].disable()
            elif 4 <= len(self.members) <= 6:
                self.elements["background"].set_image(
                    pygame.transform.scale(
                        pygame.image.load(
                            "resources/images/pick_clan_screen/clan_four_light.png"
                        ).convert_alpha(),
                        (1600, 1400),
                    )
                )
                self.elements["next_step"].enable()
                # In order for the "previous step" to work properly, we must enable this button, just in case it
                # was disabled in the next step.
                self.elements["select_cat"].enable()
            elif len(self.members) == 7:
                self.elements["background"].set_image(
                    pygame.transform.scale(
                        pygame.image.load(
                            "resources/images/pick_clan_screen/clan_full_light.png"
                        ).convert_alpha(),
                        (1600, 1400),
                    )
                )
                self.elements["select_cat"].disable()
                self.elements["next_step"].enable()

            # Hide the recruit cat button if no cat is selected.
            if self.selected_cat is not None:
                self.elements["select_cat"].show()
            else:
                self.elements["select_cat"].hide()

        elif self.sub_screen == "choose camp":
            # Enable/disable biome buttons
            if self.biome_selected == "Forest":
                self.elements["forest_biome"].disable()
                self.elements["mountain_biome"].enable()
                self.elements["plains_biome"].enable()
                self.elements["beach_biome"].enable()
                self.elements["rainworld_biome"].enable()
                self.elements["desert_biome"].enable()
                self.elements["wetlands_biome"].enable()
            elif self.biome_selected == "Mountainous":
                self.elements["forest_biome"].enable()
                self.elements["mountain_biome"].disable()
                self.elements["plains_biome"].enable()
                self.elements["beach_biome"].enable()
                self.elements["rainworld_biome"].enable()
                self.elements["desert_biome"].enable()
                self.elements["wetlands_biome"].enable()
            elif self.biome_selected == "Plains":
                self.elements["forest_biome"].enable()
                self.elements["mountain_biome"].enable()
                self.elements["plains_biome"].disable()
                self.elements["beach_biome"].enable()
                self.elements["rainworld_biome"].enable()
                self.elements["desert_biome"].enable()
                self.elements["wetlands_biome"].enable()
            elif self.biome_selected == "Beach":
                self.elements["forest_biome"].enable()
                self.elements["mountain_biome"].enable()
                self.elements["plains_biome"].enable()
                self.elements["beach_biome"].disable()
                self.elements["rainworld_biome"].enable()
                self.elements["desert_biome"].enable()
                self.elements["wetlands_biome"].enable()


                # NEONPINK BIOMES
            elif self.biome_selected == "Rainworld":
                self.elements["forest_biome"].enable()
                self.elements["mountain_biome"].enable()
                self.elements["plains_biome"].enable()
                self.elements["beach_biome"].enable()
                self.elements["rainworld_biome"].disable()
                self.elements["desert_biome"].enable()
                self.elements["wetlands_biome"].enable()
            elif self.biome_selected == "Desert":
                self.elements["forest_biome"].enable()
                self.elements["mountain_biome"].enable()
                self.elements["plains_biome"].enable()
                self.elements["beach_biome"].enable()
                self.elements["rainworld_biome"].enable()
                self.elements["desert_biome"].disable()
                self.elements["wetlands_biome"].enable()
            elif self.biome_selected == "Wetlands":
                self.elements["forest_biome"].enable()
                self.elements["mountain_biome"].enable()
                self.elements["plains_biome"].enable()
                self.elements["beach_biome"].enable()
                self.elements["rainworld_biome"].enable()
                self.elements["desert_biome"].enable()
                self.elements["wetlands_biome"].disable()

            if self.selected_season == "Newleaf":
                self.tabs["newleaf_tab"].disable()
                self.tabs["greenleaf_tab"].enable()
                self.tabs["leaffall_tab"].enable()
                self.tabs["leafbare_tab"].enable()
            elif self.selected_season == "Greenleaf":
                self.tabs["newleaf_tab"].enable()
                self.tabs["greenleaf_tab"].disable()
                self.tabs["leaffall_tab"].enable()
                self.tabs["leafbare_tab"].enable()
            elif self.selected_season == "Leaf-fall":
                self.tabs["newleaf_tab"].enable()
                self.tabs["greenleaf_tab"].enable()
                self.tabs["leaffall_tab"].disable()
                self.tabs["leafbare_tab"].enable()
            elif self.selected_season == "Leaf-bare":
                self.tabs["newleaf_tab"].enable()
                self.tabs["greenleaf_tab"].enable()
                self.tabs["leaffall_tab"].enable()
                self.tabs["leafbare_tab"].disable()

            if self.biome_selected and self.selected_camp_tab:
                self.elements["next_step"].enable()

            # Deal with tab and shown camp image:
            self.refresh_selected_camp()
        elif self.sub_screen == "choose symbol":
            if self.symbol_selected:
                if self.symbol_selected in self.symbol_buttons:
                    self.symbol_buttons[self.symbol_selected].disable()
                # refresh selected symbol image
                self.elements["selected_symbol"].set_image(
                    pygame.transform.scale(
                        sprites.sprites[self.symbol_selected], (200, 200)
                    ).convert_alpha()
                )
                symbol_name = self.symbol_selected.replace("symbol", "")
                self.text["selected"].set_text(f"Selected Symbol: {symbol_name}")
                self.elements["selected_symbol"].show()
                self.elements["done_button"].enable()


    def handle_choose_name_event(self, event):
        if event.ui_element == self.elements['next_step']:
            new_name = sub(r'[^A-Za-z0-9 ]+', "", self.elements["name_entry"].get_text()).strip()
            if not new_name:
                self.elements["error"].set_text("Your cat's name cannot be empty")
                self.elements["error"].show()
                return
            self.your_cat.name.prefix = new_name
            self.save_clan()
            self.open_clan_saved_screen()
        elif event.ui_element == self.elements["random"]:
            self.elements["name_entry"].set_text(choice(names.names_dict["normal_prefixes"]))
        elif event.ui_element == self.elements['previous_step']:
            self.selected_cat = None
            self.open_choose_leader()

    def handle_saved_clan_event(self, event):
        if event.ui_element == self.elements["continue"]:
            self.change_screen("camp screen")

    def exit_screen(self):
        self.main_menu.kill()
        self.menu_warning.kill()
        self.clear_all_page()
        self.rolls_left = game.config["clan_creation"]["rerolls"]
        return super().exit_screen()
    
    def on_use(self):
        if self.sub_screen == 'choose name':
            if self.elements["name_entry"].get_text() == "":
                self.elements['next_step'].disable()
            elif self.elements["name_entry"].get_text().startswith(" "):
                self.elements["error"].set_text("Your name cannot start with a space.")
                self.elements["error"].show()
                self.elements['next_step'].disable()
            else:
                self.elements["error"].hide()
                self.elements['next_step'].enable()
    
    def clear_all_page(self):
        """Clears the entire page, including layout images"""
        for image in self.elements:
            self.elements[image].kill()
        for tab in self.tabs:
            self.tabs[tab].kill()
        for button in self.symbol_buttons:
            self.symbol_buttons[button].kill()
        self.elements = {}
    
    def refresh_selected_cat_info(self, selected=None):
        # SELECTED CAT INFO
        if selected is not None:

            if self.sub_screen == 'choose leader':
                self.elements['cat_name'].set_text(str(selected.name))
            else:
                self.elements['cat_name'].set_text(str(selected.name))
            self.elements['cat_name'].show()
            self.elements['cat_info'].set_text(selected.gender + "\n" +
                                            "fur length: " + str(selected.pelt.length) + "\n" +
                                                str(selected.personality.trait) + "\n" +
                                                str(selected.skills.skill_string()))
            if selected.permanent_condition:

                self.elements['cat_info'].set_text(selected.gender + "\n" +
                                            "fur length: " + str(selected.pelt.length) + "\n" +
                                                str(selected.personality.trait) + "\n" +
                                                str(selected.skills.skill_string()) + "\n" +
                                                "permanent condition: " + list(selected.permanent_condition.keys())[0])
            self.elements['cat_info'].show()

    def refresh_cat_images_and_info(self, selected=None):
        """Update the image of the cat selected in the middle. Info and image.
        Also updates the location of selected cats."""

        column_poss = [100, 200]

        # updates selected cat info
        self.refresh_selected_cat_info(selected)

        # CAT IMAGES
        for u in range(6):
            if "cat" + str(u) in self.elements:
                self.elements["cat" + str(u)].kill()
            if game.choose_cats[u] == selected:
                self.elements["cat" + str(u)] = self.elements[
                    "cat" + str(u)
                ] = UISpriteButton(
                    scale(pygame.Rect((540, 400), (300, 300))),
                    pygame.transform.scale(game.choose_cats[u].sprite, (300, 300)),
                    cat_object=game.choose_cats[u],
                )
            else:
                self.elements["cat" + str(u)] = UISpriteButton(
                    scale(pygame.Rect((column_poss[0], 260 + 100 * u), (100, 100))),
                    game.choose_cats[u].sprite,
                    cat_object=game.choose_cats[u], manager=MANAGER)
        for u in range(6, 12):
            if "cat" + str(u) in self.elements:
                self.elements["cat" + str(u)].kill()
            if game.choose_cats[u] == selected:
                self.elements["cat" + str(u)] = self.elements["cat" + str(u)] = UISpriteButton(
                    scale(pygame.Rect((540, 400), (300, 300))),
                    pygame.transform.scale(game.choose_cats[u].sprite, (300, 300)),
                    cat_object=game.choose_cats[u], manager=MANAGER)
            else:
                self.elements["cat" + str(u)] = UISpriteButton(
                    scale(
                        pygame.Rect((column_poss[1], 260 + 100 * (u - 6)), (100, 100))
                    ),
                    game.choose_cats[u].sprite,
                    cat_object=game.choose_cats[u], manager=MANAGER)
                
    def refresh_cat_images_and_info2(self, selected=None):
        """Update the image of the cat selected in the middle. Info and image.
        Also updates the location of selected cats. """

        column_poss = [100, 200]

        # updates selected cat info
        self.refresh_selected_cat_info(selected)

        # # CAT IMAGES
        # for u in range(6):
        #     if game.choose_cats[u] in [self.leader, self.deputy, self.med_cat] + self.members:
        #         self.elements["cat" + str(u)] = self.elements["cat" + str(u)] = UISpriteButton(
        #             scale(pygame.Rect((620, 400), (300, 300))),
        #             pygame.transform.scale(game.choose_cats[u].sprite, (300, 300)),
        #             cat_object=game.choose_cats[u])

        # for u in range(6, 12):
        #     if game.choose_cats[u] in [self.leader, self.deputy, self.med_cat] + self.members:
        #         self.elements["cat" + str(u)] = self.elements["cat" + str(u)] = UISpriteButton(
        #             scale(pygame.Rect((620, 400), (300, 300))),
        #             pygame.transform.scale(game.choose_cats[u].sprite, (300, 300)),
        #             cat_object=game.choose_cats[u])
        
    def open_name_cat(self):
        """Opens the name clan screen"""
        
        self.clear_all_page()
        
        self.elements["leader_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((580, 300), (400, 400))),
                                                                    pygame.transform.scale(
                                                                        self.your_cat.sprite,
                                                                        (200, 200)), manager=MANAGER)
        if game.settings["dark mode"]:
            self.elements['background'] = pygame_gui.elements.UIImage(scale(pygame.Rect((0, 0), (1600, 1400))),
                                                                    NewLifeScreen.your_name_img_dark, manager=MANAGER)
        else:
            self.elements['background'] = pygame_gui.elements.UIImage(scale(pygame.Rect((0, 0), (1600, 1400))),
                                                                    NewLifeScreen.your_name_img, manager=MANAGER)

        self.elements['text1'] = pygame_gui.elements.UIImage(scale(pygame.Rect((520, 730), (796, 52))),
                                                                  NewLifeScreen.your_name_txt1, manager=MANAGER)
        self.elements['text2'] = pygame_gui.elements.UIImage(scale(pygame.Rect((520, 790), (536, 52))),
                                                                  NewLifeScreen.your_name_txt2, manager=MANAGER)
        self.elements['background'].disable()

        self.elements["version_background"] = UIImageButton(scale(pygame.Rect((1450, 1344), (1400, 55))), "", object_id="blank_button", manager=MANAGER)
        self.elements["version_background"].disable()

        if game.settings['fullscreen']:
            version_number = pygame_gui.elements.UILabel(
                pygame.Rect((1500, 1350), (-1, -1)), get_version_info().version_number[0:8],
                object_id=get_text_box_theme())
            # Adjust position
            version_number.set_position(
                (1600 - version_number.get_relative_rect()[2] - 8,
                1400 - version_number.get_relative_rect()[3]))
        else:
            version_number = pygame_gui.elements.UILabel(
                pygame.Rect((700, 650), (-1, -1)), get_version_info().version_number[0:8],
                object_id=get_text_box_theme())
            # Adjust position
            version_number.set_position(
                (800 - version_number.get_relative_rect()[2] - 8,
                700 - version_number.get_relative_rect()[3]))

        self.refresh_cat_images_and_info2()
        
        self.sub_screen = 'choose name'
        
        self.elements["random"] = UIImageButton(scale(pygame.Rect((570, 895), (68, 68))), "",
                                                object_id="#random_dice_button"
                                                , manager=MANAGER)

        self.elements["error"] = pygame_gui.elements.UITextBox("", scale(pygame.Rect((506, 1310), (596, -1))),
                                                               manager=MANAGER,
                                                               object_id="#default_dark", visible=False)
        self.main_menu.kill()
        self.main_menu = UIImageButton(scale(pygame.Rect((100, 100), (306, 60))), "", object_id="#main_menu_button"
                                       , manager=MANAGER)

        self.elements['previous_step'] = UIImageButton(scale(pygame.Rect((506, 1290), (294, 60))), "",
                                                       object_id="#previous_step_button", manager=MANAGER)
        self.elements['next_step'] = UIImageButton(scale(pygame.Rect((800, 1290), (294, 60))), "",
                                                   object_id="#next_step_button", manager=MANAGER)
        self.elements["name_entry"] = pygame_gui.elements.UITextEntryLine(scale(pygame.Rect((650, 900), (280, 58)))
                                                                          , manager=MANAGER, initial_text=self.your_cat.name.prefix)
        self.elements["name_entry"].set_allowed_characters(
            list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_- "))
        self.elements["name_entry"].set_text_length_limit(11)

        if game.settings['dark mode']:
            self.elements["clan"] = pygame_gui.elements.UITextBox("-kit",
                                                              scale(pygame.Rect((870, 905), (200, 50))),
                                                              object_id="#text_box_30_horizcenter_light",
                                                              manager=MANAGER)
        
        else:
            self.elements["clan"] = pygame_gui.elements.UITextBox("-kit",
                                                              scale(pygame.Rect((870, 905), (200, 50))),
                                                              object_id="#text_box_30_horizcenter",
                                                              manager=MANAGER)
            
    def clan_name_header(self):
        self.elements["name_backdrop"] = pygame_gui.elements.UIImage(
            scale(pygame.Rect((584, 200), (432, 100))),
            NewLifeScreen.clan_frame_img,
            manager=MANAGER,
        )
        self.elements["clan_name"] = pygame_gui.elements.UITextBox(
            game.clan.name + "Clan",
            scale(pygame.Rect((585, 212), (432, 100))),
            object_id="#text_box_30_horizcenter_light",
            manager=MANAGER,
        )

    def open_choose_leader(self):
        """Set up the screen for the choose leader phase."""
        self.clear_all_page()
        self.sub_screen = "choose leader"

        if game.settings['dark mode']:
            self.elements['background'] = pygame_gui.elements.UIImage(scale(pygame.Rect((500, 1000), (600, 70))),
                                                                  NewLifeScreen.leader_img_dark, manager=MANAGER)
        else:
            self.elements['background'] = pygame_gui.elements.UIImage(scale(pygame.Rect((500, 1000), (600, 70))),
                                                                  NewLifeScreen.leader_img, manager=MANAGER)

        self.elements["background"].disable()
        self.clan_name_header()

        # Roll_buttons
        x_pos = 310
        y_pos = 470
        self.elements["roll1"] = UIImageButton(
            scale(pygame.Rect((x_pos, y_pos), (68, 68))),
            "",
            object_id="#random_dice_button",
            manager=MANAGER,
        )
        y_pos += 80
        self.elements["roll2"] = UIImageButton(
            scale(pygame.Rect((x_pos, y_pos), (68, 68))),
            "",
            object_id="#random_dice_button",
            manager=MANAGER,
        )
        y_pos += 80
        self.elements["roll3"] = UIImageButton(
            scale(pygame.Rect((x_pos, y_pos), (68, 68))),
            "",
            object_id="#random_dice_button",
            manager=MANAGER,
        )

        _tmp = 160
        if self.rolls_left == -1:
            _tmp += 5
        self.elements["dice"] = UIImageButton(
            scale(pygame.Rect((_tmp, 870), (68, 68))),
            "",
            object_id="#random_dice_button",
            manager=MANAGER,
        )
        del _tmp
        self.elements["reroll_count"] = pygame_gui.elements.UILabel(
            scale(pygame.Rect((200, 880), (100, 50))),
            str(self.rolls_left),
            object_id=get_text_box_theme(""),
            manager=MANAGER,
        )

        if game.config["clan_creation"]["rerolls"] == 3:
            if self.rolls_left <= 2:
                self.elements["roll1"].disable()
            if self.rolls_left <= 1:
                self.elements["roll2"].disable()
            if self.rolls_left == 0:
                self.elements["roll3"].disable()
            self.elements["dice"].hide()
            self.elements["reroll_count"].hide()
        else:
            if self.rolls_left == 0:
                self.elements["dice"].disable()
            elif self.rolls_left == -1:
                self.elements["reroll_count"].hide()
            self.elements["roll1"].hide()
            self.elements["roll2"].hide()
            self.elements["roll3"].hide()

        # info for chosen cats:
        if game.settings['dark mode']:
            self.elements['cat_info'] = pygame_gui.elements.UITextBox("", scale(pygame.Rect((880, 450), (230, 300))),
                                                                    visible=False, object_id="#text_box_22_horizleft_spacing_95_dark",
                                                                    manager=MANAGER)
        else:
            self.elements['cat_info'] = pygame_gui.elements.UITextBox("", scale(pygame.Rect((880, 450), (230, 300))),
                                                                    visible=False, object_id=get_text_box_theme("#text_box_22_horizleft_spacing_95"),
                                                                    manager=MANAGER)
        self.elements['cat_name'] = pygame_gui.elements.UITextBox("", scale(pygame.Rect((300, 350), (1000, 110))),
                                                                  visible=False,
                                                                  object_id=get_text_box_theme(
                                                                      "#text_box_30_horizcenter"),
                                                                  manager=MANAGER)

        self.elements['select_cat'] = UIImageButton(scale(pygame.Rect((706, 720), (190, 60))),
                                                    "",
                                                    object_id="#recruit_button",
                                                    visible=False,
                                                    manager=MANAGER)
        

        # Next and previous buttons
        self.elements['previous_step'] = UIImageButton(scale(pygame.Rect((506, 1290), (294, 60))), "",
                                                       object_id="#previous_step_button", manager=MANAGER)
        self.elements['next_step'] = UIImageButton(scale(pygame.Rect((800, 1290), (294, 60))), "",
                                                   object_id="#next_step_button", manager=MANAGER)
        self.elements['next_step'].disable()

        self.elements['customize'] = UIImageButton(scale(pygame.Rect((100,200),(236,60))), "", object_id="#customize_button", manager=MANAGER,  tool_tip_text = "Customize your own cat")

        # draw cats to choose from
        self.refresh_cat_images_and_info()
    
    def randomize_custom_cat(self):
        pelts = list(Pelt.sprites_names.keys())
        pelts.remove("Tortie")
        pelts.remove("Calico")
        pelts_tortie = pelts.copy()
        pelts_tortie.remove("SingleColour")
        pelts_tortie.remove("TwoColour")
        # pelts_tortie.append("Single")
        permanent_conditions = ['born without a leg', 'weak leg', 'twisted leg', 'born without a tail', 'paralyzed', 'raspy lungs',
                                'wasting disease', 'blind', 'one bad eye', 'failing eyesight', 'partial hearing loss', 'deaf',
                                'constant joint pain', 'seizure prone', 'allergies', 'persistent headaches', 'born without an eye',
                                'born without eyes', 'mute']

        white_patches = ["FULLWHITE"] + Pelt.little_white + Pelt.mid_white + Pelt.high_white + Pelt.mostly_white
        self.pname= random.choice(pelts) if random.randint(1,3) == 1 else "Tortie"
        self.length=random.choice(["short", "medium", "long"])
        self.colour=random.choice(Pelt.pelt_colours)
        self.white_patches= choice(white_patches) if random.randint(1,2) == 1 else None
        self.eye_color=choice(Pelt.eye_colours)
        self.eye_colour2=choice(Pelt.eye_colours) if random.randint(1,10) == 1 else self.eye_color
        self.tortiebase=choice(Pelt.tortiebases)
        self.tortiecolour=choice(Pelt.pelt_colours)
        self.pattern=choice(Pelt.tortiepatterns)
        self.tortiepattern=choice(pelts_tortie)
        self.vitiligo=choice(Pelt.vit) if random.randint(1,5) == 1 else None
        self.points=choice(Pelt.point_markings) if random.randint(1,5) == 1 else None
        self.scars=[choice(Pelt.scars1 + Pelt.scars2 + Pelt.scars3)] if random.randint(1,10) == 1 else []
        self.tint=choice(["pink", "gray", "red", "orange", "black", "yellow", "purple", "blue","dilute","warmdilute","cooldilute"]) if random.randint(1,5) == 1 else None
        self.skin=choice(Pelt.skin_sprites)
        self.white_patches_tint=choice(["offwhite", "cream", "darkcream", "gray", "pink"]) if random.randint(1,5) == 1 else None
        self.reverse= False if random.randint(1,2) == 1 else True
        self.skill = random.choice(self.skills)
        self.sex = random.choice(["male", "female"])
        self.personality = choice(['troublesome', 'lonesome', 'impulsive', 'bullying', 'attention-seeker', 'charming', 'daring',
                                   'noisy', 'nervous', 'quiet', 'insecure', 'daydreamer', 'sweet', 'polite', 'know-it-all', 'bossy',
                                   'disciplined', 'patient', 'manipulative', 'secretive', 'rebellious', 'grumpy', 'passionate',
                                   'honest', 'leader-like', 'smug'])
        self.accessory = choice(Pelt.plant_accessories + Pelt.wild_accessories + Pelt.collars + Pelt.flower_accessories + Pelt.plant2_accessories + Pelt.snake_accessories + Pelt.smallAnimal_accessories + Pelt.deadInsect_accessories + Pelt.aliveInsect_accessories + Pelt.fruit_accessories + Pelt.crafted_accessories + Pelt.tail2_accessories + Pelt.np_autism) if random.randint(1,5) == 1 else None
        self.permanent_condition = choice(permanent_conditions) if random.randint(1,20) == 1 else None
        self.faith = random.choice(["flexible", "starclan", "dark forest", "neutral"])

        self.kitten_sprite=random.randint(0,2)
        self.adolescent_pose = random.randint(0,2)
        self.adult_pose = random.randint(0,2)
        self.elder_pose = random.randint(0,2)

    def open_customize_cat(self):
        self.clear_all_page()
        self.sub_screen = "customize cat"
        pelt2 = Pelt(
            name=self.pname,
            length=self.length,
            colour=self.colour,
            white_patches=self.white_patches,
            eye_color=self.eye_color,
            eye_colour2=self.eye_colour2,
            tortiebase=self.tortiebase,
            tortiecolour=self.tortiecolour,
            pattern=self.pattern,
            tortiepattern=Pelt.sprites_names.get(self.tortiepattern),
            vitiligo=self.vitiligo,
            points=self.points,
            accessory=None,
            paralyzed=self.paralyzed,
            scars=self.scars,
            tint=self.tint,
            skin=self.skin,
            white_patches_tint=self.white_patches_tint,
            kitten_sprite=self.kitten_sprite,
            adol_sprite=self.adolescent_pose if self.adolescent_pose > 2 else self.adolescent_pose + 3,
            adult_sprite=self.adult_pose if self.adult_pose > 2 else self.adult_pose + 6,
            senior_sprite=self.elder_pose if self.elder_pose > 2 else self.elder_pose + 12,
            reverse=self.reverse,
            accessories=[self.accessory] if self.accessory else [],
            inventory=[self.accessory] if self.accessory else []
        )
        if self.length == 'long' and self.adult_pose < 9:
            pelt2.cat_sprites['young adult'] = self.adult_pose + 9
            pelt2.cat_sprites['adult'] = self.adult_pose + 9
            pelt2.cat_sprites['senior adult'] = self.adult_pose + 9

        self.elements["left"] = UIImageButton(scale(pygame.Rect((950, 990), (102, 134))), "", object_id="#arrow_right_fancy",
                                                 starting_height=2)
        
        self.elements["right"] = UIImageButton(scale(pygame.Rect((1300, 990), (102, 134))), "", object_id="#arrow_left_fancy",
                                             starting_height=2)
        if self.page == 0:
            self.elements['left'].disable()
        else:
            self.elements['left'].enable()
        
        if self.page == 3:
            self.elements['right'].disable()
        else:
            self.elements['right'].enable()

       
        
        column1_x = 150  # x-coordinate for column 1
        column2_x = 450  # x-coordinate for column 2
        column3_x = 900  # x-coordinate for column 3
        column4_x = 1200
        x_align = 340
        x_align2 = 200
        x_align3 = 250
        y_pos = [80, 215, 280, 415, 480, 615, 680, 815, 880, 1015, 1080]


        self.elements['random_customize'] = UIImageButton(scale(pygame.Rect((240, y_pos[6]), (68, 68))), "", object_id="#random_dice_button", starting_height=2)
        

        pelts = list(Pelt.sprites_names.keys())
        pelts.remove("Tortie")
        pelts.remove("Calico")
        
        pelts_tortie = pelts.copy()
        # pelts_tortie.remove("SingleColour")
        pelts_tortie.remove("TwoColour")
        
        permanent_conditions = [
            'born without a leg', 'weak leg', 'twisted leg', 'born without a tail', 'paralyzed', 'raspy lungs', 'wasting disease',
            'blind', 'one bad eye', 'failing eyesight', 'partial hearing loss', 'deaf', 'constant joint pain', 'seizure prone',
            'allergies', 'persistent headaches', 'born without an eye', 'born without eyes', 'mute']

    # background images
    # values are ((x position, y position), (x width, y height))

        if game.settings['dark mode']:
            self.elements['spritebg'] = pygame_gui.elements.UIImage(scale(pygame.Rect((170, 220), (500, 570))),
                                                                  NewLifeScreen.sprite_preview_bg_dark, manager=MANAGER)
        else:
            self.elements['spritebg'] = pygame_gui.elements.UIImage(scale(pygame.Rect((170, 220), (500, 570))),
                                                                  NewLifeScreen.sprite_preview_bg, manager=MANAGER)
            
        if game.settings['dark mode']:
            self.elements['posesbg'] = pygame_gui.elements.UIImage(scale(pygame.Rect((100, 800), (650, 400))),
                                                                  NewLifeScreen.poses_bg_dark, manager=MANAGER)
        else:
            self.elements['posesbg'] = pygame_gui.elements.UIImage(scale(pygame.Rect((100, 800), (650, 400))),
                                                                  NewLifeScreen.poses_bg, manager=MANAGER)


        if game.settings['dark mode']:
            self.elements['choicesbg'] = pygame_gui.elements.UIImage(scale(pygame.Rect((850, 90), (650, 1150))),
                                                                  NewLifeScreen.choice_bg_dark, manager=MANAGER)
        else:
            self.elements['choicesbg'] = pygame_gui.elements.UIImage(scale(pygame.Rect((850, 90), (650, 1150))),
                                                                  NewLifeScreen.choice_bg, manager=MANAGER)


        self.elements['preview text'] = pygame_gui.elements.UITextBox(
                'Preview Age',
                scale(pygame.Rect((x_align, y_pos[5]),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
        self.elements['preview age'] = pygame_gui.elements.UIDropDownMenu(["kitten", "adolescent", "adult", "elder"], str(self.preview_age), scale(pygame.Rect((x_align, y_pos[6]), (260, 70))), manager=MANAGER)
        c_moons = 1
        if self.preview_age == "adolescent":
            c_moons = 6
        elif self.preview_age == "adult":
            c_moons = 12
        elif self.preview_age == "elder":
            c_moons = 121
        self.custom_cat = Cat(moons = c_moons, pelt=pelt2, loading_cat=True)
        self.custom_cat.sprite = generate_sprite(self.custom_cat)
        self.elements["sprite"] = UISpriteButton(scale(pygame.Rect
                                         ((250,280), (350, 350))),
                                   self.custom_cat.sprite,
                                   self.custom_cat.ID,
                                   starting_height=0, manager=MANAGER)
        
        self.elements['pose text'] = pygame_gui.elements.UITextBox(
                'Kitten Pose',
                scale(pygame.Rect((column1_x, y_pos[7] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
        self.elements['pose'] = pygame_gui.elements.UIDropDownMenu(["0", "1", "2"], str(self.kitten_sprite), scale(pygame.Rect((column1_x, y_pos[8]), (250, 70))), manager=MANAGER)
            
        self.elements['pose text2'] = pygame_gui.elements.UITextBox(
                'Adolescent Pose',
                scale(pygame.Rect((column2_x, y_pos[7] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
        self.elements['adolescent pose'] = pygame_gui.elements.UIDropDownMenu(["0", "1", "2"], str(self.adolescent_pose), scale(pygame.Rect((column2_x, y_pos[8]), (250, 70))), manager=MANAGER)

        self.elements['pose text3'] = pygame_gui.elements.UITextBox(
                'Adult Pose',
                scale(pygame.Rect((column1_x, y_pos[9] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
        self.elements['adult pose'] = pygame_gui.elements.UIDropDownMenu(["0", "1", "2"], str(self.adult_pose), scale(pygame.Rect((column1_x, y_pos[10]), (250, 70))), manager=MANAGER)

        self.elements['pose text4'] = pygame_gui.elements.UITextBox(
                'Elder Pose',
                scale(pygame.Rect((column2_x, y_pos[9] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
        self.elements['elder pose'] = pygame_gui.elements.UIDropDownMenu(["0", "1", "2"], str(self.elder_pose), scale(pygame.Rect((column2_x, y_pos[10]), (250, 70))), manager=MANAGER)


        # page 0
        # pose
        # pelt type 
        # pelt color
        # pelt tint
        # pelt length
        # White patches
        # White patches tint
        
        if self.page == 0:

        
            #page 1 dropdown labels

            self.elements['pelt text'] = pygame_gui.elements.UITextBox(
                'Pelt type',
                scale(pygame.Rect((column4_x, y_pos[3] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
            if self.pname == "Tortie":
                self.elements['pelt dropdown'] = pygame_gui.elements.UIDropDownMenu(pelts, "SingleColour", scale(pygame.Rect((column4_x, y_pos[4]),(250,70))), manager=MANAGER)
            else:
                self.elements['pelt dropdown'] = pygame_gui.elements.UIDropDownMenu(pelts, str(self.pname), scale(pygame.Rect((column4_x, y_pos[4]),(250,70))), manager=MANAGER)
            if self.pname == "Tortie":
                self.elements['pelt dropdown'].disable()
            else:
                self.elements['pelt dropdown'].enable()
            self.elements['pelt color text'] = pygame_gui.elements.UITextBox(
                'Pelt color',
                scale(pygame.Rect((column3_x, y_pos[1] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )        
            self.elements['pelt color'] = pygame_gui.elements.UIDropDownMenu(Pelt.pelt_colours, str(self.colour), scale(pygame.Rect((column3_x, y_pos[2]),(250,70))), manager=MANAGER)
            
            self.elements['tint text'] = pygame_gui.elements.UITextBox(
                'Tint',
                scale(pygame.Rect((column4_x, y_pos[1] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
            if self.tint:
                self.elements['tint'] = pygame_gui.elements.UIDropDownMenu(["pink", "gray", "red", "orange", "black", "yellow", "purple", "blue", "None","dilute","warmdilute","cooldilute"], str(self.tint), scale(pygame.Rect((column4_x, y_pos[2]), (250, 70))), manager=MANAGER)
            else:
                self.elements['tint'] = pygame_gui.elements.UIDropDownMenu(["pink", "gray", "red", "orange", "black", "yellow", "purple", "blue",  "None","dilute","warmdilute","cooldilute"], "None", scale(pygame.Rect((column4_x, y_pos[2]), (250, 70))), manager=MANAGER)
            
            self.elements['pelt length text'] = pygame_gui.elements.UITextBox(
                'Pelt length',
                scale(pygame.Rect((column3_x, y_pos[3] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
            self.elements['pelt length'] = pygame_gui.elements.UIDropDownMenu(Pelt.pelt_length, str(self.length), scale(pygame.Rect((column3_x, y_pos[4]), (250, 70))), manager=MANAGER)

            self.elements['white patch text'] = pygame_gui.elements.UITextBox(
                'White patches',
                scale(pygame.Rect((column3_x, y_pos[5] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
            if self.white_patches:
                self.elements['white patches'] = pygame_gui.elements.UIDropDownMenu(["None", "FULLWHITE"] + Pelt.little_white + Pelt.mid_white + Pelt.high_white + Pelt.mostly_white, str(self.white_patches), scale(pygame.Rect((column3_x, y_pos[6]),(250,70))), manager=MANAGER)
            else:
                self.elements['white patches'] = pygame_gui.elements.UIDropDownMenu(["None", "FULLWHITE"] + Pelt.little_white + Pelt.mid_white + Pelt.high_white + Pelt.mostly_white, "None", scale(pygame.Rect((column3_x, y_pos[6]),(250,70))), manager=MANAGER)
            self.elements['white patch tint text'] = pygame_gui.elements.UITextBox(
                'Patches tint',
                scale(pygame.Rect((column4_x, y_pos[5] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
            if self.white_patches_tint:
                self.elements['white_patches_tint'] = pygame_gui.elements.UIDropDownMenu(["None"] + ["offwhite", "cream", "darkcream", "gray", "pink"], str(self.white_patches_tint), scale(pygame.Rect((column4_x, y_pos[6]), (250, 70))), manager=MANAGER)
            else:
                self.elements['white_patches_tint'] = pygame_gui.elements.UIDropDownMenu(["None"] + ["offwhite", "cream", "darkcream", "gray", "pink"], "None", scale(pygame.Rect((column4_x, y_pos[6]), (250, 70))), manager=MANAGER)

            self.elements['eye color text'] = pygame_gui.elements.UITextBox(
                'Eye color',
                scale(pygame.Rect((column3_x, y_pos[7] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
            self.elements['eye color'] = pygame_gui.elements.UIDropDownMenu(
                Pelt.eye_colours, str(self.eye_color),
                scale(pygame.Rect((column3_x, y_pos[8]),(250,70))), manager=MANAGER)

            self.elements['eye color2 text'] = pygame_gui.elements.UITextBox(
                'Eye color 2',
                scale(pygame.Rect((column4_x, y_pos[7] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
            if self.eye_colour2:
                self.elements['eye color2'] = pygame_gui.elements.UIDropDownMenu(Pelt.eye_colours, str(self.eye_colour2), scale(pygame.Rect((column4_x, y_pos[8]),(250,70))), manager=MANAGER)
            else:
                self.elements['eye color2'] = pygame_gui.elements.UIDropDownMenu(Pelt.eye_colours, str(self.eye_colour), scale(pygame.Rect((column4_x, y_pos[8]),(250,70))), manager=MANAGER)

        #page 1
        #tortie
        #tortie pattern
        #tortie base
        #tortie color
        #tortie pattern2
                
        elif self.page == 1:
            self.elements['tortie text'] = pygame_gui.elements.UITextBox(
                'Tortie:',
                scale(pygame.Rect((column3_x, y_pos[2] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
            self.elements['base text'] = pygame_gui.elements.UITextBox(
                'Base',
                scale(pygame.Rect((column3_x, y_pos[3] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
            
            self.elements['tortie color text'] = pygame_gui.elements.UITextBox(
                'Color',
                scale(pygame.Rect((column3_x, y_pos[5] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
            self.elements['pattern text'] = pygame_gui.elements.UITextBox(
                'Type',
                scale(pygame.Rect((column4_x, y_pos[5] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
            self.elements['tint text2'] = pygame_gui.elements.UITextBox(
                'Pattern',
                scale(pygame.Rect((column4_x, y_pos[3] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )

            # page 1 dropdowns

            if self.pname == "Tortie":
                self.elements['tortie'] = pygame_gui.elements.UIDropDownMenu(["Yes", "No"], "Yes", scale(pygame.Rect((column4_x, y_pos[2]), (250, 70))), manager=MANAGER)
            else:
                self.elements['tortie'] = pygame_gui.elements.UIDropDownMenu(["Yes", "No"], "No", scale(pygame.Rect((column4_x, y_pos[2]), (250, 70))), manager=MANAGER)

            if self.tortiebase:
                self.elements['tortiebase'] = pygame_gui.elements.UIDropDownMenu(Pelt.tortiebases, str(self.tortiebase), scale(pygame.Rect((column3_x, y_pos[4]), (250, 70))), manager=MANAGER)
            else:
                self.elements['tortiebase'] = pygame_gui.elements.UIDropDownMenu(Pelt.tortiebases, "single", scale(pygame.Rect((column3_x, y_pos[4]), (250, 70))), manager=MANAGER)

            if self.pattern:
                self.elements['pattern'] = pygame_gui.elements.UIDropDownMenu(Pelt.tortiepatterns, str(self.pattern), scale(pygame.Rect((column4_x, y_pos[4]), (250, 70))), manager=MANAGER)
            else:
                self.elements['pattern'] = pygame_gui.elements.UIDropDownMenu(Pelt.tortiepatterns, "ONE", scale(pygame.Rect((column4_x, y_pos[4]), (250, 70))), manager=MANAGER)
            if self.tortiecolour:
                self.elements['tortiecolor'] = pygame_gui.elements.UIDropDownMenu(Pelt.pelt_colours, str(self.tortiecolour), scale(pygame.Rect((column3_x, y_pos[6]), (250, 70))), manager=MANAGER)
            else:
                self.elements['tortiecolor'] = pygame_gui.elements.UIDropDownMenu(Pelt.pelt_colours, "GINGER", scale(pygame.Rect((column3_x, y_pos[6]), (250, 70))), manager=MANAGER)
            if self.tortiepattern:
                self.elements['tortiepattern'] = pygame_gui.elements.UIDropDownMenu(pelts_tortie, str(self.tortiepattern), scale(pygame.Rect((column4_x, y_pos[6]), (250, 70))), manager=MANAGER)
            else:
                self.elements['tortiepattern'] = pygame_gui.elements.UIDropDownMenu(pelts_tortie, "SingleColour", scale(pygame.Rect((column4_x, y_pos[6]), (250, 70))), manager=MANAGER)

            if self.pname != "Tortie":
                self.elements['pattern'].disable()
                self.elements['tortiebase'].disable()
                self.elements['tortiecolor'].disable()
                self.elements['tortiepattern'].disable()
            else:
                self.elements['pattern'].enable()
                self.elements['tortiebase'].enable()
                self.elements['tortiecolor'].enable()
                self.elements['tortiepattern'].enable()

            self.elements['vit text'] = pygame_gui.elements.UITextBox(
                'Vitiligo',
                scale(pygame.Rect((column3_x, y_pos[7] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
            self.elements['point text'] = pygame_gui.elements.UITextBox(
                'Points',
                scale(pygame.Rect((column4_x, y_pos[7] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
            if self.vitiligo:
                self.elements['vitiligo'] = pygame_gui.elements.UIDropDownMenu(["None"] + Pelt.vit, str(self.vitiligo), scale(pygame.Rect((column3_x, y_pos[8]), (250, 70))), manager=MANAGER)
            else:
                self.elements['vitiligo'] = pygame_gui.elements.UIDropDownMenu(["None"] + Pelt.vit, "None", scale(pygame.Rect((column3_x, y_pos[8]), (250, 70))), manager=MANAGER)
            
            if self.points:
                self.elements['points'] = pygame_gui.elements.UIDropDownMenu(["None"] + Pelt.point_markings, str(self.points), scale(pygame.Rect((column4_x, y_pos[8]), (250, 70))), manager=MANAGER)
            else:
                self.elements['points'] = pygame_gui.elements.UIDropDownMenu(["None"] + Pelt.point_markings, "None", scale(pygame.Rect((column4_x, y_pos[8]), (250, 70))), manager=MANAGER)
            

        elif self.page == 2:
            self.elements['skin text'] = pygame_gui.elements.UITextBox(
                'Skin',
                scale(pygame.Rect((column3_x, y_pos[1] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
            self.elements['scar text'] = pygame_gui.elements.UITextBox(
                'Scar',
                scale(pygame.Rect((column3_x, y_pos[3] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            ) 
            self.elements['accessory text'] = pygame_gui.elements.UITextBox(
                'Accessory',
                scale(pygame.Rect((column4_x, y_pos[1] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            
            )
            self.elements['permanent condition text'] = pygame_gui.elements.UITextBox(
                'Condition',
                scale(pygame.Rect((column4_x, y_pos[3] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )

            self.elements['sex text'] = pygame_gui.elements.UITextBox(
                'Sex',
                scale(pygame.Rect((column3_x, y_pos[5] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
            self.elements['personality text'] = pygame_gui.elements.UITextBox(
                'Kit Personality',
                scale(pygame.Rect((column4_x, y_pos[5] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )

            self.elements['reverse text'] = pygame_gui.elements.UITextBox(
                'Reverse',
                scale(pygame.Rect((column3_x, y_pos[7] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER)
            
            self.elements['skills text'] = pygame_gui.elements.UITextBox(
                'Skill',
                scale(pygame.Rect((column4_x, y_pos[7] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER)
            
            # page 2 dropdowns
            
            self.elements['skin'] = pygame_gui.elements.UIDropDownMenu(Pelt.skin_sprites, str(self.skin), scale(pygame.Rect((column3_x, y_pos[2]), (250, 70))), manager=MANAGER)

            if self.scars:
                self.elements['scars'] = pygame_gui.elements.UIDropDownMenu(["None"] + Pelt.scars1 + Pelt.scars2 + Pelt.scars3, str(self.scars[0]), scale(pygame.Rect((column3_x, y_pos[4]), (250, 70))), manager=MANAGER)
            else:
                self.elements['scars'] = pygame_gui.elements.UIDropDownMenu(["None"] + Pelt.scars1 + Pelt.scars2 + Pelt.scars3, "None", scale(pygame.Rect((column3_x, y_pos[4]), (250, 70))), manager=MANAGER)

            if self.accessory:
                self.elements['accessory'] = pygame_gui.elements.UIDropDownMenu(["None"] + Pelt.plant_accessories + Pelt.wild_accessories + Pelt.collars + Pelt.flower_accessories + Pelt.plant2_accessories + Pelt.snake_accessories + Pelt.smallAnimal_accessories + Pelt.deadInsect_accessories + Pelt.aliveInsect_accessories + Pelt.fruit_accessories + Pelt.crafted_accessories + Pelt.tail2_accessories + Pelt.np_autism, str(self.accessory), scale(pygame.Rect((1150, y_pos[2]), (300, 70))), manager=MANAGER)
            else:
                self.elements['accessory'] = pygame_gui.elements.UIDropDownMenu(["None"] + Pelt.plant_accessories + Pelt.wild_accessories + Pelt.collars + Pelt.flower_accessories + Pelt.plant2_accessories + Pelt.snake_accessories + Pelt.smallAnimal_accessories + Pelt.deadInsect_accessories + Pelt.aliveInsect_accessories + Pelt.fruit_accessories + Pelt.crafted_accessories + Pelt.tail2_accessories + Pelt.np_autism, "None", scale(pygame.Rect((1150, y_pos[2]), (300, 70))), manager=MANAGER)

            if self.permanent_condition:
                self.elements['permanent conditions'] = pygame_gui.elements.UIDropDownMenu(
                    ["None"] + permanent_conditions,
                    str(self.permanent_condition),
                    scale(pygame.Rect((1150, y_pos[4]), (300, 70))), manager=MANAGER)
            else:
                self.elements['permanent conditions'] = pygame_gui.elements.UIDropDownMenu(
                    ["None"] + permanent_conditions,
                    "None", scale(pygame.Rect((1150, y_pos[4]), (300, 70))), manager=MANAGER)

            self.elements['sex'] = pygame_gui.elements.UIDropDownMenu(['male', 'female'], str(self.sex), scale(pygame.Rect((column3_x, y_pos[6]), (250, 70))), manager=MANAGER)

            self.elements['personality'] = pygame_gui.elements.UIDropDownMenu([
                'troublesome', 'lonesome', 'impulsive', 'bullying', 'attention-seeker', 'charming', 'daring', 'noisy', 'nervous',
                'quiet', 'insecure', 'daydreamer', 'sweet', 'polite', 'know-it-all', 'bossy', 'disciplined', 'patient',
                'manipulative', 'secretive', 'rebellious', 'grumpy', 'passionate', 'honest', 'leader-like', 'smug'],
                str(self.personality), scale(pygame.Rect((1150, y_pos[6]), (300, 70))), manager=MANAGER)

            if self.reverse:
                self.elements['reverse'] = pygame_gui.elements.UIDropDownMenu(["Yes", "No"], "Yes", scale(pygame.Rect((column3_x, y_pos[8]), (250, 70))), manager=MANAGER)
            else:
                self.elements['reverse'] = pygame_gui.elements.UIDropDownMenu(["Yes", "No"], "No", scale(pygame.Rect((column3_x, y_pos[8]), (250, 70))), manager=MANAGER)

            if self.skill:
                self.elements['skills'] = pygame_gui.elements.UIDropDownMenu(["Random"] + self.skills, self.skill, scale(pygame.Rect((1150, y_pos[8]), (300, 70))), manager=MANAGER)
            else:
                self.elements['skills'] = pygame_gui.elements.UIDropDownMenu(["Random"] + self.skills, "Random", scale(pygame.Rect((1150, y_pos[8]), (300, 70))), manager=MANAGER)

        elif self.page == 3:
            self.elements['faith text'] = pygame_gui.elements.UITextBox(
                'Faith',
                scale(pygame.Rect((column3_x, y_pos[1] ),(1200,-1))),
                object_id=get_text_box_theme("#text_box_30_horizleft"), manager=MANAGER
            )
            
            # page 2 dropdowns
            
            self.elements['faith'] = pygame_gui.elements.UIDropDownMenu(["flexible", "starclan", "neutral", "dark forest"], str(self.faith), scale(pygame.Rect((column3_x, y_pos[2]), (250, 70))), manager=MANAGER)

        
        self.elements['previous_step'] = UIImageButton(scale(pygame.Rect((506, 1250), (294, 60))), "",
                                                    object_id="#previous_step_button", manager=MANAGER)
        self.elements['next_step'] = UIImageButton(scale(pygame.Rect((800, 1250), (294, 60))), "",
                                                    object_id="#next_step_button", manager=MANAGER)
        

                
    def handle_customize_cat_event(self, event):
        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.elements['preview age']:
                self.preview_age = event.text
                self.update_sprite()
            if self.page == 0:
                if event.ui_element == self.elements['pelt dropdown']:
                    self.pname = event.text
                    self.update_sprite()
                elif event.ui_element == self.elements['pelt color']:
                    self.colour = event.text
                    self.update_sprite()
                if event.ui_element == self.elements['pelt length']:
                    self.length = event.text
                    self.update_sprite()
                elif event.ui_element == self.elements['tint']:
                    if event.text == "None":
                        self.tint = None
                    else:
                        self.tint = event.text
                    self.update_sprite()
                elif event.ui_element == self.elements['pose']:
                    self.kitten_sprite = int(event.text)
                    self.update_sprite()
                elif event.ui_element == self.elements['adolescent pose']:
                    self.adolescent_pose = int(event.text)
                    self.update_sprite()
                elif event.ui_element == self.elements['adult pose']:
                    if self.length in ['short', 'medium']:
                        self.adult_pose = int(event.text)
                    elif self.length == 'long':
                        self.adult_pose = int(event.text)
                    self.update_sprite()
                elif event.ui_element == self.elements['elder pose']:
                    self.elder_pose = int(event.text)
                    self.update_sprite()
                elif event.ui_element == self.elements['white patches']:
                    if event.text == "None":
                        self.white_patches = None
                    else:
                        self.white_patches = event.text
                    self.update_sprite()
                elif event.ui_element == self.elements['white_patches_tint']:
                    if event.text == "None":
                        self.white_patches_tint = None
                    else:
                        self.white_patches_tint = event.text
                    self.update_sprite()
            
                if event.ui_element == self.elements['eye color']:
                    self.eye_color = event.text
                    self.update_sprite()
                elif event.ui_element == self.elements['eye color2']:
                    self.eye_colour2 = event.text
                    self.update_sprite() 
            
            elif self.page == 1:
                if event.ui_element == self.elements['tortie']:
                    if event.text == "Yes":
                        self.pname = "Tortie"
                        # self.elements['pelt dropdown'].disable()
                        self.elements['pattern'].enable()
                        self.elements['tortiebase'].enable()
                        self.elements['tortiecolor'].enable()
                        self.elements['tortiepattern'].enable()
                        
                        self.pattern = "ONE"
                        self.tortiepattern = "Bengal"
                        self.tortiebase = "single"
                        self.tortiecolour = "GINGER"
                    else:
                        self.pname = "SingleColour"
                        self.elements['pattern'].disable()
                        self.elements['tortiebase'].disable()
                        self.elements['tortiecolor'].disable()
                        self.elements['tortiepattern'].disable()
                        self.pattern = None
                        self.tortiebase = None
                        self.tortiepattern = None
                        self.tortiecolour = None
                    self.update_sprite()
                elif event.ui_element == self.elements['tortiecolor']:
                    self.tortiecolour = event.text
                    self.update_sprite()
                elif event.ui_element == self.elements['pattern']:
                    self.pattern = event.text
                    self.update_sprite()
                elif event.ui_element == self.elements['tortiepattern']:
                    self.tortiepattern = event.text
                    self.update_sprite()
                elif event.ui_element == self.elements['tortiebase']:
                    self.tortiebase = event.text
                    self.update_sprite()
                if event.ui_element == self.elements['vitiligo']:
                    if event.text == "None":
                        self.vitiligo = None
                    else:
                        self.vitiligo = event.text
                    self.update_sprite()
                elif event.ui_element == self.elements['points']:
                    if event.text == "None":
                        self.points = None
                    else:
                        self.points = event.text
                    self.update_sprite()
                elif event.ui_element == self.elements['pose']:
                    self.kitten_sprite = int(event.text)
                    self.update_sprite()
                elif event.ui_element == self.elements['adolescent pose']:
                    self.adolescent_pose = int(event.text)
                    self.update_sprite()
                elif event.ui_element == self.elements['adult pose']:
                    if self.length in ['short', 'medium']:
                        self.adult_pose = int(event.text)
                    elif self.length == 'long':
                        self.adult_pose = int(event.text)
                    self.update_sprite()
                elif event.ui_element == self.elements['elder pose']:
                    self.elder_pose = int(event.text)
                    self.update_sprite()
                
            elif self.page == 2:
                
                if event.ui_element == self.elements['scars']:
                    if event.text == "None":
                        if "NOTAIL" in self.custom_cat.pelt.scars:
                            self.scars = []
                            self.scars.append('NOTAIL')
                        elif "NOPAW" in self.custom_cat.pelt.scars:
                            self.scars = []
                            self.scars.append('NOPAW')
                        else:
                            self.scars = []
                    else:
                        if "NOTAIL" in self.custom_cat.pelt.scars:
                            self.scars = []
                            self.scars.append('NOTAIL')
                        elif "NOPAW" in self.custom_cat.pelt.scars:
                            self.scars = []
                            self.scars.append('NOPAW')
                        else:
                            self.scars = []
                        self.scars.append(event.text)
                    self.update_sprite()
                elif event.ui_element == self.elements['skin']:
                    self.skin = event.text
                    self.update_sprite()
                elif event.ui_element == self.elements['reverse']:
                    self.reverse = (event.text == "Yes")
                    self.update_sprite()
                elif event.ui_element == self.elements['accessory']:
                    if event.text == "None":
                        self.accessory = None
                    else:
                        self.accessory = event.text
                    self.update_sprite()
                elif event.ui_element == self.elements['permanent conditions']:
                    if event.text == "None":
                        self.permanent_condition = None
                        self.paralyzed = False
                        if "NOTAIL" in self.scars:
                            self.scars.remove("NOTAIL")
                        elif "NOPAW" in self.scars:
                            self.scars.remove("NOPAW")
                        self.update_sprite()
                    else:
                        self.permanent_condition = event.text

                        # PARALYZED
                        if event.text == 'paralyzed':
                            self.paralyzed = True
                            self.update_sprite()
                        else:
                            self.paralyzed = False
                        
                        # SCARS
                        if event.text == 'born without a leg' and 'NOPAW' not in self.custom_cat.pelt.scars:
                            self.scars.append('NOPAW')
                        elif event.text == "born without a tail" and "NOTAIL" not in self.custom_cat.pelt.scars:
                            self.scars.append('NOTAIL')
                        else:
                            if "NOTAIL" in self.scars:
                                self.scars.remove("NOTAIL")
                            elif "NOPAW" in self.scars:
                                self.scars.remove("NOPAW")
                        
                        # EYES
                        #if event.text == 'born without an eye':
                        #    self.eye_color = 'MISSING'
                        # starting framework for the future. that is.

                        self.update_sprite()

                elif event.ui_element == self.elements['sex']:
                    self.sex = event.text

                elif event.ui_element == self.elements['personality']:
                    self.personality = event.text
                elif event.ui_element == self.elements['pose']:
                    self.kitten_sprite = int(event.text)
                    self.update_sprite()
                elif event.ui_element == self.elements['adolescent pose']:
                    self.adolescent_pose = int(event.text)
                    self.update_sprite()
                elif event.ui_element == self.elements['adult pose']:
                    if self.length in ['short', 'medium']:
                        self.adult_pose = int(event.text)
                    elif self.length == 'long':
                        self.adult_pose = int(event.text)
                    self.update_sprite()
                elif event.ui_element == self.elements['elder pose']:
                    self.elder_pose = int(event.text)
                    self.update_sprite()
                elif event.ui_element == self.elements['skills']:
                    self.skill = event.text
            elif self.page == 3:
                if event.ui_element == self.elements['faith']:
                    self.faith = event.text
        
        elif event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.main_menu:
                self.change_screen('start screen')
            elif event.ui_element == self.elements['right']:
                if self.page < 5:
                    self.page += 1
                    self.open_customize_cat()
            elif event.ui_element == self.elements['left']:
                if self.page > 0:
                    self.page -= 1
                    self.open_customize_cat()
            elif event.ui_element == self.elements['random_customize']:
                self.randomize_custom_cat()
                self.open_customize_cat()
            elif event.ui_element == self.elements['next_step']:
                new_cat = Cat(moons = 1)
                new_cat.pelt = self.custom_cat.pelt
                new_cat.gender = self.sex
                new_cat.genderalign = self.sex

                if new_cat.genderalign == "male":
                    new_cat.pronouns = [Cat.default_pronouns[2].copy()]
                elif new_cat.genderalign == "female":
                    new_cat.pronouns = [Cat.default_pronouns[1].copy()]
                else:
                    new_cat.pronouns = [Cat.default_pronouns[0].copy()]
                    
                self.your_cat = new_cat
                if self.permanent_condition is not None and self.permanent_condition != 'paralyzed':
                    self.your_cat.get_permanent_condition(self.permanent_condition, born_with=True)
                    self.your_cat.permanent_condition[self.permanent_condition]["moons_until"] = 1
                    self.your_cat.permanent_condition[self.permanent_condition]["moons_with"] = -1
                    self.your_cat.permanent_condition[self.permanent_condition]['born_with'] = True
                if self.paralyzed and 'paralyzed' not in self.your_cat.permanent_condition:
                    self.your_cat.get_permanent_condition('paralyzed')
                    self.your_cat.permanent_condition['paralyzed']["moons_until"] = 1
                    self.your_cat.permanent_condition['paralyzed']["moons_with"] = -1
                    self.your_cat.permanent_condition['paralyzed']['born_with'] = True
                if self.permanent_condition is not None and self.permanent_condition == "born without a tail" and "NOTAIL" not in self.your_cat.pelt.scars:
                    self.your_cat.pelt.scars.append('NOTAIL')
                    self.your_cat.permanent_condition['born without a tail']["moons_until"] = 1
                    self.your_cat.permanent_condition['born without a tail']["moons_with"] = -1
                    self.your_cat.permanent_condition['born without a tail']['born_with'] = True
                elif self.permanent_condition is not None and self.permanent_condition == "born without a leg" and "NOPAW" not in self.your_cat.pelt.scars:
                    self.your_cat.pelt.scars.append('NOPAW')
                    self.your_cat.permanent_condition['born without a leg']["moons_until"] = 1
                    self.your_cat.permanent_condition['born without a leg']["moons_with"] = -1
                    self.your_cat.permanent_condition['born without a leg']['born_with'] = True
                self.your_cat.pelt.accessories = [self.accessory] if self.accessory else []
                self.your_cat.pelt.inventory = [self.accessory] if self.accessory else []
                self.your_cat.personality = Personality(trait=self.personality, kit_trait=True)
                if self.skill == "Random":
                    self.skill = random.choice(self.skills)
                self.your_cat.skills.primary = Skill.get_skill_from_string(Skill, self.skill)
                self.your_cat.lock_faith = self.faith
                self.selected_cat = None
                self.open_name_cat()
            elif event.ui_element == self.elements['previous_step']:
                self.open_choose_leader()

    def update_sprite(self):
        pelt2 = Pelt(
            name=self.pname,
            length=self.length,
            colour=self.colour,
            white_patches=self.white_patches,
            eye_color=self.eye_color,
            eye_colour2=self.eye_colour2,
            tortiebase=self.tortiebase,
            tortiecolour=self.tortiecolour,
            pattern=self.pattern,
            tortiepattern=Pelt.sprites_names.get(self.tortiepattern),
            vitiligo=self.vitiligo,
            points=self.points,
            accessory=None,
            paralyzed=self.paralyzed,
            scars=self.scars,
            tint=self.tint,
            skin=self.skin,
            white_patches_tint=self.white_patches_tint,
            kitten_sprite=self.kitten_sprite,
            adol_sprite=self.adolescent_pose if self.adolescent_pose > 2 else self.adolescent_pose + 3,
            adult_sprite=self.adult_pose if self.adult_pose > 2 else self.adult_pose + 6,
            senior_sprite=self.elder_pose if self.elder_pose > 2 else self.elder_pose + 12,
            reverse=self.reverse,
            accessories=[self.accessory] if self.accessory else [],
            inventory=[self.accessory] if self.accessory else []
        )
        if self.length == 'long' and self.adult_pose < 9:
            pelt2.cat_sprites['young adult'] = self.adult_pose + 9
            pelt2.cat_sprites['adult'] = self.adult_pose + 9
            pelt2.cat_sprites['senior adult'] = self.adult_pose + 9
        c_moons = 1
        if self.preview_age == "adolescent":
            c_moons = 6
        elif self.preview_age == "adult":
            c_moons = 12
        elif self.preview_age == "elder":
            c_moons = 121
        self.custom_cat = Cat(moons = c_moons, pelt=pelt2, loading_cat=True)

        self.custom_cat.sprite = generate_sprite(self.custom_cat)
        self.elements['sprite'].kill()
        self.elements["sprite"] = UISpriteButton(scale(pygame.Rect
                                        ((250,280), (350, 350))),
                                self.custom_cat.sprite,
                                self.custom_cat.ID,
                                starting_height=0, manager=MANAGER)
        
    def open_clan_saved_screen(self):
        self.clear_all_page()

        self.sub_screen = 'saved screen'

        # self.elements["selected_symbol"] = pygame_gui.elements.UIImage(
        #     scale(pygame.Rect((700, 210), (200, 200))),
        #     pygame.transform.scale(
        #         sprites.sprites[self.symbol_selected], (200, 200)
        #     ).convert_alpha(),
        #     object_id="#selected_symbol",
        #     starting_height=1,
        #     manager=MANAGER,
        # )

        self.elements["leader_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((700, 240), (200, 200))),
                                                                    pygame.transform.scale(
                                                                        self.your_cat.sprite,
                                                                        (200, 200)), manager=MANAGER)
        self.elements["continue"] = UIImageButton(scale(pygame.Rect((692, 600), (204, 60))), "",
                                                  object_id="#continue_button_small")
        self.elements["save_confirm"] = pygame_gui.elements.UITextBox('Welcome to the world, ' + self.your_cat.name.prefix + 'kit!',
                                                                    scale(pygame.Rect((200, 470), (1200, 60))),
                                                                    object_id=get_text_box_theme(
                                                                        "#text_box_30_horizcenter"),
                                                                    manager=MANAGER)

    def save_clan(self):
        self.your_cat.create_inheritance_new_cat()
        game.clan.your_cat = self.your_cat
        game.clan.your_cat.moons = -1
        game.clan.add_cat(game.clan.your_cat)
        game.cur_events_list.clear()
        game.herb_events_list.clear()
        self.delete_example_cats()
        Cat.grief_strings.clear()
        Cat.sort_cats()

    def delete_example_cats(self):
        key_copy = tuple(Cat.all_cats.keys())
        for i in key_copy:  # Going through all currently existing cats
            # cat_class is a Cat-object
            if i not in [game.clan.your_cat.ID] + self.current_members:
                Cat.all_cats[i].example = True
                self.remove_cat(Cat.all_cats[i].ID)

    def remove_cat(self, ID):  # ID is cat.ID
        """
        This function is for completely removing the cat from the game,
        it's not meant for a cat that's simply dead
        """

        if Cat.all_cats[ID] in Cat.all_cats_list:
            Cat.all_cats_list.remove(Cat.all_cats[ID])

        if ID in Cat.all_cats:
            Cat.all_cats.pop(ID)

        if ID in game.clan.clan_cats:
            game.clan.clan_cats.remove(ID)
        if ID in game.clan.starclan_cats:
            game.clan.starclan_cats.remove(ID)
        if ID in game.clan.unknown_cats:
            game.clan.unknown_cats.remove(ID)
        if ID in game.clan.darkforest_cats:
            game.clan.darkforest_cats.remove(ID)