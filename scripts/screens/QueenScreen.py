import pygame.transform
import pygame_gui.elements
from random import choice, randint
import ujson
import re
from .Screens import Screens
from scripts.utility import get_text_box_theme, scale, pronoun_repl, get_personality_compatibility
from scripts.cat.cats import Cat
from scripts.game_structure import image_cache
from scripts.game_structure.game_essentials import game, screen, screen_x, screen_y, MANAGER
from scripts.game_structure.ui_elements import UIImageButton, UISpriteButton

class QueenScreen(Screens):
    selected_cat = None
    current_page = 1
    list_frame = pygame.transform.scale(image_cache.load_image("resources/images/choosing_frame.png").convert_alpha(),
                                        (1300 / 3200 * screen_x, 452 / 1400 * screen_y))
    queen_art = pygame.transform.scale(image_cache.load_image("resources/images/queenart.png").convert_alpha(),
                                        (300, 300))
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
        self.activity = "mossball"

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element in self.cat_list_buttons.values():
                self.selected_cat = event.ui_element.return_cat_object()
                self.update_selected_cat()
            elif event.ui_element == self.confirm_mentor and self.selected_cat:
                if not self.selected_cat.dead:
                    self.update_selected_cat()
                    self.change_cat(self.selected_cat)
            elif event.ui_element == self.back_button:
                self.change_screen('profile screen')
            elif event.ui_element == self.next_cat_button:
                if isinstance(Cat.fetch_cat(self.next_cat), Cat):
                    game.switches['cat'] = self.next_cat
                    self.update_cat_list()
                    self.update_selected_cat()
                else:
                    print("invalid next cat", self.next_cat)
            elif event.ui_element == self.previous_cat_button:
                if isinstance(Cat.fetch_cat(self.previous_cat), Cat):
                    game.switches['cat'] = self.previous_cat
                    self.update_cat_list()
                    self.update_selected_cat()
                else:
                    print("invalid previous cat", self.previous_cat)
            elif event.ui_element == self.next_page_button:
                self.current_page += 1
                self.update_cat_list()
            elif event.ui_element == self.previous_page_button:
                self.current_page -= 1
                self.update_cat_list()
        elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            self.activity = event.text

    def screen_switches(self):
        self.the_cat = Cat.all_cats.get(game.switches['cat'])
        self.activity = "mossball"
        self.heading = pygame_gui.elements.UITextBox(f"{self.the_cat.name}'s Nursery Activities",
                                                     scale(pygame.Rect((300, 50), (1000, 80))),
                                                     object_id=get_text_box_theme("#text_box_34_horizcenter"),
                                                     manager=MANAGER)
        if game.settings['dark mode']:
            if self.the_cat.did_activity:
                self.heading2 = pygame_gui.elements.UITextBox("This queen already worked this moon.",
                                                        scale(pygame.Rect((300, 110), (1000, 160))),
                                                        object_id=get_text_box_theme("#text_box_26"),
                                                        manager=MANAGER)
            else:
                self.heading2 = pygame_gui.elements.UITextBox("Nursery activities can impact a kit's stats.\nStats may affect the kit's future role and personality.",
                                                        scale(pygame.Rect((300, 110), (1000, 160))),
                                                        object_id=get_text_box_theme("#text_box_26"),
                                                        manager=MANAGER)

        else:
            if self.the_cat.did_activity:
                self.heading2 = pygame_gui.elements.UITextBox("This queen already worked this moon.",
                                                        scale(pygame.Rect((530, 110), (1000, 160))),
                                                        object_id=get_text_box_theme("#text_box_26"),
                                                        manager=MANAGER)
            else:
                self.heading2 = pygame_gui.elements.UITextBox("Nursery activities can impact a kit's stats.\nStats may affect the kit's future role and personality.",
                                                        scale(pygame.Rect((530, 110), (1000, 160))),
                                                        object_id=get_text_box_theme("#text_box_26"),
                                                        manager=MANAGER)

        self.mentor_frame = pygame_gui.elements.UIImage(scale(pygame.Rect((830, 226), (562, 394))),
                                                        pygame.transform.scale(
                                                            image_cache.load_image(
                                                                "resources/images/choosing_cat1_frame_ment.png").convert_alpha(),
                                                            (562, 394)), manager=MANAGER)

        self.back_button = UIImageButton(scale(pygame.Rect((50, 1290), (210, 60))), "", object_id="#back_button")
        

        self.previous_page_button = UIImageButton(scale(pygame.Rect((310, 1160), (68, 68))), "",
                                                  object_id="#relation_list_previous", manager=MANAGER)
        self.next_page_button = UIImageButton(scale(pygame.Rect((582, 1160), (68, 68))), "",
                                              object_id="#relation_list_next", manager=MANAGER)

        self.activity_text = pygame_gui.elements.UITextBox("Activity:",
                                                     scale(pygame.Rect((-110, 220), (1000, 80))),
                                                     object_id=get_text_box_theme("#text_box_34_horizcenter"),
                                                     manager=MANAGER)
        self.activities = pygame_gui.elements.UIDropDownMenu(["mossball", "playfight", "lecture", "clean", "tell story", "scavenger hunt"], "mossball", scale(pygame.Rect((200, 300), (300, 70))), manager=MANAGER)
        self.confirm_mentor = UIImageButton(scale(pygame.Rect((580, 300), (208, 52))), "",
                                            object_id="#play_select")
        if self.the_cat.did_activity:
            self.confirm_mentor.disable()
        self.activity_box = pygame_gui.elements.UITextBox("",
                                                     scale(pygame.Rect((200, 420), (600, 400))),
                                                     object_id=get_text_box_theme("#text_box_26"),
                                                     manager=MANAGER)
        self.selected_cat = None
        self.update_selected_cat()  # Updates the image and details of selected cat
        self.update_cat_list()

    def exit_screen(self):

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
        self.heading2.kill()
        del self.heading2
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

        self.activity_box.kill()
        self.activity_text.kill()
        self.activities.kill()


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
            

    def change_cat(self, affair_cat=None):
        RESOURCE_DIR = "resources/dicts/events/lifegen_events/"
        with open(f"{RESOURCE_DIR}nursery_activities.json", 'r') as read_file:
            display_events = ujson.loads(read_file.read())[self.activity]

        success = self.get_success()
        stat_change = choice(display_events["stat_change"])
        while (success and "down" in stat_change) or (not success and "up" in stat_change):
            stat_change = choice(display_events["stat_change"])
        self.activity_box.kill()
        self.activity_box = pygame_gui.elements.UITextBox(self.adjust_txt(choice(display_events[stat_change])),
                                                    scale(pygame.Rect((200, 420), (600, 400))),
                                                    object_id=get_text_box_theme("#text_box_26"),
                                                    manager=MANAGER)
        if stat_change == "courage up":
            self.selected_cat.courage += 1
        elif stat_change == "courage down":
            self.selected_cat.courage -= 1
        elif stat_change == "empathy up":
            self.selected_cat.empathy += 1
        elif stat_change == "empathy down":
            self.selected_cat.empathy -= 1
        elif stat_change == "compassion up":
            self.selected_cat.compassion += 1
        elif stat_change == "compassion down":
            self.selected_cat.compassion -= 1
        elif stat_change == "intelligence up":
            self.selected_cat.intelligence += 1
        elif stat_change == "intelligence down":
            self.selected_cat.intelligence -= 1
        
        if success:
            exp_gain = randint(5, 20)
            self.the_cat.experience += exp_gain
        self.the_cat.did_activity = True
        self.confirm_mentor.disable()
        self.update_selected_cat()

    def get_success(self):
        queen = self.the_cat
        kit = self.selected_cat

        #influences on success chances: exp, relationship, skill

        chance = 50
        
        if queen.experience_level == "untrained":
            chance = 40
        elif queen.experience_level == "trainee":
            chance = 50
        elif queen.experience_level == "prepared":
            chance = 60
        elif queen.experience_level == "proficient":
            chance = 70
        elif queen.experience_level == "expert":
            chance = 80
        elif queen.experience_level == "master":
            chance = 90

        if queen.ID in kit.relationships:
            rel1 = queen.relationships[kit.ID]
        else:
            rel1 = queen.create_one_relationship(kit)

        if kit.ID in queen.relationships:
            rel2 = kit.relationships[queen.ID]
        else:
            rel2 = kit.create_one_relationship(queen)

        compat = get_personality_compatibility(queen, kit)
        if compat is True:
            chance += 10
        elif compat is False:
            chance -= 5

        if rel1.platonic_like > 30:
            chance += 5
        if rel1.dislike > 10:
            chance -= 5
        if rel2.platonic_like > 30:
            chance += 5
        if rel2.dislike > 10:
            chance -= 5
        
        return randint(0, 100) < min(chance, 95)


    def adjust_txt(self, text):
        process_text_dict = {}
        process_text_dict["t_k"] = self.selected_cat
        process_text_dict["t_q"] = self.the_cat
        for abbrev in process_text_dict.keys():
            abbrev_cat = process_text_dict[abbrev]
            process_text_dict[abbrev] = (abbrev_cat, choice(abbrev_cat.pronouns))
        text = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), text)
        text = text.replace("t_k", str(self.selected_cat.name))
        text = text.replace("t_q", str(self.the_cat.name))
        return text

    def update_selected_cat(self):
        """Updates the image and information on the currently selected mentor"""
        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}
        if self.selected_cat:

            self.selected_details["selected_image"] = pygame_gui.elements.UIImage(
                scale(pygame.Rect((850, 300), (300, 300))),
                pygame.transform.scale(
                    self.selected_cat.sprite,
                    (300, 300)), manager=MANAGER)

            stats = f"Courage: {self.selected_cat.courage}\nCompassion: {self.selected_cat.compassion} \nIntelligence: {self.selected_cat.intelligence} \nEmpathy: {self.selected_cat.empathy}"
            
            self.selected_details["selected_info"] = pygame_gui.elements.UITextBox(stats,
                                                                                   scale(pygame.Rect((1180, 325),
                                                                                                     (210, 250))),
                                                                                   object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
                                                                                   manager=MANAGER)

            name = str(self.selected_cat.name)  # get name
            if 11 <= len(name):  # check name length
                short_name = str(name)[0:9]
                name = short_name + '...'
            self.selected_details["mentor_name"] = pygame_gui.elements.ui_label.UILabel(
                scale(pygame.Rect((890, 230), (220, 60))),
                name,
                object_id="#text_box_34_horizcenter", manager=MANAGER)

    def update_cat_list(self):
        """Updates the cat sprite buttons. """
        valid_mentors = self.chunks(self.get_valid_cats(), 15)

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
            if pos_x >= 525:
                pos_x = 0
                pos_y += 120
            i += 1

    def get_valid_cats(self):
        """Get a list of valid mates for the current cat"""
        
        # Behold! The uglest list comprehension ever created!
        valid_mates = [i for i in Cat.all_cats_list if
                       not i.faded
                       and i.moons >=1 and i.moons < 6 and not i.dead and not i.outside]
        
        return valid_mates

    def on_use(self):
        # Due to a bug in pygame, any image with buttons over it must be blited
        screen.blit(self.list_frame, (150 / 1600 * screen_x, 720 / 1400 * screen_y))
        screen.blit(self.queen_art, (150 / 260 * screen_x, 720 / 1410 * screen_y))

    def chunks(self, L, n):
        return [L[x: x + n] for x in range(0, len(L), n)]