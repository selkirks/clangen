import pygame.transform
import pygame_gui.elements
from random import choice, randint
import ujson
import re
from scripts.event_class import Single_Event
from .Screens import Screens
from scripts.cat.cats import Cat
from scripts.game_structure import image_cache
from scripts.game_structure.game_essentials import game
from scripts.events_module.relationship.pregnancy_events import Pregnancy_Events
from scripts.game_structure.screen_settings import MANAGER
from scripts.game_structure.ui_elements import (
    UISpriteButton,
    UISurfaceImageButton,
    UIImageButton
)
from scripts.utility import (
    get_text_box_theme,
    ui_scale,
    ui_scale_offset,
    pronoun_repl
)
from ..ui.generate_box import get_box, BoxStyles
from ..ui.generate_button import get_button_dict, ButtonStyles
from ..ui.get_arrow import get_arrow
from ..ui.icon import Icon


class AffairScreen(Screens):
    selected_cat = None
    current_page = 1
    list_frame = None
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
                if not self.selected_cat.dead and not self.selected_cat.outside:
                    self.update_selected_cat()
                    self.change_cat(self.selected_cat)
                    # resetting selected cat so theyre not still in the box when reentering the affair screen next moon
                    self.selected_cat = None
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

    def screen_switches(self):
        super().screen_switches()
        self.the_cat = game.clan.your_cat

        list_frame = get_box(BoxStyles.ROUNDED_BOX, (650, 226))
        self.list_frame = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((75, 360), (650, 226))), list_frame, starting_height=1
        )

        self.heading = pygame_gui.elements.UITextBox("",
                                                    ui_scale(pygame.Rect(
                                                        (150, 25), (500, 40))),
                                                    object_id=get_text_box_theme(
                                                        "#text_box_34_horizcenter"),
                                                    manager=MANAGER)

        self.mentor_frame = pygame_gui.elements.UIImage(ui_scale(pygame.Rect((100, 108), (298, 220))),
                                                        pygame.transform.scale(
                                                            image_cache.load_image(
                                                                "resources/images/affair_select.png").convert_alpha(),
                                                            (298, 220)), manager=MANAGER)

        self.back_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((25, 25), (105, 30))),
            get_arrow(2) + " Back",
            get_button_dict(ButtonStyles.SQUOVAL, (105, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
        )
        self.confirm_mentor = UIImageButton(ui_scale(pygame.Rect((150, 302), (104, 26))), "",
                                            object_id="#patrol_select_button")

        self.previous_page_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((315, 579), (34, 34))),
            Icon.ARROW_LEFT,
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
            starting_height=0,
        )
        self.next_page_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((451, 579), (34, 34))),
            Icon.ARROW_RIGHT,
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
            starting_height=0,
        )
        self.affair_screen = pygame_gui.elements.UIImage(ui_scale(pygame.Rect((425, 65), (222, 273))),
                                                        pygame.transform.scale(image_cache.load_image("resources/images/affair_screen.png").convert_alpha(), (496, 420)), manager=MANAGER)

        self.update_selected_cat()
        self.update_cat_list()

    def exit_screen(self):
        self.current_page = 1

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
        
        if self.list_frame:
            self.list_frame.kill()
            del self.list_frame

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
                for i in game.clan.your_cat.mates:
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
                for i in game.clan.your_cat.mates:
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
        for i in game.clan.your_cat.mates:
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
        random_mate = Cat.fetch_cat(choice(game.clan.your_cat.mates))
        while random_mate.dead or random_mate.outside:
            random_mate = Cat.fetch_cat(choice(game.clan.your_cat.mates))
        random_warrior = Cat.fetch_cat(choice(game.clan.clan_cats))
        counter = 0
        while random_warrior.status != "warrior" or random_warrior.dead or random_warrior.outside or random_warrior.ID == affair_cat.ID or random_warrior.ID in game.clan.your_cat.mates or random_warrior.ID == game.clan.your_cat.ID:
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
                ui_scale(pygame.Rect((140, 150), (135, 135))),
                pygame.transform.scale(
                    self.selected_cat.sprite,
                    (135, 135)), manager=MANAGER)

            info = self.selected_cat.status + "\n" + \
                self.selected_cat.genderalign + "\n" + self.selected_cat.personality.trait + "\n" + \
                self.selected_cat.skills.skill_string(short=True)

            self.selected_details["selected_info"] = pygame_gui.elements.UITextBox(
                info,
                ui_scale(pygame.Rect((285, 162), (105, 125))),
                object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
                manager=MANAGER)

            name = str(self.selected_cat.name)  # get name
            if 11 <= len(name):  # check name length
                short_name = str(name)[0:9]
                name = short_name + '...'
            self.selected_details["mentor_name"] = pygame_gui.elements.ui_label.UILabel(
                ui_scale(pygame.Rect((145, 115), (110, 30))),
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
        pos_y = 20
        i = 0
        for cat in display_cats:
            if game.clan.clan_settings["show fav"] and cat.favourite != 0:
                self.fav[str(i)] = pygame_gui.elements.UIImage(
                    ui_scale(pygame.Rect((100 + pos_x, 365 + pos_y), (50, 50))),
                    pygame.transform.scale(
                        pygame.image.load(
                            f"resources/images/fav_marker_{cat.favourite}.png").convert_alpha(),
                        (50, 50))
                )
                self.fav[str(i)].disable()
            self.cat_list_buttons["cat" + str(i)] = UISpriteButton(
                ui_scale(pygame.Rect((100 + pos_x, 365 + pos_y), (50, 50))),
                cat.sprite, cat_object=cat, manager=MANAGER)
            pos_x += 60
            if pos_x >= 550:
                pos_x = 0
                pos_y += 60
            i += 1

    def get_valid_cats(self):
        """Get a list of valid mates for the current cat"""

        # Behold! The uglest list comprehension ever created!
        valid_mates = [i for i in Cat.all_cats_list if
                       not i.faded
                       and self.the_cat.is_potential_mate(
                           i, for_love_interest=False,
                           age_restriction=True
                       )
                       and i.ID not in self.the_cat.mates
                       and i.outside == self.the_cat.outside]

        return valid_mates

    def on_use(self):
        super().on_use()

    def chunks(self, L, n):
        return [L[x: x + n] for x in range(0, len(L), n)]
