import pygame.transform
import pygame_gui.elements
from random import choice, randint
import ujson

from scripts.cat_relations.inheritance import Inheritance
from scripts.cat.history import History
from scripts.event_class import Single_Event
from scripts.events import events_class

from .Screens import Screens

from scripts.utility import get_personality_compatibility, get_text_box_theme, scale, scale_dimentions, shorten_text_to_fit
from scripts.cat.cats import Cat
from scripts.game_structure import image_cache
from scripts.cat.pelts import Pelt
from scripts.game_structure.windows import GameOver, PickPath, DeathScreen
from scripts.game_structure.game_essentials import game, screen, screen_x, screen_y, MANAGER
from scripts.game_structure.windows import RelationshipLog
from scripts.game_structure.propagating_thread import PropagatingThread
from scripts.game_structure.ui_elements import UIImageButton, UITextBoxTweaked, UISpriteButton

class ChooseRebornScreen(Screens):
    selected_cat = None
    current_page = 1
    list_frame = pygame.transform.scale(image_cache.load_image("resources/images/choosing_frame.png").convert_alpha(),
                                        (1300 / 1600 * screen_x, 452 / 1400 * screen_y))
    apprentice_details = {}
    selected_details = {}
    cat_list_buttons = {}

    def __init__(self, name=None):
        super().__init__(name)
        self.fav = {}
        self.list_page = None
        self.next_cat = None
        self.previous_cat = None
        self.next_page_button = None
        self.previous_page_button = None
        self.current_mentor_warning = None
        self.confirm_mentor = None
        self.back_button = None
        self.next_cat_button = None
        self.previous_cat_button = None
        self.mentor_icon = None
        self.app_frame = None
        self.mentor_frame = None
        self.current_mentor_text = None
        self.info = None
        self.heading = None
        self.mentor = None
        self.the_cat = None
        self.dead_tab = None
        self.alive_tab = None
        self.current_list = "alive"

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element in self.cat_list_buttons.values():
                self.selected_cat = event.ui_element.return_cat_object()
                self.update_selected_cat()
                # self.update_buttons()
            elif event.ui_element == self.confirm_mentor and self.selected_cat:
                self.update_selected_cat()
                self.change_cat(self.selected_cat)
                if not self.selected_cat.dead:
                    game.switches['continue_after_death'] = False
                else:
                    game.switches['continue_after_death'] = True

                # self.update_buttons()
            elif event.ui_element == self.back_button:
                self.change_screen('events screen')
                game.switches['continue_after_death'] = False
            elif event.ui_element == self.next_cat_button:
                if isinstance(Cat.fetch_cat(self.next_cat), Cat):
                    game.switches['cat'] = self.next_cat
                    self.update_cat_list()
                    self.update_selected_cat()
                    # self.update_buttons()
                else:
                    print("invalid next cat", self.next_cat)
            elif event.ui_element == self.previous_cat_button:
                if isinstance(Cat.fetch_cat(self.previous_cat), Cat):
                    game.switches['cat'] = self.previous_cat
                    self.update_cat_list()
                    self.update_selected_cat()
                    # self.update_buttons()
                else:
                    print("invalid previous cat", self.previous_cat)
            elif event.ui_element == self.dead_tab:
                self.current_list = "dead"
                self.current_page = 1
                self.alive_tab.enable()
                self.dead_tab.disable()
                self.update_cat_list()
            elif event.ui_element == self.alive_tab:
                self.current_list = "alive"
                self.current_page = 1
                self.alive_tab.disable()
                self.dead_tab.enable()
                self.update_cat_list()
            elif event.ui_element == self.next_page_button:
                self.current_page += 1
                self.update_cat_list()
            elif event.ui_element == self.previous_page_button:
                self.current_page -= 1
                self.update_cat_list()
            

    def screen_switches(self):
        self.the_cat = game.clan.your_cat
        self.current_page = 1
        self.mentor = Cat.fetch_cat(self.the_cat.mentor)

        self.heading = pygame_gui.elements.UITextBox("",
                                                     scale(pygame.Rect((300, 50), (1000, 80))),
                                                     object_id=get_text_box_theme("#text_box_34_horizcenter"),
                                                     manager=MANAGER)
        self.selected_cat = None

        self.mentor_frame = pygame_gui.elements.UIImage(scale(pygame.Rect((630, 226), (562, 394))),
                                                        pygame.transform.scale(
                                                            image_cache.load_image(
                                                                "resources/images/choosing_cat1_frame_ment.png").convert_alpha(),
                                                            (562, 394)), manager=MANAGER)

        self.back_button = UIImageButton(scale(pygame.Rect((50, 1290), (210, 60))), "", object_id="#back_button")
        self.confirm_mentor = UIImageButton(scale(pygame.Rect((680, 610), (208, 52))), "",
                                            object_id="#patrol_select_button")
       
        self.previous_page_button = UIImageButton(scale(pygame.Rect((630, 1160), (68, 68))), "",
                                                  object_id="#relation_list_previous", manager=MANAGER)
        self.next_page_button = UIImageButton(scale(pygame.Rect((902, 1160), (68, 68))), "",
                                              object_id="#relation_list_next", manager=MANAGER)

        self.current_list = "alive"

        self.alive_tab = UIImageButton(scale(pygame.Rect((200, 653), (150, 70))), "",
                                              object_id="#alive_select_button", manager=MANAGER)
        self.dead_tab = UIImageButton(scale(pygame.Rect((360, 653), (150, 70))), "",
                                              object_id="#dead_select_button", manager=MANAGER)

        self.alive_tab.disable()
        self.update_selected_cat()  # Updates the image and details of selected cat
        self.update_cat_list()
        # self.update_buttons()

    def exit_screen(self):

        # self.selected_details["selected_image"].kill()
        # self.selected_details["selected_info"].kill()
        for ele in self.cat_list_buttons:
            self.cat_list_buttons[ele].kill()
        self.cat_list_buttons = {}

        for marker in self.fav:
            self.fav[marker].kill()
        self.fav = {}

        for ele in self.apprentice_details:
            self.apprentice_details[ele].kill()
        self.apprentice_details = {}

        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}

        self.heading.kill()
        del self.heading

        self.mentor_frame.kill()
        del self.mentor_frame

        self.back_button.kill()
        del self.back_button
        self.confirm_mentor.kill()
        del self.confirm_mentor

        self.previous_page_button.kill()
        del self.previous_page_button
        self.next_page_button.kill()
        del self.next_page_button
        self.alive_tab.kill()
        del self.alive_tab
        self.dead_tab.kill()
        del self.dead_tab

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

    def change_cat(self, new_mentor=None):
        self.exit_screen()
        game.cur_events_list.clear()
        game.clan.your_cat = new_mentor

        # resetting talked_to so the new MC can talk to a cat
        # the old one previously talked to in the same moon
        for cat in Cat.all_cats_list:
            if cat.talked_to is True:
                cat.talked_to = False

        game.switches["attended half-moon"] = False
        if game.clan.your_cat.status not in ['newborn', 'kitten', 'apprentice', 'medicine cat apprentice', 'mediator apprentice', "queen's apprentice"]:
            game.clan.your_cat.w_done = True
        game.switches['cur_screen'] = "events screen"

    def update_selected_cat(self):
        """Updates the image and information on the currently selected mentor"""
        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}
        if self.selected_cat:

            self.selected_details["selected_image"] = pygame_gui.elements.UIImage(
                scale(pygame.Rect((650, 300), (300, 300))),
                pygame.transform.scale(
                    self.selected_cat.sprite,
                    (300, 300)), manager=MANAGER)

            info = self.selected_cat.status + "\n" + \
                   self.selected_cat.genderalign + "\n" + self.selected_cat.personality.trait + "\n"
            if self.selected_cat.moons < 1:
                info += "???"
            else:
                info += self.selected_cat.skills.skill_string(short=True)

            self.selected_details["selected_info"] = pygame_gui.elements.UITextBox(info,
                                                                                   scale(pygame.Rect((965, 325),
                                                                                                     (210, 250))),
                                                                                   object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
                                                                                   manager=MANAGER)

            name = str(self.selected_cat.name)  # get name
            if 11 <= len(name):  # check name length
                short_name = str(name)[0:9]
                name = short_name + '...'
            self.selected_details["mentor_name"] = pygame_gui.elements.ui_label.UILabel(
                scale(pygame.Rect((690, 230), (220, 60))),
                name,
                object_id="#text_box_34_horizcenter", manager=MANAGER)

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

        for marker in self.fav:
            self.fav[marker].kill()
        self.fav = {}

        pos_x = 0
        pos_y = 40
        i = 0
        for cat in display_cats:
            if game.clan.clan_settings["show fav"] and cat.favourite != 0:
                self.fav[str(i)] = pygame_gui.elements.UIImage(
                    scale(pygame.Rect((200 + pos_x, 730 + pos_y), (100, 100))),
                    pygame.transform.scale(
                        pygame.image.load(
                            f"resources/images/fav_marker_{cat.favourite}.png").convert_alpha(),
                        (100, 100))
                )
                self.fav[str(i)].disable()
            self.cat_list_buttons["cat" + str(i)] = UISpriteButton(
                scale(pygame.Rect((200 + pos_x, 730 + pos_y), (100, 100))),
                cat.sprite, cat_object=cat, manager=MANAGER)
            pos_x += 120
            if pos_x >= 1100:
                pos_x = 0
                pos_y += 120
            i += 1

    def get_valid_cats(self):
        valid_mentors = []

        for cat in Cat.all_cats_list:
            if self.current_list == "alive":
                if not cat.dead and not cat.outside and not cat.ID == game.clan.your_cat.ID:
                    valid_mentors.append(cat)
            else:
                if cat.dead and not cat.ID == game.clan.your_cat.ID and not cat.ID == game.clan.instructor.ID and not cat.ID == game.clan.demon.ID and not cat.outside and cat.status not in [
                    "loner", "kittypet", "rogue", "former Clancat", "rival Clancat",
                    "rival newborn", "rival kitten", "rival apprentice",
                    "rival medicine cat apprentice", "rival queen's apprentice",
                    "rival mediator apprentice", "rival medicine cat", "rival mediator",
                    "rival deputy", "rival leader"
                    ]:
                    valid_mentors.append(cat)
        
        return valid_mentors

    def on_use(self):
        # Due to a bug in pygame, any image with buttons over it must be blited
        screen.blit(self.list_frame, (150 / 1600 * screen_x, 720 / 1400 * screen_y))

    def chunks(self, L, n):
        return [L[x: x + n] for x in range(0, len(L), n)]
