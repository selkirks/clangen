# pylint: disable=line-too-long
"""

This file contains:
  The start screen,
  The switch clan screen,
  The settings screen,
  And the statistics screen.



"""  # pylint: enable=line-too-long

import logging
import os
import platform
import subprocess
import traceback
import logging
import random
from html import escape

import pygame
import pygame_gui
import ujson
from requests.exceptions import RequestException, Timeout

from scripts.cat.cats import Cat
from scripts.clan import Clan
from scripts.cat.pelts import Pelt
from scripts.game_structure import image_cache
from scripts.game_structure.discord_rpc import _DiscordRPC
from scripts.game_structure.game_essentials import game, screen, screen_x, screen_y, MANAGER
from scripts.game_structure.windows import DeleteCheck, UpdateAvailablePopup, ChangelogPopup, SaveError
from scripts.utility import get_text_box_theme, scale, quit  # pylint: disable=redefined-builtin
from scripts.cat.history import History
from .Screens import Screens
from ..housekeeping.datadir import get_data_dir, get_cache_dir
from ..housekeeping.update import has_update, UpdateChannel, get_latest_version_number
from ..housekeeping.version import get_version_info


logger = logging.getLogger(__name__)
has_checked_for_update = False
update_available = False

class AchievementScreen(Screens):
    """
    TODO: DOCS
    """

    def screen_switches(self):
        """
        TODO: DOCS
        """
        
        self.set_disabled_menu_buttons(["stats"])
        self.show_menu_buttons()
        self.update_heading_text(f'{game.clan.name}Clan')
        a_txt = ""
        with open('resources/dicts/achievements.json', 'r', encoding='utf-8') as f:
            a_txt = ujson.load(f)

        self.check_achivements()
        
        
        # Determine stats
        stats_text = f"Achievements:"
        for i in game.clan.achievements:
            stats_text += "\n" + a_txt[i]
            
            

        self.stats_box = pygame_gui.elements.UITextBox(
            stats_text,
            scale(pygame.Rect((200, 300), (1200, 1000))),
            manager=MANAGER,
            object_id=get_text_box_theme("#text_box_30_horizcenter"))

    def check_achivements(self):
        you = game.clan.your_cat
        achievements = set()
        murder_history = History.get_murders(you)
        clan_cats = game.clan.clan_cats
        count_alive_cats = 0
        if murder_history:
            if 'is_murderer' in murder_history:
                num_victims = len(murder_history["is_murderer"])
                if num_victims >= 0:
                    achievements.add("1")
                if num_victims >= 5:
                    achievements.add("2")
                if num_victims >= 20:
                    achievements.add("3")
                if num_victims >= 50:
                    achievements.add("4")
        else:
            if you.moons >= 120:
                achievements.add("25")
                
        for cat in clan_cats:
            if Cat.all_cats.get(cat).pelt.tortiebase and Cat.all_cats.get(cat).gender == 'male':
                achievements.add("5")
            if Cat.all_cats.get(cat).insulted == True:
                achievements.add("29")
            if (Cat.all_cats.get(cat).name.prefix == "Coffee" and Cat.all_cats.get(cat).name.suffix == "dot") or (Cat.all_cats.get(cat).name.prefix == "Chibi" and Cat.all_cats.get(cat).name.suffix == "Galaxies"):
                achievements.add("30")
            if Cat.all_cats.get(cat).status == 'apprentice' and Cat.all_cats.get(cat).name.prefix == "Pea" and Cat.all_cats.get(cat).pelt.white_colours:
                achievements.add("33")
            if Cat.all_cats.get(cat).status == 'kitten' and Cat.all_cats.get(cat).moons > 5:
                achievements.add("34")
            ##WILDCARD check, because I've lost control of my life
            ##Declare Lists of wildcard combos for comparison. (Will be made more professional later.)
            not_wildcard_patterns = ['tabby', 'ticked', 'mackerel', 'classic', 'agouti', 'smoke', 'single']
            ##Actual check for wildcardness
            if Cat.all_cats.get(cat).pelt.name == "Tortie" or Cat.all_cats.get(cat).pelt.name == "Calico":
                ID_check = Cat.all_cats.get(cat).ID 
                ##Check if wildcard colour combo
                if (Cat.all_cats.get(cat).pelt.colour == "WHITE" and not Cat.all_cats.get(cat).pelt.tortiecolour == "WHITE"):
                    achievements.add("6")
                elif ((Cat.all_cats.get(cat).pelt.colour in Pelt.black_colours or Cat.all_cats.get(cat).pelt.colour in Pelt.white_colours) and Cat.all_cats.get(cat).pelt.tortiecolour in Pelt.black_colours or Cat.all_cats.get(cat).pelt.tortiecolour in Pelt.white_colours):
                    achievements.add("6")
                elif ((Cat.all_cats.get(cat).pelt.colour in Pelt.ginger_colours) and Cat.all_cats.get(cat).pelt.tortiecolour in Pelt.ginger_colours or Cat.all_cats.get(cat).pelt.tortiecolour in Pelt.white_colours):
                    achievements.add("6")
                elif ((Cat.all_cats.get(cat).pelt.colour in Pelt.brown_colours) and Cat.all_cats.get(cat).pelt.tortiecolour in Pelt.white_colours):
                    achievements.add("6")
                ##Check if wildcard pattern combo       
                ##rewritten wildcard pattern combo
                if Cat.all_cats.get(cat).pelt.tortiebase in Pelt.tabbies and not Cat.all_cats.get(cat).pelt.tortiepattern == "single" and Cat.all_cats.get(cat).pelt.tortiebase != Cat.all_cats.get(cat).pelt.tortiepattern:
                    achievements.add("6")
                if Cat.all_cats.get(cat).pelt.tortiebase in Pelt.spotted and not Cat.all_cats.get(cat).pelt.tortiepattern == "single" and Cat.all_cats.get(cat).pelt.tortiebase != Cat.all_cats.get(cat).pelt.tortiepattern:
                    achievements.add("6")
                if Cat.all_cats.get(cat).pelt.tortiebase in Pelt.exotic and not Cat.all_cats.get(cat).pelt.tortiepattern == "single" and Cat.all_cats.get(cat).pelt.tortiebase != Cat.all_cats.get(cat).pelt.tortiepattern:
                    achievements.add("6")
                if Cat.all_cats.get(cat).pelt.tortiebase in Pelt.plain and not Cat.all_cats.get(cat).pelt.tortiepattern in not_wildcard_patterns and Cat.all_cats.get(cat).pelt.tortiebase != Cat.all_cats.get(cat).pelt.tortiepattern:
                    achievements.add("6")
            ##code block for achievement 31
            achieve31RankList = ['warrior', 'mediator', 'leader']
            achieve31UsedRanks = []
            if len(Cat.all_cats.get(cat).mate) >= 2:
                catMateIDs = Cat.all_cats.get(cat).mate.copy()
                if Cat.all_cats.get(cat).status in achieve31RankList:
                    achieve31UsedRanks.append(Cat.all_cats.get(cat).status)
                    for cat in clan_cats:
                        if Cat.all_cats.get(cat).ID in catMateIDs:
                            if (Cat.all_cats.get(cat).status in achieve31RankList) and (Cat.all_cats.get(cat).status not in achieve31UsedRanks):
                                achieve31UsedRanks.append(Cat.all_cats.get(cat).status)
                        countranks = 0
                        for i in achieve31UsedRanks:
                            if i in achieve31RankList:
                                countranks += 1
                            if countranks >= 3:
                                achievements.add("31")
        #code for achievement 23 + 24
            if Clan.age >= 1:                          
                if not Cat.all_cats.get(cat).dead and not Cat.all_cats.get(cat).outside:
                    count_alive_cats += 1
                if count_alive_cats == 1 and Cat.all_cats.get(cat).ID == you.ID:
                    achievements.add('23')
                elif count_alive_cats >= 100:
                    achievements.add('24')

        if you.joined_df:
            achievements.add("7")
        
        if len(you.former_apprentices) >= 1:
            achievements.add("8")
        if len(you.former_apprentices) >= 5:
            achievements.add("9")
        
        if you.inheritance.get_children():
            achievements.add("10")
        for i in you.relationships.keys():
            if you.relationships.get(i).dislike >= 60:
                achievements.add("11")
            if you.relationships.get(i).romantic_love >= 60:
                achievements.add('12')
            
        if len(you.mate) >= 5:
            achievements.add('13')
        if you.status == 'warrior':
            achievements.add('14')
        elif you.status == 'medicine cat':
            achievements.add('15')
        elif you.status == 'mediator':
            achievements.add('16')
        elif you.status == 'deputy':
            achievements.add('17')
        elif you.status == 'leader':
            achievements.add('18')
        elif you.status == 'elder':
            achievements.add('19')
        elif you.status == 'queen':
            achievements.add('32')
        
        if you.moons >= 200:
            achievements.add('20')
        if you.exiled:
            achievements.add('21')
        elif you.outside:
            achievements.add('22')
            
        if you.experience >= 100:
            achievements.add('26')
        if you.experience >= 200:
            achievements.add('27')
        if you.experience >= 300:
            achievements.add('28')        
        
        for i in game.clan.achievements:
            achievements.add(i)
        
        game.clan.achievements = list(achievements)

    def exit_screen(self):
        """
        TODO: DOCS
        """
        self.stats_box.kill()
        del self.stats_box

    def handle_event(self, event):
        """
        TODO: DOCS
        """
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            self.menu_button_pressed(event)

    def on_use(self):
        """
        TODO: DOCS
        """
