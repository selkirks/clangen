import os
import shutil
import subprocess
import threading
import time
from platform import system
from random import choice
import ujson
import pygame
import platform
import pygame_gui
from re import sub
import random
from typing import TYPE_CHECKING
from pygame_gui.elements import UIWindow
from pygame_gui.windows import UIMessageWindow
from scripts.cat.history import History
from scripts.cat.names import Name
from scripts.game_structure import image_cache
from scripts.housekeeping.progress_bar_updater import UIUpdateProgressBar
from scripts.event_class import Single_Event
from scripts.game_structure.game_essentials import game
from scripts.game_structure.screen_settings import MANAGER
from scripts.game_structure.ui_elements import (
    UIImageButton,
    UITextBoxTweaked,
    UISurfaceImageButton,
)
from scripts.housekeeping.datadir import (
    get_save_dir,
    get_cache_dir,
    get_saved_images_dir,
    get_data_dir,
)
from scripts.housekeeping.update import (
    self_update,
    UpdateChannel,
    get_latest_version_number,
)
from scripts.housekeeping.version import get_version_info
from scripts.ui.generate_box import BoxStyles, get_box
from scripts.ui.generate_button import ButtonStyles, get_button_dict
from scripts.ui.get_arrow import get_arrow
from scripts.ui.icon import Icon
from scripts.utility import (
    ui_scale,
    quit,
    update_sprite,
    logger,
    process_text,
    ui_scale_dimensions,
    ui_scale_offset,
)

if TYPE_CHECKING:
    from scripts.screens.Screens import Screens


class SymbolFilterWindow(UIWindow):
    def __init__(self):
        super().__init__(
            ui_scale(pygame.Rect((250, 175), (300, 450))),
            window_display_title="Symbol Filters",
            object_id="#filter_window",
        )
        self.set_blocking(True)

        self.possible_tags = {
            "plant": ["flower", "tree", "leaf", "other plant", "fruit"],
            "animal": ["cat", "fish", "bird", "mammal", "bug", "other animal"],
            "element": ["water", "fire", "earth", "air", "light"],
            "location": [],
            "descriptor": [],
            "miscellaneous": [],
        }

        self.back_button = UIImageButton(
            ui_scale(pygame.Rect((270, 5), (22, 22))),
            "",
            object_id="#exit_window_button",
            starting_height=10,
            container=self,
        )
        self.filter_title = pygame_gui.elements.UILabel(
            ui_scale(pygame.Rect((5, 5), (-1, -1))),
            text="Show Symbols With:",
            object_id="#text_box_40",
            container=self,
        )
        self.filter_container = pygame_gui.elements.UIScrollingContainer(
            ui_scale(pygame.Rect((5, 45), (285, 310))),
            manager=MANAGER,
            starting_height=1,
            object_id="#filter_container",
            allow_scroll_x=False,
            container=self,
        )
        self.checkbox = {}
        self.checkbox_text = {}
        x_pos = 15
        y_pos = 20
        for tag, subtags in self.possible_tags.items():
            self.checkbox[tag] = UIImageButton(
                ui_scale(pygame.Rect((x_pos, y_pos), (34, 34))),
                "",
                object_id="@checked_checkbox",
                container=self.filter_container,
                starting_height=2,
                manager=MANAGER,
            )
            if tag in game.switches["disallowed_symbol_tags"]:
                self.checkbox[tag].change_object_id("@unchecked_checkbox")

            self.checkbox_text[tag] = pygame_gui.elements.UILabel(
                ui_scale(pygame.Rect((6, y_pos + 4), (-1, -1))),
                text=str(tag),
                container=self.filter_container,
                object_id="#text_box_30_horizleft",
                manager=MANAGER,
                anchors={"left_target": self.checkbox[tag]},
            )
            y_pos += 35
            if subtags:
                for s_tag in subtags:
                    self.checkbox[s_tag] = UIImageButton(
                        ui_scale(pygame.Rect((x_pos + 35, y_pos), (34, 34))),
                        "",
                        object_id="@checked_checkbox",
                        container=self.filter_container,
                        starting_height=2,
                        manager=MANAGER,
                    )

                    if tag in game.switches["disallowed_symbol_tags"]:
                        self.checkbox[s_tag].disable()
                    if s_tag in game.switches["disallowed_symbol_tags"]:
                        self.checkbox[s_tag].change_object_id("@unchecked_checkbox")

                    self.checkbox_text[s_tag] = pygame_gui.elements.UILabel(
                        ui_scale(pygame.Rect((6, y_pos + 4), (-1, -1))),
                        text=s_tag,
                        container=self.filter_container,
                        object_id="#text_box_30_horizleft",
                        manager=MANAGER,
                        anchors={"left_target": self.checkbox[s_tag]},
                    )
                    y_pos += 30
                y_pos += 5

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.back_button:
                self.kill()

            elif event.ui_element in self.checkbox.values():
                for tag, element in self.checkbox.items():
                    if element == event.ui_element:
                        # find out what state the checkbox was in when clicked
                        object_ids = element.get_object_ids()
                        # handle checked checkboxes becoming unchecked
                        if "@checked_checkbox" in object_ids:
                            self.checkbox[tag].change_object_id("@unchecked_checkbox")
                            # add tag to disallowed list
                            if tag not in game.switches["disallowed_symbol_tags"]:
                                game.switches["disallowed_symbol_tags"].append(tag)
                            # if tag had subtags, also add those subtags
                            if tag in self.possible_tags:
                                for s_tag in self.possible_tags[tag]:
                                    self.checkbox[s_tag].change_object_id(
                                        "@unchecked_checkbox"
                                    )
                                    self.checkbox[s_tag].disable()
                                    if (
                                        s_tag
                                        not in game.switches["disallowed_symbol_tags"]
                                    ):
                                        game.switches["disallowed_symbol_tags"].append(
                                            s_tag
                                        )

                        # handle unchecked checkboxes becoming checked
                        elif "@unchecked_checkbox" in object_ids:
                            self.checkbox[tag].change_object_id("@checked_checkbox")
                            # remove tag from disallowed list
                            if tag in game.switches["disallowed_symbol_tags"]:
                                game.switches["disallowed_symbol_tags"].remove(tag)
                            # if tag had subtags, also add those subtags
                            if tag in self.possible_tags:
                                for s_tag in self.possible_tags[tag]:
                                    self.checkbox[s_tag].change_object_id(
                                        "@checked_checkbox"
                                    )
                                    self.checkbox[s_tag].enable()
                                    if s_tag in game.switches["disallowed_symbol_tags"]:
                                        game.switches["disallowed_symbol_tags"].remove(
                                            s_tag
                                        )
        return super().process_event(event)


class SaveCheck(UIWindow):
    def __init__(self, last_screen, is_main_menu, mm_btn):
        if game.is_close_menu_open:
            return
        game.is_close_menu_open = True
        super().__init__(
            ui_scale(pygame.Rect((250, 200), (300, 200))),
            window_display_title="Save Check",
            object_id="#save_check_window",
            resizable=False,
            always_on_top=True,
        )
        self.set_blocking(True)

        self.clan_name = "UndefinedClan"
        if game.clan:
            self.clan_name = f"{game.clan.name}Clan"
        self.last_screen = last_screen
        self.isMainMenu = is_main_menu
        self.mm_btn = mm_btn
        # adding a variable for starting_height to make sure that this menu is always on top
        top_stack_menu_layer_height = 10000
        if self.isMainMenu:
            self.mm_btn.disable()
            self.main_menu_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((0, 155), (152, 30))),
                get_arrow(3) + " Main Menu",
                get_button_dict(ButtonStyles.SQUOVAL, (152, 30)),
                manager=MANAGER,
                object_id="@buttonstyles_squoval",
                starting_height=top_stack_menu_layer_height,
                container=self,
                anchors={"centerx": "centerx"},
            )
            self.message = (
                "Would you like to save your game before exiting to the Main Menu? If you don't, progress "
                "may be lost!"
            )
        else:
            self.main_menu_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((0, 155), (152, 30))),
                get_arrow(2) + " Quit Game",
                get_button_dict(ButtonStyles.SQUOVAL, (152, 30)),
                manager=MANAGER,
                object_id="@buttonstyles_squoval",
                starting_height=top_stack_menu_layer_height,
                container=self,
                anchors={"centerx": "centerx"},
            )
            self.message = "Would you like to save your game before exiting? If you don't, progress may be lost!"

        self.game_over_message = UITextBoxTweaked(
            self.message,
            ui_scale(pygame.Rect((20, 20), (260, -1))),
            line_spacing=1,
            object_id="#text_box_30_horizcenter",
            container=self,
        )
        self.save_button = UIImageButton(
            ui_scale(pygame.Rect((0, 115), (114, 30))),
            "",
            object_id="#save_button",
            starting_height=top_stack_menu_layer_height,
            container=self,
            anchors={"centerx": "centerx"},
        )
        self.save_button_saved_state = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((0, 115), (114, 30))),
            pygame.transform.scale(
                image_cache.load_image("resources/images/save_clan_saved.png"),
                ui_scale_dimensions((114, 30)),
            ),
            starting_height=top_stack_menu_layer_height + 2,
            container=self,
            anchors={"centerx": "centerx"},
        )
        self.save_button_saved_state.hide()
        self.save_button_saving_state = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((93, 115), (114, 30))),
            pygame.transform.scale(
                image_cache.load_image("resources/images/save_clan_saving.png"),
                ui_scale_dimensions((114, 30)),
            ),
            starting_height=top_stack_menu_layer_height + 1,
            container=self,
        )
        self.save_button_saving_state.hide()

        self.back_button = UIImageButton(
            ui_scale(pygame.Rect((270, 5), (22, 22))),
            "",
            object_id="#exit_window_button",
            starting_height=top_stack_menu_layer_height,
            container=self,
        )

        self.back_button.enable()
        self.main_menu_button.enable()
        self.set_blocking(True)

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.main_menu_button:
                if self.isMainMenu:
                    game.is_close_menu_open = False
                    self.mm_btn.enable()
                    game.last_screen_forupdate = game.switches["cur_screen"]
                    game.switches["cur_screen"] = "start screen"
                    game.switch_screens = True
                    self.kill()
                else:
                    game.is_close_menu_open = False
                    quit(savesettings=False, clearevents=False)
            elif event.ui_element == self.save_button:
                if game.clan is not None:
                    self.save_button_saving_state.show()
                    self.save_button.disable()
                    game.save_cats()
                    game.clan.save_clan()
                    game.clan.save_pregnancy(game.clan)
                    game.save_events()
                    self.save_button_saving_state.hide()
                    self.save_button_saved_state.show()
            elif event.ui_element == self.back_button:
                game.is_close_menu_open = False
                self.kill()
                if self.isMainMenu:
                    self.mm_btn.enable()

                # only allow one instance of this window
        return super().process_event(event)


class DeleteCheck(UIWindow):
    def __init__(self, reloadscreen, clan_name):
        super().__init__(
            ui_scale(pygame.Rect((250, 200), (300, 180))),
            window_display_title="Delete Check",
            object_id="#delete_check_window",
            resizable=False,
        )
        self.set_blocking(True)
        self.clan_name = clan_name
        self.reloadscreen = reloadscreen

        self.delete_check_message = UITextBoxTweaked(
            f"Do you wish to delete {str(self.clan_name + 'Clan')}? This is permanent and cannot be undone.",
            ui_scale(pygame.Rect((20, 20), (260, -1))),
            line_spacing=1,
            object_id="#text_box_30_horizcenter",
            container=self,
        )

        self.delete_it_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((71, 100), (153, 30))),
            "Delete it!",
            get_button_dict(ButtonStyles.SQUOVAL, (153, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )
        self.go_back_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((71, 145), (153, 30))),
            "No! Go back!",
            get_button_dict(ButtonStyles.SQUOVAL, (153, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )

        self.back_button = UIImageButton(
            ui_scale(pygame.Rect((270, 5), (22, 22))),
            "",
            object_id="#exit_window_button",
            container=self,
        )

        self.back_button.enable()

        self.go_back_button.enable()
        self.delete_it_button.enable()

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.delete_it_button:
                rempath = get_save_dir() + "/" + self.clan_name
                shutil.rmtree(rempath)
                if os.path.exists(rempath + "clan.json"):
                    os.remove(rempath + "clan.json")
                elif os.path.exists(rempath + "clan.txt"):
                    os.remove(rempath + "clan.txt")
                else:
                    print("No clan.json/txt???? Clan prolly wasnt initalized kekw")
                self.kill()
                self.reloadscreen("switch clan screen")

            elif event.ui_element == self.go_back_button:
                self.kill()
            elif event.ui_element == self.back_button:
                game.is_close_menu_open = False
                self.kill()
        return super().process_event(event)


class GameOver(UIWindow):
    def __init__(self, last_screen):
        super().__init__(
            ui_scale(pygame.Rect((250, 200), (300, 180))),
            window_display_title="Game Over",
            object_id="#game_over_window",
            resizable=False,
        )
        self.set_blocking(True)
        self.clan_name = str(game.clan.name + "Clan")
        self.last_screen = last_screen
        self.game_over_message = UITextBoxTweaked(
            f"{self.clan_name} has died out. For now, this is where their story ends. Perhaps it's time to tell a new "
            f"tale?",
            ui_scale(pygame.Rect((20, 20), (260, -1))),
            line_spacing=1,
            object_id="",
            container=self,
        )

        self.game_over_message = UITextBoxTweaked(
            f"(leaving will not erase the save file)",
            ui_scale(pygame.Rect((20, 155), (260, -1))),
            line_spacing=0.8,
            object_id="#text_box_22_horizcenter",
            container=self,
        )

        self.begin_anew_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((25, 115), (111, 30))),
            "begin anew",
            get_button_dict(ButtonStyles.SQUOVAL, (111, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )
        self.not_yet_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((159, 115), (111, 30))),
            "not yet",
            get_button_dict(ButtonStyles.SQUOVAL, (111, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )

        self.not_yet_button.enable()
        self.begin_anew_button.enable()

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.begin_anew_button:
                game.last_screen_forupdate = game.switches["cur_screen"]
                game.switches["cur_screen"] = "start screen"
                game.switch_screens = True
                self.kill()
            elif event.ui_element == self.not_yet_button:
                self.kill()
        return super().process_event(event)


class ChangeCatName(UIWindow):
    """This window allows the user to change the cat's name"""

    def __init__(self, cat):
        super().__init__(
            ui_scale(pygame.Rect((300, 215), (400, 185))),
            window_display_title="Change Cat Name",
            object_id="#change_cat_name_window",
            resizable=False,
        )
        self.the_cat = cat
        self.back_button = UIImageButton(
            ui_scale(pygame.Rect((370, 5), (22, 22))),
            "",
            object_id="#exit_window_button",
            container=self,
        )

        self.specsuffic_hidden = self.the_cat.name.specsuffix_hidden

        self.heading = pygame_gui.elements.UITextBox(
            f"-Change {self.the_cat.name}'s Name-",
            ui_scale(pygame.Rect((50, 10), (300, 40))),
            object_id="#text_box_30_horizcenter",
            manager=MANAGER,
            container=self,
        )

        self.name_changed = pygame_gui.elements.UITextBox(
            "Name Changed!",
            ui_scale(pygame.Rect((245, 130), (400, 40))),
            visible=False,
            object_id="#text_box_30_horizleft",
            manager=MANAGER,
            container=self,
        )

        self.done_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((161, 145), (77, 30))),
            "done",
            get_button_dict(ButtonStyles.SQUOVAL, (77, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
            container=self,
        )

        x_pos, y_pos = 37, 17

        self.prefix_entry_box = pygame_gui.elements.UITextEntryLine(
            ui_scale(pygame.Rect((0 + x_pos, 50 + y_pos), (120, 30))),
            initial_text=self.the_cat.name.prefix,
            manager=MANAGER,
            container=self,
        )

        self.random_prefix = UISurfaceImageButton(
            ui_scale(pygame.Rect((122 + x_pos, 48 + y_pos), (34, 34))),
            "\u2684",
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
            manager=MANAGER,
            container=self,
            tool_tip_text="Randomize the prefix",
            sound_id="dice_roll",
        )

        self.random_suffix = UISurfaceImageButton(
            ui_scale(pygame.Rect((281 + x_pos, 48 + y_pos), (34, 34))),
            "\u2684",
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
            manager=MANAGER,
            container=self,
            tool_tip_text="Randomize the suffix",
            sound_id="dice_roll",
        )

        self.toggle_spec_block_on = UIImageButton(
            ui_scale(pygame.Rect((202 + x_pos, 80 + y_pos), (34, 34))),
            "",
            object_id="@unchecked_checkbox",
            tool_tip_text=f"Remove the cat's special suffix",
            manager=MANAGER,
            container=self,
        )

        self.toggle_spec_block_off = UIImageButton(
            ui_scale(pygame.Rect((202 + x_pos, 80 + y_pos), (34, 34))),
            "",
            object_id="@checked_checkbox",
            tool_tip_text="Re-enable the cat's special suffix",
            manager=MANAGER,
            container=self,
        )

        if self.the_cat.status in self.the_cat.name.names_dict["special_suffixes"]:
            self.suffix_entry_box = pygame_gui.elements.UITextEntryLine(
                ui_scale(pygame.Rect((159 + x_pos, 50 + y_pos), (120, 30))),
                placeholder_text=self.the_cat.name.names_dict["special_suffixes"][
                    self.the_cat.status
                ],
                manager=MANAGER,
                container=self,
            )
            if not self.the_cat.name.specsuffix_hidden:
                self.toggle_spec_block_on.show()
                self.toggle_spec_block_on.enable()
                self.toggle_spec_block_off.hide()
                self.toggle_spec_block_off.disable()
                self.random_suffix.disable()
                self.suffix_entry_box.disable()
            else:
                self.toggle_spec_block_on.hide()
                self.toggle_spec_block_on.disable()
                self.toggle_spec_block_off.show()
                self.toggle_spec_block_off.enable()
                self.random_suffix.enable()
                self.suffix_entry_box.enable()
                self.suffix_entry_box.set_text(self.the_cat.name.suffix)

        else:
            self.toggle_spec_block_on.disable()
            self.toggle_spec_block_on.hide()
            self.toggle_spec_block_off.disable()
            self.toggle_spec_block_off.hide()
            self.suffix_entry_box = pygame_gui.elements.UITextEntryLine(
                ui_scale(pygame.Rect((159 + x_pos, 50 + y_pos), (120, 30))),
                initial_text=self.the_cat.name.suffix,
                manager=MANAGER,
                container=self,
            )
        self.set_blocking(True)

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.done_button:
                old_name = str(self.the_cat.name)

                self.the_cat.specsuffix_hidden = self.specsuffic_hidden
                self.the_cat.name.specsuffix_hidden = self.specsuffic_hidden

                # Note: Prefixes are not allowed be all spaces or empty, but they can have spaces in them.
                if sub(r"[^A-Za-z0-9 ]+", "", self.prefix_entry_box.get_text()) != "":
                    self.the_cat.name.prefix = sub(
                        r"[^A-Za-z0-9 ]+", "", self.prefix_entry_box.get_text()
                    )

                # Suffixes can be empty, if you want. However, don't change the suffix if it's currently being hidden
                # by a special suffix.
                if (
                    self.the_cat.status
                    not in self.the_cat.name.names_dict["special_suffixes"]
                    or self.the_cat.name.specsuffix_hidden
                ):
                    self.the_cat.name.suffix = sub(
                        r"[^A-Za-z0-9 ]+", "", self.suffix_entry_box.get_text()
                    )
                    self.name_changed.show()

                if old_name != str(self.the_cat.name):
                    self.name_changed.show()
                    self.heading.set_text(f"-Change {self.the_cat.name}'s Name-")
                else:
                    self.name_changed.hide()

            elif event.ui_element == self.random_prefix:
                if self.suffix_entry_box.text:
                    use_suffix = self.suffix_entry_box.text
                else:
                    use_suffix = self.the_cat.name.suffix
                self.prefix_entry_box.set_text(
                    Name(
                        None,
                        use_suffix,
                        cat=self.the_cat
                    ).prefix
                )
            elif event.ui_element == self.random_suffix:
                if self.prefix_entry_box.text:
                    use_prefix = self.prefix_entry_box.text
                else:
                    use_prefix = self.the_cat.name.prefix
                self.suffix_entry_box.set_text(
                    Name(
                        use_prefix,
                        None,
                        cat=self.the_cat
                    ).suffix
                )
            elif event.ui_element == self.toggle_spec_block_on:
                self.specsuffic_hidden = True
                self.suffix_entry_box.enable()
                self.random_suffix.enable()
                self.toggle_spec_block_on.disable()
                self.toggle_spec_block_on.hide()
                self.toggle_spec_block_off.enable()
                self.toggle_spec_block_off.show()
                self.suffix_entry_box.set_text(self.the_cat.name.suffix)
            elif event.ui_element == self.toggle_spec_block_off:
                self.specsuffic_hidden = False
                self.random_suffix.disable()
                self.toggle_spec_block_off.disable()
                self.toggle_spec_block_off.hide()
                self.toggle_spec_block_on.enable()
                self.toggle_spec_block_on.show()
                self.suffix_entry_box.set_text("")
                self.suffix_entry_box.rebuild()
                self.suffix_entry_box.disable()
            elif event.ui_element == self.back_button:
                game.all_screens["profile screen"].exit_screen()
                game.all_screens["profile screen"].screen_switches()
                self.kill()
        return super().process_event(event)


class PronounCreation(UIWindow):
    # This window allows the user to create a pronoun set

    def __init__(self, cat):
        super().__init__(
            ui_scale(pygame.Rect((80, 150), (650, 400))),
            window_display_title="Create Cat Pronouns",
            object_id="#change_cat_gender_window",
            resizable=False,
        )
        self.the_cat = cat
        self.conju = 1
        self.box_labels = {}
        self.elements = {}
        self.boxes = {}
        self.checkbox_label = {}
        self.back_button = UIImageButton(
            ui_scale(pygame.Rect((615, 10), (22, 22))),
            "",
            object_id="#exit_window_button",
            container=self,
        )
        self.heading = pygame_gui.elements.UITextBox(
            f"Create new pronouns,"
            f" you have full control. "
            f"<br> Test your created pronouns before saving them!",
            ui_scale(pygame.Rect((15, 50), (380, 75))),
            object_id="#text_box_30_horizcenter_spacing_95",
            manager=MANAGER,
            container=self,
        )

        # Create a sub-container for the Demo frame and sample text
        demo_container_rect = ui_scale(pygame.Rect((397, 57), (425, 592)))
        self.demo_container = pygame_gui.elements.UIScrollingContainer(
            relative_rect=demo_container_rect, manager=MANAGER, container=self
        )

        # Add the Demo frame to the sub-container
        self.elements["demo_frame"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((0, 0), (207, 288))),
            get_box(BoxStyles.FRAME, (207, 288)),
            manager=MANAGER,
            container=self.demo_container,
        )
        # Title of Demo Box
        self.elements["demo title"] = pygame_gui.elements.UITextBox(
            "<b>Demo",
            ui_scale(pygame.Rect((75, 10), (225, 32))),
            object_id="#text_box_34_horizleft",
            manager=MANAGER,
            container=self.demo_container,
        )

        # Add UITextBox for the sample text to the sub-container
        self.sample_text_box = pygame_gui.elements.UITextBox(
            self.get_sample_text(self.the_cat.pronouns[0]),
            ui_scale(pygame.Rect((7, 30), (197, 278))),
            object_id="#text_box_30_horizcenter_spacing_95",
            manager=MANAGER,
            container=self.demo_container,
        )

        self.elements["core_container"] = pygame_gui.core.UIContainer(
            ui_scale(pygame.Rect((0, 0), (375, 400))),
            manager=MANAGER,
            container=self,
        )

        # Tittle
        self.elements["Pronoun Creation"] = pygame_gui.elements.UITextBox(
            "Pronoun Creation",
            ui_scale(pygame.Rect((0, 15), (225, 32))),
            object_id="#text_box_40_horizcenter",
            manager=MANAGER,
            container=self.elements["core_container"],
            anchors={"centerx": "centerx"},
        )

        # Adjusted positions for labels
        self.box_labels["subject"] = pygame_gui.elements.UITextBox(
            "Subject",
            ui_scale(pygame.Rect((87, 100), (100, 30))),
            object_id="#text_box_30_horizcenter_spacing_95",
            manager=MANAGER,
            container=self,
        )

        self.box_labels["object"] = pygame_gui.elements.UITextBox(
            "Object",
            ui_scale(pygame.Rect((212, 100), (100, 30))),
            object_id="#text_box_30_horizcenter_spacing_95",
            manager=MANAGER,
            container=self,
        )

        self.box_labels["poss"] = pygame_gui.elements.UITextBox(
            "Possessive",
            ui_scale(pygame.Rect((25, 170), (100, 30))),
            object_id="#text_box_30_horizcenter_spacing_95",
            manager=MANAGER,
            container=self,
        )

        self.box_labels["inposs"] = pygame_gui.elements.UITextBox(
            "Independent<br>Possessive",
            ui_scale(pygame.Rect((125, 150), (150, 60))),
            object_id="#text_box_30_horizcenter_spacing_95",
            manager=MANAGER,
            container=self,
        )

        self.box_labels["self"] = pygame_gui.elements.UITextBox(
            "Reflexive",
            ui_scale(pygame.Rect((275, 170), (100, 30))),
            object_id="#text_box_30_horizcenter_spacing_95",
            manager=MANAGER,
            container=self,
        )
        
        self.box_labels["parent"] = pygame_gui.elements.UITextBox(
            "Parent",
            ui_scale(pygame.Rect((87, 235), (100, 30))),
            object_id="#text_box_30_horizcenter_spacing_95",
            manager=MANAGER,
            container=self,
        )

        self.box_labels["sibling"] = pygame_gui.elements.UITextBox(
            "Sibling",
            ui_scale(pygame.Rect((215, 235), (100, 30))),
            object_id="#text_box_30_horizcenter_spacing_95",
            manager=MANAGER,
            container=self,
        )

        self.checkbox_label["singular_label"] = pygame_gui.elements.UITextBox(
            "Singular",
            ui_scale(pygame.Rect((60, 350), (100, 30))),
            object_id="#text_box_30_horizcenter_spacing_95",
            manager=MANAGER,
            container=self,
        )
        self.checkbox_label["plural_label"] = pygame_gui.elements.UITextBox(
            "Plural",
            ui_scale(pygame.Rect((180, 350), (100, 30))),
            object_id="#text_box_30_horizcenter_spacing_95",
            manager=MANAGER,
            container=self,
        )

        # Row 1
        self.boxes["subject"] = pygame_gui.elements.UITextEntryLine(
            ui_scale(pygame.Rect((90, 125), (100, 30))),
            placeholder_text=self.the_cat.pronouns[0]["subject"],
            manager=MANAGER,
            container=self,
        )

        self.boxes["object"] = pygame_gui.elements.UITextEntryLine(
            ui_scale(pygame.Rect((215, 125), (100, 30))),
            placeholder_text=self.the_cat.pronouns[0]["object"],
            manager=MANAGER,
            container=self,
        )

        # Row 2
        self.boxes["poss"] = pygame_gui.elements.UITextEntryLine(
            ui_scale(pygame.Rect((25, 200), (100, 30))),
            placeholder_text=self.the_cat.pronouns[0]["poss"],
            manager=MANAGER,
            container=self,
        )

        self.boxes["inposs"] = pygame_gui.elements.UITextEntryLine(
            ui_scale(pygame.Rect((150, 200), (100, 30))),
            placeholder_text=self.the_cat.pronouns[0]["inposs"],
            manager=MANAGER,
            container=self,
        )

        self.boxes["self"] = pygame_gui.elements.UITextEntryLine(
            ui_scale(pygame.Rect((275, 200), (100, 30))),
            placeholder_text=self.the_cat.pronouns[0]["self"],
            manager=MANAGER,
            container=self,
        )

        self.boxes["parent"] = pygame_gui.elements.UITextEntryLine(
            ui_scale(pygame.Rect((90, 275), (100, 30))),
            placeholder_text=self.the_cat.pronouns[0]["parent"],
            manager=MANAGER,
            container=self,
        )

        self.boxes["sibling"] = pygame_gui.elements.UITextEntryLine(
            ui_scale(pygame.Rect((215, 275), (100, 30))),
            placeholder_text=self.the_cat.pronouns[0]["sibling"],
            manager=MANAGER,
            container=self,
        )

        # setting parent/sibling text right away
        # so they can go unedited when creating new pronouns
        self.boxes["parent"].set_text(self.the_cat.pronouns[0]["parent"])
        self.boxes["sibling"].set_text(self.the_cat.pronouns[0]["sibling"])

        # Save Confirmation
        self.pronoun_added = pygame_gui.elements.UITextBox(
            f"Pronoun saved and added to presets!",
            ui_scale(pygame.Rect((225, 350), (400, 40))),
            visible=False,
            object_id="#text_box_30_horizleft",
            manager=MANAGER,
            container=self,
        )

        # Add buttons
        self.buttons = {}
        self.buttons["save_pronouns"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((140, 345), (73, 30))),
            "save",
            get_button_dict(ButtonStyles.SQUOVAL, (73, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
            container=self.elements["core_container"],
            anchors={"centerx": "centerx"},
        )
        # Creating Checkmarks
        self.buttons["singular_unchecked"] = UIImageButton(
            ui_scale(pygame.Rect((40, 350), (34, 34))),
            "",
            object_id="@unchecked_checkbox",
            starting_height=2,
            visible=False,
            manager=MANAGER,
            container=self,
        )
        self.buttons["singular_checked"] = UIImageButton(
            ui_scale(pygame.Rect((40, 350), (34, 34))),
            "",
            object_id="@checked_checkbox",
            starting_height=2,
            visible=False,
            manager=MANAGER,
            container=self,
        )

        self.buttons["plural_unchecked"] = UIImageButton(
            ui_scale(pygame.Rect((165, 350), (34, 34))),
            "",
            object_id="@unchecked_checkbox",
            starting_height=2,
            visible=False,
            manager=MANAGER,
            container=self,
        )
        self.buttons["plural_checked"] = UIImageButton(
            ui_scale(pygame.Rect((165, 350), (34, 34))),
            "",
            object_id="@checked_checkbox",
            starting_height=2,
            visible=False,
            manager=MANAGER,
            container=self,
        )
        if self.the_cat.pronouns[0]["conju"] == 1:
            # self.buttons["plural"].disable()
            self.buttons["plural_checked"].show()
            self.buttons["singular_unchecked"].show()
        else:
            self.buttons["plural_unchecked"].show()
            self.buttons["singular_checked"].show()
            self.conju = 2

        self.buttons["test_set"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((60, 237), (104, 30))),
            "Test Set",
            get_button_dict(ButtonStyles.SQUOVAL, (104, 30)),
            object_id="@buttonstyles_squoval",
            starting_height=2,
            manager=MANAGER,
            container=self.demo_container,
        )

        self.set_blocking(True)

    def get_new_pronouns(self):
        pronoun_template = {
            "name": "",
            "subject": "",
            "object": "",
            "poss": "",
            "inposs": "",
            "self": "",
            "conju": 1,
            "parent": "",
            "sibling": ""
        }

        if sub(r"[^A-Za-z0-9 ]+", "", self.boxes["subject"].get_text()) != "":
            pronoun_template["subject"] = sub(
                r"[^A-Za-z0-9 ]+", "", self.boxes["subject"].get_text()
            )
        if sub(r"[^A-Za-z0-9 ]+", "", self.boxes["object"].get_text()) != "":
            pronoun_template["object"] = sub(
                r"[^A-Za-z0-9 ]+", "", self.boxes["object"].get_text()
            )
        if sub(r"[^A-Za-z0-9 ]+", "", self.boxes["poss"].get_text()) != "":
            pronoun_template["poss"] = sub(
                r"[^A-Za-z0-9 ]+", "", self.boxes["poss"].get_text()
            )
        if sub(r"[^A-Za-z0-9 ]+", "", self.boxes["inposs"].get_text()) != "":
            pronoun_template["inposs"] = sub(
                r"[^A-Za-z0-9 ]+", "", self.boxes["inposs"].get_text()
            )
        if sub(r"[^A-Za-z0-9 ]+", "", self.boxes["self"].get_text()) != "":
            pronoun_template["self"] = sub(
                r"[^A-Za-z0-9 ]+", "", self.boxes["self"].get_text()
            )
        if sub(r"[^A-Za-z0-9 ]+", "", self.boxes["parent"].get_text()) != "":
            pronoun_template["parent"] = sub(
                r"[^A-Za-z0-9 ]+", "", self.boxes["parent"].get_text()
            )
        if sub(r"[^A-Za-z0-9 ]+", "", self.boxes["sibling"].get_text()) != "":
            pronoun_template["sibling"] = sub(
                r"[^A-Za-z0-9 ]+", "", self.boxes["sibling"].get_text()
            )
        if self.conju == 2:
            pronoun_template["conju"] = 2
        # if save button or add to cat is pressed, set 'name' as a counting number thing as an invisible identifier
        newid = len(game.clan.custom_pronouns) + 1
        pronoun_template["ID"] = "custom" + str(newid)
        return pronoun_template

    def is_box_full(self, entry):
        if entry.get_text() == "":
            return False
        else:
            return True

    def are_boxes_full(self):
        values = []
        values.append(self.is_box_full(self.boxes["subject"]))
        values.append(self.is_box_full(self.boxes["object"]))
        values.append(self.is_box_full(self.boxes["poss"]))
        values.append(self.is_box_full(self.boxes["inposs"]))
        values.append(self.is_box_full(self.boxes["self"]))
        values.append(self.is_box_full(self.boxes["parent"]))
        values.append(self.is_box_full(self.boxes["sibling"]))
        for value in values:
            if value is False:
                return False
        return True

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.back_button:
                game.all_screens["change gender screen"].exit_screen()
                game.all_screens["change gender screen"].screen_switches()
                self.kill()
            elif event.ui_element == self.buttons["save_pronouns"]:
                if self.are_boxes_full():
                    print("SAVED")
                    new_pronouns = self.get_new_pronouns()
                    game.clan.custom_pronouns.append(new_pronouns)
                    self.pronoun_added.show()
            elif event.ui_element == self.buttons["singular_unchecked"]:
                self.buttons["plural_checked"].hide()
                self.buttons["singular_unchecked"].hide()
                self.buttons["plural_unchecked"].show()
                self.buttons["singular_checked"].show()
                self.conju = 2
            elif event.ui_element == self.buttons["plural_unchecked"]:
                """self.buttons["plural"].enable()"""
                self.buttons["plural_checked"].show()
                self.buttons["singular_unchecked"].show()
                self.buttons["plural_unchecked"].hide()
                self.buttons["singular_checked"].hide()
                self.conju = 1
            elif event.ui_element == self.buttons["test_set"]:
                self.sample_text_box.kill()
                self.sample_text_box = pygame_gui.elements.UITextBox(
                    self.get_sample_text(self.get_new_pronouns()),
                    ui_scale(pygame.Rect((7, 30), (197, 278))),
                    object_id="#text_box_30_horizcenter_spacing_95",
                    manager=MANAGER,
                    container=self.demo_container,
                )
        return super().process_event(event)

    def get_sample_text(self, pronouns):
        text = ""
        subject = f"{pronouns['subject']} are quick. <br>"
        if pronouns["conju"] == 2:
            subject = f"{pronouns['subject']} is quick. <br>"
        text += subject.capitalize()
        text += f"Everyone saw {pronouns['object']}. <br>"
        poss = f"{pronouns['poss']} paw slipped.<br>"
        text += poss.capitalize()
        text += f"That den is {pronouns['inposs']}. <br>"
        text += f"This cat hunts by {pronouns['self']}.<br>"

        text += f"This cat wants to be a {pronouns['parent']} someday.<br>"
        text += f"This cat is a good {pronouns['sibling']}.<br>"

        # Full Sentence Example, doesn't fit.
        """sentence = f"{pronouns['poss']} keen sense alerted {pronouns['object']} to prey and {pronouns['subject']} decided to treat {pronouns['self']} by catching prey that would be {pronouns['inposs']} alone to eat. "
        if pronouns["conju"] == 2:
            sentence = f"{pronouns['poss']} keen sense alerted {pronouns['object']} to prey and {pronouns['subject']} decides to treat {pronouns['self']} by catching prey that would be {pronouns['inposs']} alone to eat. "
        text += sentence.capitalize()"""
        # print (len(game.clan.custom_pronouns)+1)
        return text


class KillCat(UIWindow):
    """This window allows the user to kill the selected cat"""

    def __init__(self, cat):
        super().__init__(
            ui_scale(pygame.Rect((300, 200), (450, 200))),
            window_display_title="Kill Cat",
            object_id="#kill_cat_window",
            resizable=False,
        )
        self.history = History()
        self.the_cat = cat
        self.take_all = False
        self.back_button = UIImageButton(
            ui_scale(pygame.Rect((420, 5), (22, 22))),
            "",
            object_id="#exit_window_button",
            container=self,
        )
        cat_dict = {"m_c": (str(self.the_cat.name), choice(self.the_cat.pronouns))}
        self.heading = pygame_gui.elements.UITextBox(
            f"<b>-- How did this cat die? --</b>",
            ui_scale(pygame.Rect((10, 10), (400, 75))),
            object_id="#text_box_30_horizcenter_spacing_95",
            manager=MANAGER,
            container=self,
        )

        self.one_life_check = UIImageButton(
            ui_scale(pygame.Rect((25, 150), (34, 34))),
            "",
            object_id="@unchecked_checkbox",
            tool_tip_text=process_text(
                "If this is checked, the leader will lose all {PRONOUN/m_c/poss} lives",
                cat_dict,
            ),
            manager=MANAGER,
            container=self,
        )
        self.all_lives_check = UIImageButton(
            ui_scale(pygame.Rect((25, 150), (34, 34))),
            "",
            object_id="@checked_checkbox",
            tool_tip_text=process_text(
                "If this is checked, the leader will lose all {PRONOUN/m_c/poss} lives",
                cat_dict,
            ),
            manager=MANAGER,
            container=self,
        )

        if self.the_cat.status == "leader":
            self.done_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((347, 152), (77, 30))),
                "done",
                get_button_dict(ButtonStyles.SQUOVAL, (77, 30)),
                object_id="@buttonstyles_squoval",
                manager=MANAGER,
                container=self,
            )

            self.prompt = process_text(
                "This cat died when {PRONOUN/m_c/subject}...", cat_dict
            )
            self.initial = process_text(
                "{VERB/m_c/were/was} killed by a higher power.", cat_dict
            )

            self.all_lives_check.hide()
            self.life_text = pygame_gui.elements.UITextBox(
                "Take all the leader's lives",
                ui_scale(pygame.Rect((60, 147), (300, 40))),
                object_id="#text_box_30_horizleft",
                manager=MANAGER,
                container=self,
            )
            self.beginning_prompt = pygame_gui.elements.UITextBox(
                self.prompt,
                ui_scale(pygame.Rect((25, 30), (450, 40))),
                object_id="#text_box_30_horizleft",
                manager=MANAGER,
                container=self,
            )

            self.death_entry_box = pygame_gui.elements.UITextEntryBox(
                ui_scale(pygame.Rect((25, 65), (400, 75))),
                initial_text=self.initial,
                object_id="text_entry_line",
                manager=MANAGER,
                container=self,
            )

        elif History.get_death_or_scars(self.the_cat, death=True):
            # This should only occur for retired leaders.

            self.prompt = process_text(
                "This cat died when {PRONOUN/m_c/subject}...", cat_dict
            )
            self.initial = process_text(
                "{VERB/m_c/were/was} killed by something unknowable to even StarClan",
                cat_dict,
            )
            self.all_lives_check.hide()
            self.one_life_check.hide()

            self.beginning_prompt = pygame_gui.elements.UITextBox(
                self.prompt,
                ui_scale(pygame.Rect((25, 30), (450, 40))),
                object_id="#text_box_30_horizleft",
                manager=MANAGER,
                container=self,
            )

            self.death_entry_box = pygame_gui.elements.UITextEntryBox(
                ui_scale(pygame.Rect((25, 65), (400, 75))),
                initial_text=self.initial,
                object_id="text_entry_line",
                manager=MANAGER,
                container=self,
            )

            self.done_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((186, 152), (77, 30))),
                "done",
                get_button_dict(ButtonStyles.SQUOVAL, (77, 30)),
                object_id="@buttonstyles_squoval",
                manager=MANAGER,
                container=self,
            )
        else:
            self.initial = "This cat was killed by a higher power."
            self.prompt = None
            self.all_lives_check.hide()
            self.one_life_check.hide()

            self.death_entry_box = pygame_gui.elements.UITextEntryBox(
                ui_scale(pygame.Rect((25, 55), (400, 75))),
                initial_text=self.initial,
                object_id="text_entry_line",
                manager=MANAGER,
                container=self,
            )

            self.done_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((186, 152), (77, 30))),
                "done",
                get_button_dict(ButtonStyles.SQUOVAL, (77, 30)),
                object_id="@buttonstyles_squoval",
                manager=MANAGER,
                container=self,
            )
        self.set_blocking(True)

    def process_event(self, event):
        super().process_event(event)

        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.done_button:
                death_message = sub(
                    r"[^A-Za-z0-9<->/.()*'&#!?,| _]+",
                    "",
                    self.death_entry_box.get_text(),
                )
                if self.the_cat.status == "leader":
                    if death_message.startswith("was"):
                        death_message = death_message.replace(
                            "was", "{VERB/m_c/were/was}", 1
                        )
                    elif death_message.startswith("were"):
                        death_message = death_message.replace(
                            "were", "{VERB/m_c/were/was}", 1
                        )

                    if self.take_all:
                        game.clan.leader_lives = 0
                    else:
                        game.clan.leader_lives -= 1

                self.the_cat.die()
                self.history.add_death(self.the_cat, death_message)
                update_sprite(self.the_cat)
                game.all_screens["profile screen"].exit_screen()
                game.all_screens["profile screen"].screen_switches()
                self.kill()
            elif event.ui_element == self.all_lives_check:
                self.take_all = False
                self.all_lives_check.hide()
                self.one_life_check.show()
            elif event.ui_element == self.one_life_check:
                self.take_all = True
                self.all_lives_check.show()
                self.one_life_check.hide()
            elif event.ui_element == self.back_button:
                game.all_screens["profile screen"].exit_screen()
                game.all_screens["profile screen"].screen_switches()
                self.kill()

        return super().process_event(event)


class UpdateWindow(UIWindow):
    def __init__(self, last_screen, announce_restart_callback):
        super().__init__(
            ui_scale(pygame.Rect((250, 200), (300, 160))),
            window_display_title="Game Over",
            object_id="#game_over_window",
            resizable=False,
        )
        self.set_blocking(True)
        self.last_screen = last_screen
        self.update_message = pygame_gui.elements.UITextBox(
            f"Update in progress.",
            ui_scale(pygame.Rect((20, 10), (260, -1))),
            object_id="#text_box_30_horizcenter_spacing_95",
            starting_height=4,
            container=self,
        )
        self.announce_restart_callback = announce_restart_callback

        self.step_text = UITextBoxTweaked(
            f"Downloading update...",
            ui_scale(pygame.Rect((20, 40), (260, -1))),
            line_spacing=1,
            object_id="#text_box_30_horizcenter",
            container=self,
        )

        self.progress_bar = UIUpdateProgressBar(
            ui_scale(pygame.Rect((20, 65), (260, 45))),
            self.step_text,
            object_id="progress_bar",
            container=self,
        )

        self.update_thread = threading.Thread(
            target=self_update,
            daemon=True,
            args=(
                UpdateChannel(get_version_info().release_channel),
                self.progress_bar,
                announce_restart_callback,
            ),
        )
        self.update_thread.start()

        self.cancel_button = UIImageButton(
            ui_scale(pygame.Rect((200, 115), (78, 30))),
            "",
            object_id="#cancel_button",
            container=self,
        )

        self.cancel_button.enable()

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.cancel_button:
                self.kill()

        return super().process_event(event)


class AnnounceRestart(UIWindow):
    def __init__(self, last_screen):
        super().__init__(
            ui_scale(pygame.Rect((250, 200), (300, 90))),
            window_display_title="Game Over",
            object_id="#game_over_window",
            resizable=False,
        )
        self.last_screen = last_screen
        self.announce_message = UITextBoxTweaked(
            f"The game will automatically restart in 3...",
            ui_scale(pygame.Rect((20, 20), (260, -1))),
            line_spacing=1,
            object_id="#text_box_30_horizcenter",
            container=self,
        )

        threading.Thread(target=self.update_text, daemon=True).start()

    def update_text(self):
        for i in range(2, 0, -1):
            time.sleep(1)
            self.announce_message.set_text(
                f"The game will automatically restart in {i}..."
            )


class UpdateAvailablePopup(UIWindow):
    def __init__(self, last_screen, show_checkbox: bool = False):
        super().__init__(
            ui_scale(pygame.Rect((200, 200), (400, 230))),
            window_display_title="Update available",
            object_id="#game_over_window",
            resizable=False,
        )
        self.set_blocking(True)
        self.last_screen = last_screen

        self.begin_update_title = UIImageButton(
            ui_scale(pygame.Rect((97, 15), (200, 40))),
            "",
            object_id="#new_update_button",
            container=self,
        )

        latest_version_number = "{:.16}".format(get_latest_version_number())
        current_version_number = "{:.16}".format(get_version_info().version_number)

        self.game_over_message = UITextBoxTweaked(
            f"<strong>Update to LifeGen {latest_version_number}</strong>",
            ui_scale(pygame.Rect((10, 80), (400, -1))),
            line_spacing=0.8,
            object_id="#update_popup_title",
            container=self,
        )

        self.game_over_message = UITextBoxTweaked(
            f"Your current version: {current_version_number}",
            ui_scale(pygame.Rect((11, 100), (400, -1))),
            line_spacing=0.8,
            object_id="#current_version",
            container=self,
        )

        self.game_over_message = UITextBoxTweaked(
            f"Install update now?",
            ui_scale(pygame.Rect((10, 131), (200, -1))),
            line_spacing=0.8,
            object_id="#text_box_30",
            container=self,
        )

        self.box_unchecked = UIImageButton(
            ui_scale(pygame.Rect((7, 183), (34, 34))),
            "",
            object_id="@unchecked_checkbox",
            container=self,
        )
        self.box_checked = UIImageButton(
            ui_scale(pygame.Rect((7, 183), (34, 34))),
            "",
            object_id="@checked_checkbox",
            container=self,
        )
        self.box_text = UITextBoxTweaked(
            f"Don't ask again",
            ui_scale(pygame.Rect((39, 190), (125, -1))),
            line_spacing=0.8,
            object_id="#text_box_30",
            container=self,
        )

        self.continue_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((278, 185), (102, 30))),
            "continue",
            get_button_dict(ButtonStyles.SQUOVAL, (77, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )
        self.continue_button.disable()

        self.cancel_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((187, 185), (78, 30))),
            "cancel",
            get_button_dict(ButtonStyles.SQUOVAL, (77, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )

        self.close_button = UIImageButton(
            ui_scale(pygame.Rect((740, 10), (44, 44))),
            "",
            object_id="#exit_window_button",
            container=self,
        )

        if show_checkbox:
            self.box_unchecked.enable()
            self.box_checked.hide()
        else:
            self.box_checked.hide()
            self.box_unchecked.hide()
            self.box_text.hide()

        self.continue_button.enable()
        self.cancel_button.enable()
        self.close_button.enable()

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.continue_button:
                url = "https://mods.clangen.io/LifeGen/download"

                if get_version_info().is_dev():
                    url = "https://mods.clangen.io/LifeGen/download"

                if platform.system() == "Darwin":
                    subprocess.Popen(["open", "-u", url])
                elif platform.system() == "Windows":
                    os.system(f"start \"\" {url}")
                elif platform.system() == "Linux":
                    subprocess.Popen(["xdg-open", url])
            elif (
                event.ui_element == self.close_button
                or event.ui_element == self.cancel_button
            ):
                self.kill()
            elif event.ui_element == self.box_unchecked:
                self.box_unchecked.disable()
                self.box_unchecked.hide()
                self.box_checked.enable()
                self.box_checked.show()
                with open(
                    f"{get_cache_dir()}/suppress_update_popup", "w"
                ) as write_file:
                    write_file.write(get_latest_version_number())
            elif event.ui_element == self.box_checked:
                self.box_checked.disable()
                self.box_checked.hide()
                self.box_unchecked.enable()
                self.box_unchecked.show()
                if os.path.exists(f"{get_cache_dir()}/suppress_update_popup"):
                    os.remove(f"{get_cache_dir()}/suppress_update_popup")
        return super().process_event(event)

    def announce_restart_callback(self):
        y = AnnounceRestart(game.switches["cur_screen"])
        y.update(1)


class ChangelogPopup(UIWindow):
    def __init__(self, last_screen):
        super().__init__(
            ui_scale(pygame.Rect((150, 150), (500, 400))),
            window_display_title="Changelog",
            object_id="#game_over_window",
            resizable=False,
        )
        self.set_blocking(True)

        self.last_screen = last_screen
        self.changelog_popup_title = UITextBoxTweaked(
            f"<strong>What's New</strong>",
            ui_scale(pygame.Rect((0, 10), (500, -1))),
            line_spacing=1,
            object_id="#changelog_popup_title",
            container=self,
            anchors={"centerx": "centerx"},
        )

        current_version_number = "{:.16}".format(get_version_info().version_number)

        self.changelog_popup_subtitle = UITextBoxTweaked(
            f"Version {current_version_number}",
            ui_scale(pygame.Rect((0, 35), (500, -1))),
            line_spacing=1,
            object_id="#changelog_popup_subtitle",
            container=self,
            anchors={"centerx": "centerx"},
        )

        dynamic_changelog = False
        
        with open("changelog.txt", "r") as read_file:
            file_cont = read_file.read()

        self.changelog_text = UITextBoxTweaked(
            file_cont,
            ui_scale(pygame.Rect((10, 65), (480, 325))),
            object_id="#text_box_30",
            line_spacing=0.95,
            starting_height=2,
            container=self,
            manager=MANAGER,
        )

        self.close_button = UIImageButton(
            ui_scale(pygame.Rect((470, 5), (22, 22))),
            "",
            object_id="#exit_window_button",
            starting_height=2,
            container=self,
        )

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.close_button:
                self.kill()
        return super().process_event(event)


class RelationshipLog(UIWindow):
    """This window allows the user to see the relationship log of a certain relationship."""

    def __init__(self, relationship, disable_button_list, hide_button_list):
        super().__init__(
            ui_scale(pygame.Rect((273, 122), (505, 550))),
            window_display_title="Relationship Log",
            object_id="#relationship_log_window",
            resizable=False,
        )
        self.hide_button_list = hide_button_list
        for button in self.hide_button_list:
            button.hide()

        self.exit_button = UIImageButton(
            ui_scale(pygame.Rect((470, 7), (22, 22))),
            "",
            object_id="#exit_window_button",
            container=self,
        )
        self.back_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((25, 645), (105, 30))),
            get_arrow(2) + "Back",
            get_button_dict(ButtonStyles.SQUOVAL, (105, 30)),
            object_id="@buttonstyles_squoval",
        )
        self.log_icon = UISurfaceImageButton(
            ui_scale(pygame.Rect((222, 404), (34, 34))),
            Icon.NOTEPAD,
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
        )
        self.closing_buttons = [self.exit_button, self.back_button, self.log_icon]

        self.disable_button_list = []
        for button in disable_button_list:
            if button.is_enabled:
                self.disable_button_list.append(button)
                button.disable()

        opposite_log_string = None
        if not relationship.opposite_relationship:
            relationship.link_relationship()
        if (
            relationship.opposite_relationship
            and len(relationship.opposite_relationship.log) > 0
        ):
            opposite_log_string = f"{f'<br>-----------------------------<br>'.join(relationship.opposite_relationship.log)}<br>"

        log_string = (
            f"{f'<br>-----------------------------<br>'.join(relationship.log)}<br>"
            if len(relationship.log) > 0
            else "There are no relationship logs."
        )

        if not opposite_log_string:
            self.log = pygame_gui.elements.UITextBox(
                log_string,
                ui_scale(pygame.Rect((15, 45), (476, 425))),
                object_id="#text_box_30_horizleft",
                manager=MANAGER,
                container=self,
            )
        else:
            self.log = pygame_gui.elements.UITextBox(
                log_string,
                ui_scale(pygame.Rect((15, 45), (476, 250))),
                object_id="#text_box_30_horizleft",
                manager=MANAGER,
                container=self,
            )
            self.opp_heading = pygame_gui.elements.UITextBox(
                "<u><b>OTHER PERSPECTIVE</b></u>",
                ui_scale(pygame.Rect((15, 275), (476, 280))),
                object_id="#text_box_30_horizleft",
                manager=MANAGER,
                container=self,
            )
            self.opp_heading.disable()
            self.opp_log = pygame_gui.elements.UITextBox(
                opposite_log_string,
                ui_scale(pygame.Rect((15, 305), (476, 232))),
                object_id="#text_box_30_horizleft",
                manager=MANAGER,
                container=self,
            )

    def closing_process(self):
        """Handles to enable and kill all processes when an exit button is clicked."""
        for button in self.disable_button_list:
            button.enable()

        for button in self.hide_button_list:
            button.show()
            button.enable()
        self.log_icon.kill()
        self.exit_button.kill()
        self.back_button.kill()
        self.kill()

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element in self.closing_buttons:
                self.closing_process()
        return super().process_event(event)


class SaveError(UIWindow):
    def __init__(self, error_text):
        super().__init__(
            ui_scale(pygame.Rect((150, 150), (500, 400))),
            window_display_title="Changelog",
            object_id="#game_over_window",
            resizable=False,
        )
        self.set_blocking(True)
        self.changelog_popup_title = pygame_gui.elements.UITextBox(
            f"<strong>Saving Failed!</strong>\n\n{error_text}",
            ui_scale(pygame.Rect((20, 10), (445, 375))),
            object_id="#text_box_30",
            container=self,
        )

        self.close_button = UIImageButton(
            ui_scale(pygame.Rect((470, 5), (22, 22))),
            "",
            object_id="#exit_window_button",
            starting_height=2,
            container=self,
        )

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.close_button:
                self.kill()
        return super().process_event(event)


class SaveAsImage(UIWindow):
    def __init__(self, image_to_save, file_name):
        super().__init__(
            ui_scale(pygame.Rect((200, 175), (400, 250))),
            object_id="#game_over_window",
            resizable=False,
        )

        self.set_blocking(True)

        self.image_to_save = image_to_save
        self.file_name = file_name
        self.scale_factor = 1

        button_layout_rect = ui_scale(pygame.Rect((0, 5), (22, 22)))
        button_layout_rect.topright = ui_scale_offset((-1, 5))

        self.close_button = UIImageButton(
            button_layout_rect,
            "",
            object_id="#exit_window_button",
            starting_height=2,
            container=self,
            anchors={"right": "right", "top": "top"},
        )

        self.save_as_image = UISurfaceImageButton(
            ui_scale(pygame.Rect((0, 90), (135, 30))),
            "Save as Image",
            get_button_dict(ButtonStyles.SQUOVAL, (135, 30)),
            object_id="@buttonstyles_squoval",
            sound_id="save",
            container=self,
            anchors={"centerx": "centerx"},
        )

        self.open_data_directory_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((0, 175), (178, 30))),
            "Open Data Directory",
            get_button_dict(ButtonStyles.SQUOVAL, (178, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
            starting_height=2,
            tool_tip_text="Opens the data directory. "
            "This is where save files, images, "
            "and logs are stored.",
            anchors={"centerx": "centerx"},
        )

        self.small_size_button = UIImageButton(
            ui_scale(pygame.Rect((54, 50), (97, 30))),
            "",
            object_id="#image_small_button",
            container=self,
            starting_height=2,
        )
        self.small_size_button.disable()

        self.medium_size_button = UIImageButton(
            ui_scale(pygame.Rect((151, 50), (97, 30))),
            "",
            object_id="#image_medium_button",
            container=self,
            starting_height=2,
        )

        self.large_size_button = UIImageButton(
            ui_scale(pygame.Rect((248, 50), (97, 30))),
            "",
            object_id="#image_large_button",
            container=self,
            starting_height=2,
        )

        self.confirm_text = pygame_gui.elements.UITextBox(
            "",
            ui_scale(pygame.Rect((5, 125), (390, 45))),
            object_id="#text_box_26_horizcenter_vertcenter_spacing_95",
            container=self,
            starting_height=2,
        )

    def save_image(self):
        file_name = self.file_name
        file_number = ""
        i = 0
        while True:
            if os.path.isfile(
                f"{get_saved_images_dir()}/{file_name + file_number}.png"
            ):
                i += 1
                file_number = f"_{i}"
            else:
                break

        scaled_image = pygame.transform.scale_by(self.image_to_save, self.scale_factor)
        pygame.image.save(
            scaled_image, f"{get_saved_images_dir()}/{file_name + file_number}.png"
        )
        return f"{file_name + file_number}.png"

    def process_event(self, event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.close_button:
                self.kill()
            elif event.ui_element == self.open_data_directory_button:
                if system() == "Darwin":
                    subprocess.Popen(["open", "-R", get_data_dir()])
                elif system() == "Windows":
                    os.startfile(get_data_dir())  # pylint: disable=no-member
                elif system() == "Linux":
                    try:
                        subprocess.Popen(["xdg-open", get_data_dir()])
                    except OSError:
                        logger.exception("Failed to call to xdg-open.")
                return True
            elif event.ui_element == self.save_as_image:
                file_name = self.save_image()
                self.confirm_text.set_text(
                    f"Saved as {file_name} in the saved_images folder"
                )
            elif event.ui_element == self.small_size_button:
                self.scale_factor = 1
                self.small_size_button.disable()
                self.medium_size_button.enable()
                self.large_size_button.enable()
            elif event.ui_element == self.medium_size_button:
                self.scale_factor = 4
                self.small_size_button.enable()
                self.medium_size_button.disable()
                self.large_size_button.enable()
            elif event.ui_element == self.large_size_button:
                self.scale_factor = 6
                self.small_size_button.enable()
                self.medium_size_button.enable()
                self.large_size_button.disable()

        return super().process_event(event)


class EventLoading(UIWindow):
    """Handles the event loading animation"""

    def __init__(self, pos):
        if pos is None:
            pos = (350, 300)

        super().__init__(
            ui_scale(pygame.Rect(pos, (100, 100))),
            window_display_title="Game Over",
            object_id="#loading_window",
            resizable=False,
        )

        self.set_blocking(True)
        game.switches['window_open'] = True

        self.frames = self.load_images()
        self.end_animation = False

        self.animated_image = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect(0, 0, 100, 100)),
            self.frames[0],
            container=self,
        )

        self.animation_thread = threading.Thread(target=self.animate)
        self.animation_thread.start()

    @staticmethod
    def load_images():
        frames = []
        for i in range(0, 16):
            frames.append(
                pygame.image.load(f"resources/images/loading_animate/timeskip/{i}.png")
            )

        return frames

    def animate(self):
        """Loops over the event frames and displays the animation"""
        i = 0
        while not self.end_animation:
            i = (i + 1) % (len(self.frames))

            self.animated_image.set_image(self.frames[i])
            time.sleep(0.125)

    def kill(self):
        self.end_animation = True
        game.switches['window_open'] = False
        super().kill()

class PickPath(UIWindow):
    def __init__(self, last_screen):
        super().__init__(ui_scale(pygame.Rect((220, 175), (400, 250))),
                         window_display_title='Choose your Path',
                         object_id='#game_over_window',
                         resizable=False)
        self.set_blocking(True)
        game.switches['window_open'] = True
        self.clan_name = str(game.clan.name + 'Clan')
        self.last_screen = last_screen
        self.pick_path_message = UITextBoxTweaked(
            f"You have an important decision to make...",
            ui_scale(pygame.Rect((20, 20), (360, -1))),
            line_spacing=1,
            object_id="#text_box_30_horizcenter",
            container=self
        )

        self.begin_anew_button = UIImageButton(
            ui_scale(pygame.Rect((15, 80), (75, 75))),
            "",
            object_id="#med",
            container=self,
            tool_tip_text='Choose to become a medicine cat apprentice'
        )
        self.not_yet_button = UIImageButton(
            ui_scale(pygame.Rect((110, 80), (75, 75))),
            "",
            object_id="#warrior",
            container=self,
            tool_tip_text='Choose to become a warrior apprentice'

        )
        self.mediator_button = UIImageButton(
            ui_scale(pygame.Rect((205, 80), (75, 75))),
            "",
            object_id="#mediator",
            container=self,
            tool_tip_text='Choose to become a mediator apprentice'

        )
        self.queen_button = UIImageButton(
            ui_scale(pygame.Rect((300, 80), (75, 75))),
            "",
            object_id="#queen",
            container=self,
            tool_tip_text="Choose to become a queen's apprentice"

        )
        self.random_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((170, 175), (50, 50))),
            Icon.DICE,
            get_button_dict(ButtonStyles.ICON, (50, 50)),
            object_id="@buttonstyles_icon",
            container=self,
            tool_tip_text="Random"
        )

        self.not_yet_button.enable()
        self.begin_anew_button.enable()
        self.mediator_button.enable()
        self.random_button.enable()

    def process_event(self, event):
        super().process_event(event)

        try:
            status = ""
            if event.type == pygame_gui.UI_BUTTON_START_PRESS:
                if event.ui_element == self.begin_anew_button:
                    game.switches['window_open'] = False
                    if game.clan.your_cat.moons < 12:
                        status = 'medicine cat apprentice'
                    else:
                        status = 'medicine cat'
                elif event.ui_element == self.not_yet_button:
                    game.switches['window_open'] = False
                    if game.clan.your_cat.moons < 12:
                        status = 'apprentice'
                    else:
                        status = 'warrior'
                elif event.ui_element == self.mediator_button:
                    game.switches['window_open'] = False
                    if game.clan.your_cat.moons < 12:
                        status = 'mediator apprentice'
                    else:
                        status = 'mediator'
                elif event.ui_element == self.queen_button:
                    game.switches['window_open'] = False
                    if game.clan.your_cat.moons < 12:
                        status = "queen's apprentice"
                    else:
                        status = "queen"
                elif event.ui_element == self.random_button:
                    game.switches['window_open'] = False
                    if game.clan.your_cat.moons < 12:
                        status = random.choice(['mediator apprentice','apprentice','medicine cat apprentice', "queen's apprentice"])
                    else:
                        status = random.choice(['mediator','warrior','medicine cat', "queen"])
                
                game.clan.your_cat.status_change(status)
                self.kill()
        except:
            print('Error with PickPath window!')


class DeathScreen(UIWindow):
    def __init__(self, last_screen):
        super().__init__(ui_scale(pygame.Rect((155, 175), (490, 250))),
                         window_display_title='You have died',
                         object_id='#game_over_window',
                         resizable=False)
        self.set_blocking(True)
        game.switches['window_open'] = True
        self.clan_name = str(game.clan.name + 'Clan')
        self.last_screen = last_screen
        self.pick_path_message = UITextBoxTweaked(
            f"<b>You are dead.</b>\nWhat will you do now?",
            ui_scale(pygame.Rect((20, 10), (435, -1))),
            line_spacing=1,
            object_id="#text_box_30_horizcenter",
            container=self
        )

        self.begin_anew_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((35, 75), (210, 30))),
            Icon.DICE + " Start a new Clan",
            get_button_dict(ButtonStyles.SQUOVAL, (210, 30)),
            container=self,
            object_id="@buttonstyles_squoval",
        )

        self.mediator_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((35, 115), (170, 30))),
            Icon.CAT_HEAD + " Switch cats",
            get_button_dict(ButtonStyles.SQUOVAL, (170, 30)),
            container=self,
            object_id="@buttonstyles_squoval",
        )

        self.mediator_button2 = UISurfaceImageButton(
            ui_scale(pygame.Rect((265, 75), (170, 30))),
            Icon.STARCLAN + " Revive",
            get_button_dict(ButtonStyles.SQUOVAL, (170, 30)),
            container=self,
            object_id="@buttonstyles_squoval",
        )

        self.mediator_button4 = UISurfaceImageButton(
            ui_scale(pygame.Rect((225, 115), (210, 30))),
            Icon.PAW + " Start a new life",
            get_button_dict(ButtonStyles.SQUOVAL, (210, 30)),
            container=self,
            object_id="@buttonstyles_squoval",
        )

        self.mediator_button3 = UIImageButton(
            ui_scale(pygame.Rect((115, 165), (249, 48))),
            "",
            object_id="#continue_dead_button",
            container=self,
        )

        

        self.begin_anew_button.enable()
        self.mediator_button.enable()
        if game.clan.your_cat.revives < 5:
            self.mediator_button2.enable()
        if (game.clan.your_cat.dead_for >= game.config["fading"]["age_to_fade"]) and game.clan.your_cat.prevent_fading == False:
            self.mediator_button2.disable()
        self.mediator_button3.enable()
        self.mediator_button4.enable()

    def process_event(self, event):
        super().process_event(event)

        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.begin_anew_button: 
                game.last_screen_forupdate = None
                game.switches['window_open'] = False
                game.switches['cur_screen'] = 'start screen'
                game.switches['continue_after_death'] = False
                self.begin_anew_button.kill()
                self.pick_path_message.kill()
                self.mediator_button.kill()
                self.mediator_button2.kill()
                self.mediator_button3.kill()
                self.mediator_button4.kill()
                self.kill()
                game.all_screens['events screen'].exit_screen()
            elif event.ui_element == self.mediator_button:
                game.last_screen_forupdate = None
                game.switches['window_open'] = False
                game.switches['cur_screen'] = "choose reborn screen"
                game.switches['continue_after_death'] = False
                self.begin_anew_button.kill()
                self.pick_path_message.kill()
                self.mediator_button.kill()
                self.mediator_button2.kill()
                self.mediator_button3.kill()
                self.mediator_button4.kill()
                self.kill()
                game.all_screens['events screen'].exit_screen()
            elif event.ui_element == self.mediator_button2:
                game.clan.your_cat.revives +=1
                game.clan.your_cat.dead = False
                game.clan.your_cat.df = False
                if not game.clan.your_cat.outside:
                    game.clan.your_cat.outside = False
                if game.clan.your_cat.status in ["rogue", "kittypet", "former Clancat", "loner"]:
                    game.clan.your_cat.status = "exiled"
                    # cant play as an outsider yet gotta cheese it for now
                game.clan.your_cat.dead_for = 0
                game.clan.your_cat.moons+=1
                game.clan.your_cat.update_mentor()
                game.switches['continue_after_death'] = False
                if game.clan.your_cat.outside:
                    game.clan.add_to_clan(game.clan.your_cat)
                if game.clan.your_cat.ID in game.clan.starclan_cats:
                    game.clan.starclan_cats.remove(game.clan.your_cat.ID)
                if game.clan.your_cat.ID in game.clan.darkforest_cats:
                    game.clan.darkforest_cats.remove(game.clan.your_cat.ID)
                if game.clan.your_cat.ID in game.clan.unknown_cats:
                    game.clan.unknown_cats.remove(game.clan.your_cat.ID)
                you = game.clan.your_cat
                
                if you.moons == 0 and you.status != "newborn":
                    you.status = 'newborn'
                elif you.moons < 6 and you.status != "kitten":
                    you.status = "kitten"
                elif you.moons >= 6 and you.status == "kitten":
                    you.status = "apprentice"
                    you.name.status = "apprentice"

                game.clan.your_cat.thought = "Is surprised to find themselves back in the Clan"
                game.last_screen_forupdate = None
                game.switches['window_open'] = False
                with open("resources/dicts/events/lifegen_events/revival.json", "r") as read_file:
                    revival_json = ujson.loads(read_file.read())['revival']
                
                game.next_events_list.append(Single_Event(choice(revival_json), 'alert'))
                game.switches['cur_screen'] = "events screen"
                self.begin_anew_button.kill()
                self.pick_path_message.kill()
                self.mediator_button.kill()
                self.mediator_button2.kill()
                self.mediator_button3.kill()
                self.mediator_button4.kill()
                self.kill()
            elif event.ui_element == self.mediator_button3:
                game.last_screen_forupdate = None
                game.switches['window_open'] = False
                game.switches['cur_screen'] = "events screen"
                game.switches['continue_after_death'] = True
                self.begin_anew_button.kill()
                self.pick_path_message.kill()
                self.mediator_button.kill()
                self.mediator_button2.kill()
                self.mediator_button3.kill()
                self.mediator_button4.kill()
                self.kill()
            elif event.ui_element == self.mediator_button4:
                game.last_screen_forupdate = None
                game.switches['window_open'] = False
                game.switches['customise_new_life'] = True
                game.switches['cur_screen'] = "make clan screen"
                game.switches['continue_after_death'] = False
                self.begin_anew_button.kill()
                self.pick_path_message.kill()
                self.mediator_button.kill()
                self.mediator_button2.kill()
                self.mediator_button3.kill()
                self.mediator_button4.kill()
                self.kill()
                game.all_screens['events screen'].exit_screen()

class DeputyScreen(UIWindow):
    def __init__(self, last_screen):
        super().__init__(ui_scale(pygame.Rect((250, 200), (300, 180))),
                        window_display_title='Choose your deputy',
                        object_id='#game_over_window',
                        resizable=False)
        self.set_blocking(True)
        game.switches['window_open'] = True
        self.clan_name = str(game.clan.name + 'Clan')
        self.last_screen = last_screen
        self.pick_path_message = UITextBoxTweaked(
            f"<b>You need to choose a deputy.</b>\nWho will it be?",
            ui_scale(pygame.Rect((20, 20), (250, -1))),
            line_spacing=1,
            object_id="#text_box_30_horizcenter",
            container=self
        )

        self.begin_anew_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((55, 95), (80, 30))),
            "skip",
            get_button_dict(ButtonStyles.SQUOVAL, (80, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )
        self.mediator_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((160, 95), (80, 30))),
            "choose",
            get_button_dict(ButtonStyles.SQUOVAL, (80, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )
        
        self.begin_anew_button.enable()
        self.mediator_button.enable()


    def process_event(self, event):
        super().process_event(event)
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.begin_anew_button:
                game.last_screen_forupdate = None
                game.switches['window_open'] = False
                self.begin_anew_button.kill()
                self.pick_path_message.kill()
                self.mediator_button.kill()
                self.kill()
            elif event.ui_element == self.mediator_button:
                game.last_screen_forupdate = None
                if game.clan.deputy:
                    game.clan.deputy.status_change('warrior')
                game.switches['window_open'] = False
                game.switches['cur_screen'] = "deputy screen"
                self.begin_anew_button.kill()
                self.pick_path_message.kill()
                self.mediator_button.kill()
                self.kill()
                game.all_screens['events screen'].exit_screen()

class NameKitsWindow(UIWindow):
    def __init__(self, last_screen):
        super().__init__(ui_scale(pygame.Rect((250, 200), (300, 150))),
                         window_display_title='Name Kits',
                         object_id='#game_over_window',
                         resizable=False)
        self.set_blocking(True)
        game.switches['window_open'] = True
        self.clan_name = str(game.clan.name + 'Clan')
        self.last_screen = last_screen
        self.pick_path_message = UITextBoxTweaked(
            f"<b>You have kits!</b>\nWhat will you name them?",
            ui_scale(pygame.Rect((20, 20), (250, -1))),
            line_spacing=1,
            object_id="#text_box_30_horizcenter",
            container=self
        )
        self.begin_anew_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((55, 95), (80, 30))),
            "random",
            get_button_dict(ButtonStyles.SQUOVAL, (80, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )
        self.mediator_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((160, 95), (80, 30))),
            "choose",
            get_button_dict(ButtonStyles.SQUOVAL, (80, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )

        
        self.begin_anew_button.enable()
        self.mediator_button.enable()


    def process_event(self, event):
        super().process_event(event)
        if game.switches['window_open']:
            pass

        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            try:
                if event.ui_element == self.begin_anew_button:
                    game.last_screen_forupdate = None
                    game.switches['window_open'] = False
                    self.begin_anew_button.kill()
                    self.pick_path_message.kill()
                    self.mediator_button.kill()
                    self.kill()
                elif event.ui_element == self.mediator_button:
                    game.last_screen_forupdate = None
                    game.switches['window_open'] = False
                    game.switches['cur_screen'] = "name kits screen"
                    self.begin_anew_button.kill()
                    self.pick_path_message.kill()
                    self.mediator_button.kill()
                    self.kill()
                    game.all_screens['events screen'].exit_screen()
            except:
                print("failure with kits window")


class MateScreen(UIWindow):
    def __init__(self, last_screen):
        super().__init__(ui_scale(pygame.Rect((250, 200), (300, 150))),
                         window_display_title='Choose your mate',
                         object_id='#game_over_window',
                         resizable=False)
        self.set_blocking(True)
        game.switches['window_open'] = True
        self.clan_name = str(game.clan.name + 'Clan')
        self.last_screen = last_screen
        self.mates = game.switches['new_mate']
        self.pick_path_message = UITextBoxTweaked(
            f"{self.mates.name} confesses their feelings to you.",
            ui_scale(pygame.Rect((20, 20), (260, -1))),
            line_spacing=1,
            object_id="#text_box_30_horizcenter",
            container=self
        )
        self.begin_anew_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((55, 95), (80, 30))),
            "accept",
            get_button_dict(ButtonStyles.SQUOVAL, (80, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )
        self.mediator_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((160, 95), (80, 30))),
            "reject",
            get_button_dict(ButtonStyles.SQUOVAL, (80, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )

        self.begin_anew_button.enable()
        self.mediator_button.enable()



    def process_event(self, event):
        super().process_event(event)
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            try:
                if event.ui_element == self.begin_anew_button:
                    game.last_screen_forupdate = None
                    game.switches['window_open'] = False
                    # game.switch_screens = True                    
                    self.begin_anew_button.kill()
                    self.pick_path_message.kill()
                    self.mediator_button.kill()
                    self.kill()
                    game.clan.your_cat.set_mate(game.switches['new_mate'])
                    game.switches['accept'] = True

                elif event.ui_element == self.mediator_button:
                    game.last_screen_forupdate = None
                    game.switches['window_open'] = False
                    # game.switch_screens = True
                    self.begin_anew_button.kill()
                    self.pick_path_message.kill()
                    self.mediator_button.kill()
                    self.kill()
                    game.switches['new_mate'].relationships[game.clan.your_cat.ID].romantic_love = 0
                    game.clan.your_cat.relationships[game.switches['new_mate'].ID].comfortable -= 10
                    game.switches['reject'] = True
            except:
                print("error with mate screen")

class RetireScreen(UIWindow):
    def __init__(self, last_screen):
        super().__init__(ui_scale(pygame.Rect((250, 200), (300, 150))),
                         window_display_title='Choose to retire',
                         object_id='#game_over_window',
                         resizable=False)
        self.set_blocking(True)
        game.switches['window_open'] = True
        self.clan_name = str(game.clan.name + 'Clan')
        self.last_screen = last_screen
        game.switches['retire'] = False
        game.switches['retire_reject'] = False
        self.pick_path_message = UITextBoxTweaked(
            f"You're asked if you would like to retire.",
            ui_scale(pygame.Rect((20, 20), (260, -1))),
            line_spacing=1,
            object_id="#text_box_30_horizcenter",
            container=self
        )

        self.begin_anew_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((55, 95), (80, 30))),
            "accept",
            get_button_dict(ButtonStyles.SQUOVAL, (80, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )
        self.mediator_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((160, 95), (80, 30))),
            "reject",
            get_button_dict(ButtonStyles.SQUOVAL, (80, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )
        
        self.begin_anew_button.enable()
        self.mediator_button.enable()



    def process_event(self, event):
        super().process_event(event)

        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            try:
                if event.ui_element == self.begin_anew_button:
                    game.last_screen_forupdate = None
                    game.switches['window_open'] = False
                    # game.switch_screens = True                    
                    self.begin_anew_button.kill()
                    self.pick_path_message.kill()
                    self.mediator_button.kill()
                    self.kill()
                    game.switches['retire'] = True
                    game.clan.your_cat.status_change('elder')
                elif event.ui_element == self.mediator_button:
                    game.last_screen_forupdate = None
                    game.switches['window_open'] = False
                    # game.switch_screens = True
                    self.begin_anew_button.kill()
                    self.pick_path_message.kill()
                    self.mediator_button.kill()
                    self.kill()
                    game.switches['retire_reject'] = True
            except:
                print("error with retire screen")


class ChangeCatToggles(UIWindow):
    """This window allows the user to edit various cat behavior toggles"""

    def __init__(self, cat):
        super().__init__(
            ui_scale(pygame.Rect((300, 215), (400, 185))),
            window_display_title="Change Cat Name",
            object_id="#change_cat_name_window",
            resizable=False,
        )
        self.the_cat = cat
        self.set_blocking(True)
        self.back_button = UIImageButton(
            ui_scale(pygame.Rect((370, 5), (22, 22))),
            "",
            object_id="#exit_window_button",
            container=self,
        )

        self.checkboxes = {}
        self.refresh_checkboxes()

        # Text
        self.text_1 = pygame_gui.elements.UITextBox("Prevent fading", ui_scale(pygame.Rect(60, 25, -1, 50)), 
                                                    object_id="#text_box_30_horizleft_pad_0_8",
                                                    container=self)
        
        self.text_2 = pygame_gui.elements.UITextBox("Prevent kits", ui_scale(pygame.Rect(60, 50, -1, 50)), 
                                                    object_id="#text_box_30_horizleft_pad_0_8",
                                                    container=self)
        
        self.text_3 = pygame_gui.elements.UITextBox("Prevent retirement", ui_scale(pygame.Rect(60, 75, -1, 50)), 
                                                    object_id="#text_box_30_horizleft_pad_0_8",
                                                    container=self)
        
        self.text_4 = pygame_gui.elements.UITextBox("Limit romantic interactions and mate changes",
                                                    ui_scale(pygame.Rect(60, 100, -1, 50)), 
                                                    object_id="#text_box_30_horizleft_pad_0_8",
                                                    container=self)
        
        self.text_5 = pygame_gui.elements.UITextBox("Set neutral faith",
                                                    ui_scale(pygame.Rect(60, 125, -1, 50)), 
                                                    object_id="#text_box_30_horizleft_pad_0_8",
                                                    container=self)
        
        # Text

    def refresh_checkboxes(self):
        for x in self.checkboxes.values():
            x.kill()
        self.checkboxes = {}

        # Prevent Fading
        if self.the_cat == game.clan.instructor or self.the_cat == game.clan.demon:
            box_type = "@checked_checkbox"
            tool_tip = "The afterlife guide can never fade."
        elif self.the_cat.prevent_fading:
            box_type = "@checked_checkbox"
            tool_tip = "Prevents cat from fading away after being dead for 202 moons."
        else:
            box_type = "@unchecked_checkbox"
            tool_tip = "Prevents cat from fading away after being dead for 202 moons."

        # Fading
        self.checkboxes["prevent_fading"] = UIImageButton(
            ui_scale(pygame.Rect((22, 25), (34, 34))),
            "",
            container=self,
            object_id=box_type,
            tool_tip_text=tool_tip,
        )

        if self.the_cat == game.clan.instructor or self.the_cat == game.clan.demon:
            self.checkboxes["prevent_fading"].disable()

        # No Kits
        if self.the_cat.no_kits:
            box_type = "@checked_checkbox"
            tool_tip = "Prevent the cat from adopting or having kittens."
        else:
            box_type = "@unchecked_checkbox"
            tool_tip = "Prevent the cat from adopting or having kittens."

        self.checkboxes["prevent_kits"] = UIImageButton(
            ui_scale(pygame.Rect((22, 50), (34, 34))),
            "",
            container=self,
            object_id=box_type,
            tool_tip_text=tool_tip,
        )

        # No Retire
        if self.the_cat.no_retire:
            box_type = "@checked_checkbox"
            tool_tip = "Allow cat to retiring automatically."
        else:
            box_type = "@unchecked_checkbox"
            tool_tip = "Prevent cat from retiring automatically."

        self.checkboxes["prevent_retire"] = UIImageButton(
            ui_scale(pygame.Rect((22, 75), (34, 34))),
            "",
            container=self,
            object_id=box_type,
            tool_tip_text=tool_tip,
        )

        # No mates
        if self.the_cat.no_mates:
            box_type = "@checked_checkbox"
            tool_tip = "Prevent cat from automatically taking a mate, breaking up, or having romantic interactions with non-mates."
        else:
            box_type = "@unchecked_checkbox"
            tool_tip = "Prevent cat from automatically taking a mate, breaking up, or having romantic interactions with non-mates."
        
        self.checkboxes["prevent_mates"] = UIImageButton(ui_scale(pygame.Rect(22, 100, 34, 34)), "",
                                                         container=self,
                                                         object_id=box_type,
                                                         tool_tip_text=tool_tip)
        
        #No faith
        if self.the_cat.no_faith:
            box_type = "@checked_checkbox"
            tool_tip = "Lock this cat's faith to 0."
        else:
            box_type = "@unchecked_checkbox"
            tool_tip = "Lock this cat's faith to 0."
        
        self.checkboxes["no_faith"] = UIImageButton(ui_scale(pygame.Rect(22, 125, 34, 34)), "",
                                                         container=self,
                                                         object_id=box_type,
                                                         tool_tip_text=tool_tip)

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.back_button:
                game.all_screens["profile screen"].exit_screen()
                game.all_screens["profile screen"].screen_switches()
                self.kill()
            elif event.ui_element == self.checkboxes["prevent_fading"]:
                self.the_cat.prevent_fading = not self.the_cat.prevent_fading
                self.refresh_checkboxes()
            elif event.ui_element == self.checkboxes["prevent_kits"]:
                self.the_cat.no_kits = not self.the_cat.no_kits
                self.refresh_checkboxes()
            elif event.ui_element == self.checkboxes["prevent_retire"]:
                self.the_cat.no_retire = not self.the_cat.no_retire
                self.refresh_checkboxes()
            elif event.ui_element == self.checkboxes["prevent_mates"]:
                self.the_cat.no_mates = not self.the_cat.no_mates
                self.refresh_checkboxes()
            elif event.ui_element == self.checkboxes["no_faith"]:
                self.the_cat.no_faith = not self.the_cat.no_faith
                self.refresh_checkboxes()
        
        return super().process_event(event)


class SelectFocusClans(UIWindow):
    """This window allows the user to select the clans to be sabotaged, aided or raided in the focus setting."""

    def __init__(self):
        super().__init__(
            ui_scale(pygame.Rect((250, 120), (300, 225))),
            window_display_title="Change Cat Name",
            object_id="#change_cat_name_window",
            resizable=False,
        )
        self.set_blocking(True)
        self.back_button = UIImageButton(
            ui_scale(pygame.Rect((270, 5), (22, 22))),
            "",
            object_id="#exit_window_button",
            container=self,
        )
        self.save_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((80, 180), (139, 30))),
            "Change Focus",
            get_button_dict(ButtonStyles.SQUOVAL, (139, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )
        self.save_button.disable()

        self.checkboxes = {}
        self.refresh_checkboxes()

        # Text
        self.texts = {}
        self.texts["prompt"] = pygame_gui.elements.UITextBox(
            "<b>Which Clans will you target?</b>",
            ui_scale(pygame.Rect((0, 5), (300, 30))),
            object_id="#text_box_30_horizcenter",
            container=self,
        )
        n = 0
        for clan in game.clan.all_clans:
            self.texts[clan.name] = pygame_gui.elements.UITextBox(
                clan.name + "clan",
                ui_scale(pygame.Rect(107, n * 27 + 38, -1, 25)),
                object_id="#text_box_30_horizleft_pad_0_8",
                container=self,
            )
            n += 1

    def refresh_checkboxes(self):
        for x in self.checkboxes.values():
            x.kill()
        self.checkboxes = {}

        n = 0
        for clan in game.clan.all_clans:
            box_type = "@unchecked_checkbox"
            if clan.name in game.clan.clans_in_focus:
                box_type = "@checked_checkbox"

            self.checkboxes[clan.name] = UIImageButton(
                ui_scale(pygame.Rect((75, n * 27 + 35), (34, 34))),
                "",
                container=self,
                object_id=box_type,
            )
            n += 1

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.back_button:
                game.clan.clans_in_focus = []
                game.all_screens["warrior den screen"].exit_screen()
                game.all_screens["warrior den screen"].screen_switches()
                self.kill()
            if event.ui_element == self.save_button:
                game.all_screens["warrior den screen"].save_focus()
                game.all_screens["warrior den screen"].exit_screen()
                game.all_screens["warrior den screen"].screen_switches()
                self.kill()
            if event.ui_element in self.checkboxes.values():
                for clan_name, value in self.checkboxes.items():
                    if value == event.ui_element:
                        if value.object_ids[1] == "@unchecked_checkbox":
                            game.clan.clans_in_focus.append(clan_name)
                        if value.object_ids[1] == "@checked_checkbox":
                            game.clan.clans_in_focus.remove(clan_name)
                        self.refresh_checkboxes()
                if len(game.clan.clans_in_focus) < 1 and self.save_button.is_enabled:
                    self.save_button.disable()
                if (
                    len(game.clan.clans_in_focus) >= 1
                    and not self.save_button.is_enabled
                ):
                    self.save_button.enable()

        return super().process_event(event)


class ConfirmDisplayChanges(UIMessageWindow):
    def __init__(self, source_screen: "Screens"):
        super().__init__(
            ui_scale(pygame.Rect((275, 270), (250, 160))),
            "This is a test!",
            MANAGER,
            object_id="#confirm_display_changes_window",
            always_on_top=True,
        )
        self.set_blocking(True)

        self.dismiss_button.kill()
        self.text_block.kill()

        button_size = (-1, 30)
        button_spacing = 10
        button_vertical_space = (button_spacing * 2) + button_size[1]

        dismiss_button_rect = ui_scale(pygame.Rect((0, 0), (140, 30)))
        dismiss_button_rect.bottomright = ui_scale_offset(
            (-button_spacing, -button_spacing)
        )

        self.dismiss_button = UISurfaceImageButton(
            dismiss_button_rect,
            "Confirm changes",
            get_button_dict(ButtonStyles.SQUOVAL, (140, 30)),
            MANAGER,
            container=self,
            object_id="@buttonstyles_squoval",
            anchors={
                "left": "right",
                "top": "bottom",
                "right": "right",
                "bottom": "bottom",
            },
        )

        revert_rect = ui_scale(pygame.Rect((0, 0), (75, 30)))
        revert_rect.bottomleft = ui_scale_offset((button_spacing, -button_spacing))

        self.revert_button = UISurfaceImageButton(
            revert_rect,
            "Revert",
            get_button_dict(ButtonStyles.SQUOVAL, (75, 30)),
            MANAGER,
            container=self,
            object_id="@buttonstyles_squoval",
            anchors={
                "left": "left",
                "bottom": "bottom",
            },
        )

        rect = ui_scale(pygame.Rect((0, 0), (22, 22)))
        rect.topright = ui_scale_offset((-5, 7))
        self.back_button = UIImageButton(
            rect,
            "",
            object_id="#exit_window_button",
            container=self,
            visible=True,
            anchors={"top": "top", "right": "right"},
        )

        text_block_rect = pygame.Rect(
            ui_scale_offset((0, 22)),
            (
                self.get_container().get_size()[0],
                self.get_container().get_size()[1] - button_vertical_space,
            ),
        )
        self.text_block = pygame_gui.elements.UITextBox(
            "Do you want to keep these changes? Display changes will be reverted in 10 seconds.",
            text_block_rect,
            manager=MANAGER,
            object_id="#text_box_30_horizcenter",
            container=self,
            anchors={
                "left": "left",
                "top": "top",
                "right": "right",
                "bottom": "bottom",
            },
        )
        self.text_block.rebuild_from_changed_theme_data()

        # make a timeout that will call in 10 seconds - if this window isn't closed,
        # it'll be used to revert the change
        pygame.time.set_timer(pygame.USEREVENT + 10, 10000, loops=1)

        self.source_screen_name = source_screen.name.replace(" ", "_")

    def revert_changes(self):
        """Revert the changes made to screen scaling"""
        from scripts.game_structure.screen_settings import toggle_fullscreen
        from scripts.screens.all_screens import AllScreens

        toggle_fullscreen(
            None,
            source_screen=getattr(AllScreens, self.source_screen_name),
            show_confirm_dialog=False,
        )

    def process_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if (
                event.ui_element == self.back_button
                or event.ui_element == self.dismiss_button
            ):
                self.kill()
            elif event.ui_element == self.revert_button:
                self.revert_changes()
        elif event.type == pygame.USEREVENT + 10:
            self.revert_changes()
            self.kill()
        return super().process_event(event)
