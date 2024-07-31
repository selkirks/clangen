# pylint: disable=line-too-long
import logging
import os
import platform
import subprocess

import pygame
import pygame_gui
import ujson

import scripts.screens.screens_core
from scripts.game_structure.discord_rpc import _DiscordRPC
from scripts.game_structure.game_essentials import game
from scripts.game_structure.ui_elements import UIImageButton, UISurfaceImageButton
from scripts.utility import (
    get_text_box_theme,
    ui_scale,
    ui_scale_dimensions,
)
from .Screens import Screens
from ..game_structure.screen_settings import MANAGER, toggle_fullscreen
from ..game_structure.windows import ConfirmDisplayChanges
from ..housekeeping.datadir import get_data_dir
from ..housekeeping.version import get_version_info
from ..ui.generate_button import get_button_dict, ButtonStyles
from ..ui.get_arrow import get_arrow

logger = logging.getLogger(__name__)

with open("resources/gamesettings.json", "r", encoding="utf-8") as f:
    settings_dict = ujson.load(f)


class SettingsScreen(Screens):
    """
    TODO: DOCS
    """

    sub_menu = "general"

    # This is set to the current settings when the screen is opened.
    # All edits are made directly to game.settings, however, when you
    #  leave the screen,game.settings will be reverted based on this variable
    #   However, if settings are saved, edits will also be made to this variable.
    settings_at_open = {}

    # Have the settings been changed since the page was open or since settings were saved?
    settings_changed = False

    # Contains the checkboxes
    checkboxes = {}
    # Contains the text for the checkboxes.
    checkboxes_text = {}

    # contains the tooltips for contributors
    tooltip = {}

    info_text = ""
    tooltip_text = []
    with open("resources/credits_text.json", "r", encoding="utf-8") as f:
        credits_text = ujson.load(f)
    for string in credits_text["text"]:
        if string == "{contrib}":
            for contributor in credits_text["contrib"]:
                info_text += contributor + "<br>"
                tooltip_text.append(credits_text["contrib"][contributor])
        else:
            info_text += string
            info_text += "<br>"

    def __init__(self, name="settings_screen"):
        super().__init__(name)
        self.prev_setting = None

    def handle_event(self, event):
        """
        TODO: DOCS
        """
        if event.type == pygame.USEREVENT + 11:
            self.toggle_fullscreen(self.prev_setting)
            return
        if event.type == pygame_gui.UI_TEXT_BOX_LINK_CLICKED:
            if platform.system() == "Darwin":
                subprocess.Popen(["open", "-u", event.link_target])
            elif platform.system() == "Windows":
                os.system(f'start "" {event.link_target}')
            elif platform.system() == "Linux":
                subprocess.Popen(["xdg-open", event.link_target])
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.main_menu_button:
                self.change_screen("start screen")
                return
            if event.ui_element == self.fullscreen_toggle:
                self.prev_setting = game.settings["fullscreen"]
                self.toggle_fullscreen()
                ConfirmDisplayChanges()
            elif event.ui_element == self.open_data_directory_button:
                if platform.system() == "Darwin":
                    subprocess.Popen(["open", "-R", get_data_dir()])
                elif platform.system() == "Windows":
                    os.startfile(get_data_dir())  # pylint: disable=no-member
                elif platform.system() == "Linux":
                    try:
                        subprocess.Popen(["xdg-open", get_data_dir()])
                    except OSError:
                        logger.exception("Failed to call to xdg-open.")
                return
            elif event.ui_element == self.save_settings_button:
                self.save_settings()
                game.save_settings(self)
                self.settings_changed = False
                self.update_save_button()
                return
            elif event.ui_element == self.general_settings_button:
                self.open_general_settings()
                return
            elif event.ui_element == self.info_button:
                self.open_info_screen()
                return
            elif event.ui_element == self.language_button:
                self.open_lang_settings()
            if self.sub_menu in ["general", "relation", "language"]:
                self.handle_checkbox_events(event)

        elif event.type == pygame.KEYDOWN and game.settings["keybinds"]:
            if event.key == pygame.K_ESCAPE:
                self.change_screen("start screen")
            elif event.key == pygame.K_RIGHT:
                if self.sub_menu == "general":
                    self.open_info_screen()
                elif self.sub_menu == "info":
                    self.open_lang_settings()
            elif event.key == pygame.K_LEFT:
                if self.sub_menu == "info":
                    self.open_general_settings()
                elif self.sub_menu == "language":
                    self.open_info_screen()

    def handle_checkbox_events(self, event):
        """
        TODO: DOCS
        """
        if event.ui_element in self.checkboxes.values():
            for key, value in self.checkboxes.items():
                if value == event.ui_element:
                    if self.sub_menu == "language":
                        game.settings["language"] = key
                    else:
                        game.switch_setting(key)
                    self.settings_changed = True
                    self.update_save_button()

                    if (
                        self.sub_menu == "general"
                        and event.ui_element is self.checkboxes["dark mode"]
                    ):
                        if (
                            "@unchecked_checkbox"
                            in self.checkboxes["dark mode"].get_object_ids()
                        ):
                            self.set_bg("default_dark")
                        else:
                            self.set_bg("default")

                    if (
                        self.sub_menu == "general"
                        and event.ui_element is self.checkboxes["discord"]
                    ):
                        if game.settings["discord"]:
                            print("Starting Discord RPC")
                            game.rpc = _DiscordRPC("1076277970060185701", daemon=True)
                            game.rpc.start()
                            game.rpc.start_rpc.set()
                        else:
                            print("Stopping Discord RPC")
                            game.rpc.close()

                    opens = {
                        "general": self.open_general_settings,
                        "language": self.open_lang_settings,
                    }

                    scroll_pos = None
                    if (
                        "container_general" in self.checkboxes_text
                        and self.checkboxes_text["container_general"].vert_scroll_bar
                    ):
                        scroll_pos = self.checkboxes_text[
                            "container_general"
                        ].vert_scroll_bar.start_percentage

                    if self.sub_menu in opens:
                        opens[self.sub_menu]()

                    if scroll_pos is not None:
                        self.checkboxes_text[
                            "container_general"
                        ].vert_scroll_bar.set_scroll_from_start_percentage(scroll_pos)

                    break

    def screen_switches(self):
        """
        TODO: DOCS
        """
        super().screen_switches()
        self.settings_changed = False

        self.general_settings_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((175, 100), (150, 30))),
            "general settings",
            get_button_dict(ButtonStyles.MENU_LEFT, (150, 30)),
            object_id="@buttonstyles_menu_left",
            manager=MANAGER,
        )
        self.info_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((0, 100), (150, 30))),
            "info",
            get_button_dict(ButtonStyles.MENU_MIDDLE, (150, 30)),
            object_id="@buttonstyles_menu_middle",
            manager=MANAGER,
            anchors={"left_target": self.general_settings_button},
        )
        self.language_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((0, 100), (150, 30))),
            "language",
            get_button_dict(ButtonStyles.MENU_RIGHT, (150, 30)),
            object_id="@buttonstyles_menu_right",
            manager=MANAGER,
            anchors={"left_target": self.info_button},
        )
        self.save_settings_button = UIImageButton(
            ui_scale(pygame.Rect((0, 550), (150, 30))),
            "",
            object_id="#save_settings_button",
            manager=MANAGER,
            anchors={"centerx": "centerx"},
        )

        screentext = "windowed" if game.settings["fullscreen"] else "fullscreen"
        self.fullscreen_toggle = UIImageButton(
            ui_scale(pygame.Rect((617, 25), (158, 36))),
            "",
            object_id="#toggle_fullscreen_button",
            manager=MANAGER,
            tool_tip_text=(
                f"This will put the game into {screentext} mode."
                "<br><br>"
                "<b>Important:</b> This also saves all changed settings!"
            ),
        )
        del screentext

        self.open_data_directory_button = UIImageButton(
            ui_scale(pygame.Rect((25, 645), (178, 30))),
            "",
            object_id="#open_data_directory_button",
            manager=MANAGER,
            tool_tip_text="Opens the data directory. "
            "This is where save files "
            "and logs are stored.",
        )

        if get_version_info().is_sandboxed:
            self.open_data_directory_button.hide()

        self.update_save_button()
        self.main_menu_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((25, 25), (152, 30))),
            get_arrow(3) + " Main Menu",
            get_button_dict(ButtonStyles.SQUOVAL, (152, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_squoval",
            starting_height=1,
        )
        self.sub_menu = "general"
        self.open_general_settings()

        self.set_bg("default")

        self.settings_at_open = game.settings.copy()

        self.refresh_checkboxes()

    def update_save_button(self):
        """
        Updates the disabled state the save button
        """
        if not self.settings_changed:
            self.save_settings_button.disable()
        else:
            self.save_settings_button.enable()

    def exit_screen(self):
        """
        TODO: DOCS
        """
        self.clear_sub_settings_buttons_and_text()
        self.general_settings_button.kill()
        del self.general_settings_button
        self.info_button.kill()
        del self.info_button
        self.language_button.kill()
        del self.language_button
        self.save_settings_button.kill()
        del self.save_settings_button
        self.main_menu_button.kill()
        del self.main_menu_button
        self.fullscreen_toggle.kill()
        del self.fullscreen_toggle
        self.open_data_directory_button.kill()
        del self.open_data_directory_button

        game.settings = self.settings_at_open

    def save_settings(self):
        """Saves the settings, ensuring that they will be retained when the screen changes."""
        self.settings_at_open = game.settings.copy()

    def open_general_settings(self):
        """Opens and draws general_settings"""
        self.enable_all_menu_buttons()
        self.general_settings_button.disable()
        self.clear_sub_settings_buttons_and_text()
        self.sub_menu = "general"
        self.save_settings_button.show()

        self.checkboxes_text[
            "container_general"
        ] = pygame_gui.elements.UIScrollingContainer(
            ui_scale(pygame.Rect((0, 220), (700, 300))),
            allow_scroll_x=False,
            manager=MANAGER,
        )

        n = 0
        for code, desc in settings_dict["general"].items():
            self.checkboxes_text[code] = pygame_gui.elements.UITextBox(
                desc[0],
                ui_scale(pygame.Rect((225, n * 39), (500, 39))),
                container=self.checkboxes_text["container_general"],
                object_id=get_text_box_theme("#text_box_30_horizleft_pad_0_8"),
                manager=MANAGER,
            )
            self.checkboxes_text[code].disable()
            n += 1

        self.checkboxes_text["container_general"].set_scrollable_area_dimensions(
            ui_scale_dimensions((680, (n * 39 + 40)))
        )

        self.checkboxes_text["instr"] = pygame_gui.elements.UITextBox(
            """Change the general settings of your game here.\n"""
            """More settings are available in the settings page of your Clan.""",
            ui_scale(pygame.Rect((100, 160), (600, 100))),
            object_id=get_text_box_theme("#text_box_30_horizcenter"),
            manager=MANAGER,
        )

        # This is where the actual checkboxes are created. I don't like
        #   how this is separated from the text boxes, but I've spent too much time to rewrite it.
        #   It has to separated because the checkboxes must be updated when settings are changed.
        #   Fix if you want. - keyraven
        self.refresh_checkboxes()

    def open_info_screen(self):
        """Open's info screen"""
        self.enable_all_menu_buttons()
        self.info_button.disable()
        self.clear_sub_settings_buttons_and_text()
        self.sub_menu = "info"
        self.save_settings_button.hide()

        self.checkboxes_text[
            "info_container"
        ] = pygame_gui.elements.UIScrollingContainer(
            ui_scale(pygame.Rect((0, 150), (600, 500))),
            allow_scroll_x=False,
            manager=MANAGER,
            anchors={"centerx": "centerx"},
        )

        self.checkboxes_text["info_text_box"] = pygame_gui.elements.UITextBox(
            self.info_text,
            ui_scale(pygame.Rect((0, 0), (575, -1))),
            object_id=get_text_box_theme("#text_box_30_horizcenter"),
            container=self.checkboxes_text["info_container"],
            manager=MANAGER,
            anchors={"centerx": "centerx"},
        )

        self.checkboxes_text["info_text_box"].disable()

        i = 0
        y_pos = 343
        for i, tooltip in enumerate(self.tooltip_text):
            self.tooltip[f"tip{i}"] = (
                UIImageButton(
                    ui_scale(pygame.Rect((0, i * 26 + y_pos), (200, 26))),
                    "",
                    object_id="#blank_button",
                    container=self.checkboxes_text["info_container"],
                    manager=MANAGER,
                    tool_tip_text=tooltip if tooltip else None,
                    starting_height=2,
                    anchors={"centerx": "centerx"},
                ),
            )
        self.checkboxes_text["info_container"].set_scrollable_area_dimensions(
            ui_scale_dimensions((785, i * 28 + y_pos + 275))
        )

    def open_lang_settings(self):
        """Open Language Settings"""
        self.enable_all_menu_buttons()
        self.language_button.disable()
        self.clear_sub_settings_buttons_and_text()
        self.sub_menu = "language"
        self.save_settings_button.show()

        self.checkboxes_text["instr"] = pygame_gui.elements.UITextBox(
            "Change the language of the game here. This has not been implemented yet.",
            ui_scale(pygame.Rect((100, 160), (600, 50))),
            object_id=get_text_box_theme("#text_box_30_horizcenter"),
            manager=MANAGER,
        )

        self.refresh_checkboxes()

    def refresh_checkboxes(self):
        """
        TODO: DOCS
        """
        # Kill the checkboxes. No mercy here.
        for checkbox in self.checkboxes.values():
            checkbox.kill()
        self.checkboxes = {}

        # CHECKBOXES (ehhh) FOR LANGUAGES
        if self.sub_menu == "language":
            self.checkboxes["english"] = UIImageButton(
                ui_scale(pygame.Rect((310, 200), (180, 51))),
                "",
                object_id="#english_lang_button",
                manager=MANAGER,
            )
            self.checkboxes["spanish"] = UIImageButton(
                ui_scale(pygame.Rect((310, 0), (180, 37))),
                "",
                object_id="#spanish_lang_button",
                manager=MANAGER,
                anchors={"top_target": self.checkboxes["english"]},
            )
            self.checkboxes["german"] = UIImageButton(
                ui_scale(pygame.Rect((310, 0), (180, 37))),
                "",
                object_id="#german_lang_button",
                manager=MANAGER,
                anchors={"top_target": self.checkboxes["spanish"]},
            )

            if game.settings["language"] == "english":
                self.checkboxes["english"].disable()
            elif game.settings["language"] == "spanish":
                self.checkboxes["spanish"].disable()
            elif game.settings["language"] == "german":
                self.checkboxes["german"].disable()

        else:
            n = 0
            for code, desc in settings_dict[self.sub_menu].items():
                if game.settings[code]:
                    box_type = "@checked_checkbox"
                else:
                    box_type = "@unchecked_checkbox"
                self.checkboxes[code] = UIImageButton(
                    ui_scale(pygame.Rect((170, n * 40), (34, 34))),
                    "",
                    object_id=box_type,
                    container=self.checkboxes_text["container_" + self.sub_menu],
                    tool_tip_text=desc[1],
                )
                n += 1

    def clear_sub_settings_buttons_and_text(self):
        """
        TODO: DOCS
        """
        if "info_container" in self.checkboxes_text:
            self.checkboxes_text["info_container"].kill()

        if "container_general" in self.checkboxes_text:
            self.checkboxes_text["container_general"].kill()

        for checkbox in self.checkboxes.values():
            checkbox.kill()
        self.checkboxes = {}
        for text in self.checkboxes_text.values():
            text.kill()
        self.checkboxes_text = {}

    def enable_all_menu_buttons(self):
        """
        TODO: DOCS
        """
        self.general_settings_button.enable()
        self.info_button.enable()
        self.language_button.enable()

    def on_use(self):
        """
        TODO: DOCS
        """
        super().on_use()

    def toggle_fullscreen(self, screen_mode=None):
        game.switch_setting("fullscreen")
        self.save_settings()
        game.save_settings(self)
        self.exit_screen()

        if screen_mode is None:
            screen_mode = game.settings["fullscreen"]
        toggle_fullscreen(screen_mode)
        scripts.screens.screens_core.screens_core.rebuild_core()
        game.all_screens["settings screen"].screen_switches()
