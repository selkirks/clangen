import pygame.transform
import pygame_gui.elements
from random import choice, randint
import ujson
import re
from scripts.event_class import Single_Event
from .Screens import Screens
from scripts.utility import get_text_box_theme, scale, pronoun_repl
from scripts.cat.cats import Cat
from scripts.game_structure import image_cache
from scripts.game_structure.game_essentials import game, screen, screen_x, screen_y, MANAGER
from scripts.events_module.relationship.pregnancy_events import Pregnancy_Events
from scripts.game_structure.ui_elements import UIImageButton, UISpriteButton

class AffairScreen(Screens):
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
        self.affair_screen = None

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element in self.cat_list_buttons.values():
                self.selected_cat = event.ui_element.return_cat_object()
                self.update_selected_cat()
            elif event.ui_element == self.confirm_mentor and self.selected_cat:
                if not self.selected_cat.dead:
                    self.update_selected_cat()
                    self.change_cat(self.selected_cat)
                    
                    # resetting selected cat so theyre not still in the box when reentering the affair screen next moon
                    self.selected_cat = None
            elif event.ui_element == self.back_button:
                self.change_screen('events screen')
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

    def screen_switches(self):
        self.the_cat = game.clan.your_cat
        self.mentor = Cat.fetch_cat(self.the_cat.mentor)

        self.heading = pygame_gui.elements.UITextBox("",
                                                    scale(pygame.Rect(
                                                        (300, 50), (1000, 80))),
                                                    object_id=get_text_box_theme(
                                                        "#text_box_34_horizcenter"),
                                                    manager=MANAGER)

        self.mentor_frame = pygame_gui.elements.UIImage(scale(pygame.Rect((200, 216), (596, 440))),
                                                        pygame.transform.scale(
                                                            image_cache.load_image(
                                                                "resources/images/affair_select.png").convert_alpha(),
                                                            (596, 440)), manager=MANAGER)

        self.back_button = UIImageButton(
            scale(pygame.Rect((50, 1290), (210, 60))), "", object_id="#back_button")
        self.confirm_mentor = UIImageButton(scale(pygame.Rect((300, 605), (208, 52))), "",
                                            object_id="#patrol_select_button")

        self.previous_page_button = UIImageButton(scale(pygame.Rect((630, 1160), (68, 68))), "",
                                                object_id="#relation_list_previous", manager=MANAGER)
        self.next_page_button = UIImageButton(scale(pygame.Rect((902, 1160), (68, 68))), "",
                                            object_id="#relation_list_next", manager=MANAGER)

        self.affair_screen = pygame_gui.elements.UIImage(scale(pygame.Rect((850, 130), (444, 546))),
                                                        pygame.transform.scale(image_cache.load_image("resources/images/affair_screen.png").convert_alpha(), (496, 420)), manager=MANAGER)

        self.update_selected_cat()
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

        if self.affair_screen:
            self.affair_screen.kill()

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

    RESOURCE_DIR = "resources/dicts/events/lifegen_events/"

    def change_cat(self, affair_cat=None):
        game.clan.affair = True
        with open(f"{self.RESOURCE_DIR}affair.json",
                encoding="ascii") as read_file:
            self.mu_txt = ujson.loads(read_file.read())
        success = self.is_success(affair_cat)
        affair_relationship_chance_lb = game.config["affair_relationship_change_lb"]
        affair_relationship_chance_ub = game.config["affair_relationship_change_ub"]
        if success:
            affair_cat.relationships.get(
                game.clan.your_cat.ID).dislike -= randint(affair_relationship_chance_lb, affair_relationship_chance_ub)
            affair_cat.relationships.get(
                game.clan.your_cat.ID).comfortable += randint(affair_relationship_chance_lb, affair_relationship_chance_ub)
            affair_cat.relationships.get(
                game.clan.your_cat.ID).romantic_love += randint(affair_relationship_chance_lb, affair_relationship_chance_ub)
            game.clan.your_cat.relationships.get(
                affair_cat.ID).romantic_love += randint(affair_relationship_chance_lb, affair_relationship_chance_ub)
            ceremony_txt = self.adjust_txt(
                choice(self.mu_txt['success']), affair_cat)
            game.cur_events_list.insert(0, Single_Event(ceremony_txt))
            if randint(1, game.config["affair_success_pregnancy_chance"]) == 1:
                Pregnancy_Events.handle_zero_moon_pregnant(
                    game.clan.your_cat, affair_cat, game.clan)
        else:
            ceremony_txt = self.adjust_txt(
                choice(self.mu_txt['fail']), affair_cat)
            game.cur_events_list.insert(0, Single_Event(ceremony_txt))
            if self.get_fail_consequence() == 0:
                ceremony_txt = self.adjust_txt(
                    choice(self.mu_txt['fail breakup']), affair_cat)
                for i in game.clan.your_cat.mate:
                    Cat.fetch_cat(i).get_ill("heartbroken")
                    Cat.fetch_cat(i).unset_mate(game.clan.your_cat)
                    Cat.fetch_cat(i).relationships.get(
                        game.clan.your_cat.ID).dislike += randint(affair_relationship_chance_lb, affair_relationship_chance_ub)
                    Cat.fetch_cat(i).relationships.get(
                        game.clan.your_cat.ID).comfortable -= randint(affair_relationship_chance_lb, affair_relationship_chance_ub)
                    Cat.fetch_cat(i).relationships.get(
                        game.clan.your_cat.ID).trust -= randint(affair_relationship_chance_lb, affair_relationship_chance_ub)
                    Cat.fetch_cat(i).relationships.get(
                        game.clan.your_cat.ID).romantic_love -= randint(affair_relationship_chance_lb, affair_relationship_chance_ub)
                game.cur_events_list.insert(1, Single_Event(ceremony_txt))
            else:
                ceremony_txt = self.adjust_txt(
                    choice(self.mu_txt['fail none']), affair_cat)
                game.cur_events_list.insert(1, Single_Event(ceremony_txt))
                for i in game.clan.your_cat.mate:
                    Cat.fetch_cat(i).relationships.get(
                        game.clan.your_cat.ID).dislike += randint(affair_relationship_chance_lb, affair_relationship_chance_ub)
                    Cat.fetch_cat(i).relationships.get(
                        game.clan.your_cat.ID).comfortable -= randint(affair_relationship_chance_lb, affair_relationship_chance_ub)
                    Cat.fetch_cat(i).relationships.get(
                        game.clan.your_cat.ID).trust -= randint(affair_relationship_chance_lb, affair_relationship_chance_ub)
                    Cat.fetch_cat(i).relationships.get(
                        game.clan.your_cat.ID).romantic_love -= randint(affair_relationship_chance_lb, affair_relationship_chance_ub)

        self.exit_screen()
        game.switches['cur_screen'] = "events screen"

    def is_success(self, affair_cat):
        """Calculates affair success rate based on relationships"""
        chance = game.config["affair_success_chance"]
        for i in game.clan.your_cat.mate:
            if Cat.fetch_cat(i).relationships.get(game.clan.your_cat.ID).romantic_love > 50:
                chance -=5
            elif Cat.fetch_cat(i).relationships.get(game.clan.your_cat.ID).romantic_love < 10:
                chance +=5
            if Cat.fetch_cat(i).relationships.get(game.clan.your_cat.ID).comfortable > 50:
                chance -=5
            elif Cat.fetch_cat(i).relationships.get(game.clan.your_cat.ID).comfortable < 10:
                chance +=5
            if Cat.fetch_cat(i).relationships.get(game.clan.your_cat.ID).trust > 50:
                chance -=5
            elif Cat.fetch_cat(i).relationships.get(game.clan.your_cat.ID).trust < 10:
                chance +=5
        if affair_cat.relationships.get(game.clan.your_cat.ID).dislike > 10:
            chance += 10
        if affair_cat.relationships.get(game.clan.your_cat.ID).romantic_love > 20:
            chance -= 10
        elif affair_cat.relationships.get(game.clan.your_cat.ID).romantic_love < 10:
            chance += 10
        if affair_cat.relationships.get(game.clan.your_cat.ID).comfortable > 20:
            chance -= 10
        elif affair_cat.relationships.get(game.clan.your_cat.ID).comfortable < 10:
            chance += 10
        if affair_cat.relationships.get(game.clan.your_cat.ID).trust > 20:
            chance -= 10
        elif affair_cat.relationships.get(game.clan.your_cat.ID).trust < 10:
            chance += 10
        if affair_cat.relationships.get(game.clan.your_cat.ID).admiration > 20:
            chance -= 10
        elif affair_cat.relationships.get(game.clan.your_cat.ID).admiration < 10:
            chance += 10
        if chance < 1:
            chance = 1
        if randint(1,100) < randint(0, max(0, chance + randint(-10,10))):
            return True
        return False

    def get_fail_consequence(self):
        return randint(0, 1)

    def adjust_txt(self, txt, affair_cat):
        random_mate = Cat.fetch_cat(choice(game.clan.your_cat.mate))
        while random_mate.dead or random_mate.outside:
            random_mate = Cat.fetch_cat(choice(game.clan.your_cat.mate))
        random_warrior = Cat.fetch_cat(choice(game.clan.clan_cats))
        counter = 0
        while random_warrior.status != "warrior" or random_warrior.dead or random_warrior.outside or random_warrior.ID == affair_cat.ID or random_warrior.ID in game.clan.your_cat.mate or random_warrior.ID == game.clan.your_cat.ID:
            random_warrior = Cat.fetch_cat(choice(game.clan.clan_cats))
            counter += 1
            if counter > 30:
                break

        process_text_dict = {}
        
        process_text_dict["y_c"] = (game.clan.your_cat, choice(game.clan.your_cat.pronouns))
        process_text_dict["a_n"] = (affair_cat, choice(affair_cat.pronouns))
        process_text_dict["m_n"] = (random_mate, choice(random_mate.pronouns))
        process_text_dict["r_w"] = (random_warrior, choice(random_warrior.pronouns))

        txt = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), txt)

        txt = txt.replace("a_n", str(affair_cat.name))
        txt = txt.replace("m_n", str(random_mate.name))
        txt = txt.replace("r_w", str(random_warrior.name))
        return txt

    def update_selected_cat(self):
        """Updates the image and information on the currently selected mentor"""
        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}
        if self.selected_cat:

            self.selected_details["selected_image"] = pygame_gui.elements.UIImage(
                scale(pygame.Rect((280, 300), (270, 270))),
                pygame.transform.scale(
                    self.selected_cat.sprite,
                    (270, 270)), manager=MANAGER)

            info = self.selected_cat.status + "\n" + \
                self.selected_cat.genderalign + "\n" + self.selected_cat.personality.trait + "\n" + \
                self.selected_cat.skills.skill_string(short=True)

            self.selected_details["selected_info"] = pygame_gui.elements.UITextBox(info,
                                                                                scale(pygame.Rect((570, 325),
                                                                                                    (210, 250))),
                                                                                object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
                                                                                manager=MANAGER)

            name = str(self.selected_cat.name)  # get name
            if 11 <= len(name):  # check name length
                short_name = str(name)[0:9]
                name = short_name + '...'
            self.selected_details["mentor_name"] = pygame_gui.elements.ui_label.UILabel(
                scale(pygame.Rect((290, 230), (220, 60))),
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
        """Get a list of valid mates for the current cat"""

        # Behold! The uglest list comprehension ever created!
        valid_mates = [i for i in Cat.all_cats_list if
                    not i.faded
                    and self.the_cat.is_potential_mate(
                        i, for_love_interest=False,
                        age_restriction=True)
                    and i.ID not in self.the_cat.mate]

        return valid_mates

    def on_use(self):
        # Due to a bug in pygame, any image with buttons over it must be blited
        screen.blit(self.list_frame, (150 / 1600 *
                    screen_x, 720 / 1400 * screen_y))

    def chunks(self, L, n):
        return [L[x: x + n] for x in range(0, len(L), n)]
