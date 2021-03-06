#!/usr/bin/python3
"""
Fixes Hardcoded tray icons in Linux.

Author : Bilal Elmoussaoui (bil.elmoussaoui@gmail.com)
Contributors : Andreas Angerer, Joshua Fogg
Version : 3.6.5
Website : https://github.com/bil-elmoussaoui/Hardcode-Tray
Licence : The script is released under GPL, uses a modified script
     form Chromium project released under BSD license
This file is part of Hardcode-Tray.
Hardcode-Tray is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
Hardcode-Tray is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with Hardcode-Tray. If not, see <http://www.gnu.org/licenses/>.
"""
from os import path, environ, geteuid, listdir
from argparse import ArgumentParser
from modules.data import DataManager
from modules.utils import (execute, change_colors_list, log,
                           get_list_of_themes, create_icon_theme)
from modules.const import (DB_FOLDER,
                           REVERTED_APPS, FIXED_APPS, CONVERSION_TOOLS)
from modules.applications.application import Application
from modules.applications.electron import ElectronApplication
from modules.applications.qt import QtApplication
from modules.applications.pak import PakApplication
from modules.applications.zip import ZipApplication
from modules.applications.nwjs import NWJSApplication
from modules.svg.inkscape import Inkscape, InkscapeNotInstalled
from modules.svg.cairosvg import CairoSVG, CairoSVGNotInstalled
from modules.svg.rsvgconvert import RSVGConvert, RSVGConvertNotInstalled
from modules.svg.imagemagick import ImageMagick, ImageMagickNotInstalled
from modules.svg.svgexport import SVGExport, SVGExportNotInstalled
from modules.svg.svg import SVG
import logging


from sys import stdout
from gi import require_version
require_version("Gtk", "3.0")
from gi.repository import Gio, Gtk
colours = []
gsettings = None
parser = ArgumentParser(prog="Hardcode-Tray")
absolute_path = path.split(path.abspath(__file__))[0] + "/"
THEMES_LIST = get_list_of_themes()
theme = Gtk.IconTheme.get_default()
supported_icons_cnt = 0

parser.add_argument("--debug", "-d", action='store_true',
                    help="Run the script with debug mode.")
parser.add_argument("--size", "-s", help="use a different icon size instead "
                    "of the default one.",
                    type=int, choices=[16, 22, 24])
parser.add_argument("--theme",
                    help="use a different icon theme instead "
                    "of the default one.",
                    type=str, choices=THEMES_LIST)
parser.add_argument("--light-theme", "-lt",
                    help="use a specified theme for the light icons."
                    " Can't be used with --theme."
                    "Works only with --dark-theme.",
                    type=str)
parser.add_argument("--dark-theme", "-dt",
                    help="use a specified theme for the dark icons."
                    "Can't be used with --theme"
                    "Works only with --light-theme.",
                    type=str)
parser.add_argument("--only", "-o",
                    help="fix only one application or more, linked by a ','.\n"
                    "example : --only dropbox,telegram",
                    type=str)
parser.add_argument("--path", "-p",
                    help="use a different icon path for a single icon.",
                    type=str)
parser.add_argument("--update", "-u", action='store_true',
                    help="update Hardcode-Tray to the latest stable version.")
parser.add_argument("--update-git", "-ug", action='store_true',
                    help="update Hardcode-Tray to the latest git commit.")
parser.add_argument("--version", "-v", action='store_true',
                    help="print the version number of Hardcode-Tray.")
parser.add_argument("--apply", "-a", action='store_true',
                    help="fix hardcoded tray icons")
parser.add_argument("--revert", "-r", action='store_true',
                    help="revert fixed hardcoded tray icons")
parser.add_argument("--conversion-tool", "-ct",
                    help="Which of conversion tool to use",
                    type=str, choices=CONVERSION_TOOLS)
parser.add_argument('--change-color', "-cc", type=str, nargs='+',
                    help="Replace a color with an other one, "
                    "works only with SVG.")
args = parser.parse_args()


def detect_de():
    """Detect the desktop environment, used to choose the proper icons size."""
    try:
        desktop_env = [environ.get("DESKTOP_SESSION").lower(
        ), environ.get("XDG_CURRENT_DESKTOP").lower()]
    except AttributeError:
        desktop_env = []
    if "pantheon" in desktop_env:
        log("Desktop environment detected : Panatheon")
        return "pantheon"
    else:
        try:
            out = execute(["ls", "-la", "xprop -root _DT_SAVE_MODE"],
                          verbose=False)
            if " = \"xfce4\"" in out.decode("utf-8"):
                log("Desktop environment detected: XFCE")
                return "xfce"
            else:
                return "other"
        except (OSError, RuntimeError):
            return "other"
    log("Desktop environment not detected")


def get_supported_apps(fix_only, custom_path=""):
    """Get a list of dict, a dict for each supported application."""
    database_files = listdir(absolute_path + DB_FOLDER)
    if len(fix_only) != 0:
        database_files = []
        for _file in fix_only:
            if path.exists("%s%s.json" % (DB_FOLDER, _file)):
                database_files.append("%s.json" % _file)
    database_files.sort()
    supported_apps = []
    is_only = len(database_files) == 1
    for _file in database_files:
        _file = "./%s%s" % (DB_FOLDER, _file)
        application_data = DataManager(_file, theme, default_icon_size,
                                       custom_path, is_only)
        if application_data.is_installed():
            application_type = application_data.get_type()
            if application_type == "electron":
                application = ElectronApplication(application_data, svgtopng)
            elif application_type == "pak":
                application = PakApplication(application_data, svgtopng)
            elif application_type == "qt":
                application = QtApplication(application_data, svgtopng)
            elif application_type == "nwjs":
                application = NWJSApplication(application_data, svgtopng)
            elif application_type == "zip":
                application = ZipApplication(application_data, svgtopng)
            else:
                application = Application(application_data, svgtopng)
            supported_apps.append(application)
    return supported_apps


def progress(count, count_max, app_name=""):
    """Used to draw a progress bar."""
    bar_len = 40
    space = 20
    filled_len = int(round(bar_len * count / float(count_max)))

    percents = round(100.0 * count / float(count_max), 1)
    progress_bar = '#' * filled_len + '.' * (bar_len - filled_len)

    stdout.write("\r%s%s" % (app_name, " " * (abs(len(app_name) - space))))
    stdout.write('[%s] %i/%i %s%s\r' %
                 (progress_bar, count, count_max, percents, '%'))
    print("")
    stdout.flush()


def reinstall(fix_only, custom_path):
    """Revert to the original icons."""
    apps = get_supported_apps(fix_only, custom_path)
    if len(apps) != 0:
        cnt = 0
        reverted_cnt = sum(app.data.supported_icons_cnt for app in apps)
        for i, app in enumerate(apps):
            app_name = app.get_name()
            app.reinstall()
            if app.is_done:
                cnt += app.data.supported_icons_cnt
                if app_name not in REVERTED_APPS:
                    progress(cnt, reverted_cnt, app_name)
                    REVERTED_APPS.append(app_name)
            else:
                reverted_cnt -= app.data.supported_icons_cnt
                if i == len(apps) - 1:
                    progress(cnt, reverted_cnt)
    else:
        exit("No apps to revert!")


def install(fix_only, custom_path):
    """Install the new supported icons."""
    apps = get_supported_apps(fix_only, custom_path)
    if len(apps) != 0:
        cnt = 0
        installed_cnt = sum(app.data.supported_icons_cnt for app in apps)
        for i, app in enumerate(apps):
            app_name = app.get_name()
            app.install()
            if app.is_done:
                cnt += app.data.supported_icons_cnt
                if app_name not in FIXED_APPS:
                    progress(cnt, installed_cnt, app_name)
                    FIXED_APPS.append(app_name)
            else:
                installed_cnt -= app.data.supported_icons_cnt
                if i == len(apps) - 1:
                    progress(cnt, installed_cnt)
    else:
        exit("No apps to fix! Please report on GitHub if this is not the case")


if geteuid() != 0:
    exit("You need to have root privileges to run the script.\
        \nPlease try again, this time using 'sudo'. Exiting.")

if not (environ.get("DESKTOP_SESSION") or
        environ.get("XDG_CURRENT_DESKTOP")) and not args.size:
    exit("You need to run the script using 'sudo -E'.\nPlease try again")

if args.theme:
    theme_name = args.theme
    theme = create_icon_theme(theme_name, THEMES_LIST)
elif args.light_theme and args.dark_theme:
    light_theme_name = args.light_theme
    dark_theme_name = args.dark_theme
    dark_theme = create_icon_theme(dark_theme_name, THEMES_LIST)
    light_theme = create_icon_theme(light_theme_name, THEMES_LIST)
    theme = {
        "dark": dark_theme,
        "light": light_theme
    }
else:
    source = Gio.SettingsSchemaSource.get_default()
    if source.lookup("org.gnome.desktop.interface", True):
        gsettings = Gio.Settings.new("org.gnome.desktop.interface")
        theme_name = str(gsettings.get_value("icon-theme")).strip("'")

if args.change_color:
    colours = change_colors_list(args.change_color)

level = logging.ERROR
if args.debug:
    level = logging.DEBUG
logging.basicConfig(level=level,
                    format='[%(levelname)s] - %(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

conversion_tool = args.conversion_tool if args.conversion_tool else None
svgtool_found = False
i = 0
while i < len(CONVERSION_TOOLS) and not svgtool_found:
    tool = CONVERSION_TOOLS[i]
    try:
        if ((conversion_tool and conversion_tool == tool)
                or not conversion_tool):
            svgtool_found = True
        if svgtool_found:
            svgtopng = eval(tool)(colours)
            conversion_tool = tool
    except eval("%sNotInstalled" % tool):
        svgtool_found = False
    i += 1
if not svgtool_found:
    conversion_tool = "Not Found!"
    svgtopng = SVG(colours)
    svgtopng.is_svg_enabled = False

if args.size:
    default_icon_size = args.size
else:
    if detect_de() in ("pantheon", "xfce"):
        default_icon_size = 24
    else:
        default_icon_size = 22
choice = None
fix_only = args.only.lower().strip().split(",") if args.only else []

if args.path and fix_only and len(fix_only) == 1:
    icon_path = args.path
else:
    icon_path = None
if args.apply:
    choice = 1
if args.revert:
    choice = 2
print("Welcome to the tray icons hardcoder fixer!")
print("Your indicator icon size is : %s" % default_icon_size)
if args.theme or gsettings:
    print("Your current icon theme is : %s" % theme_name)
elif args.dark_theme and args.light_theme:
    print("Your current dark icon theme is : %s" % dark_theme_name)
    print("Your current light icon theme is : %s" % light_theme_name)
print("Svg to png functions are : ", end="")
print("Enabled" if svgtopng.is_svg_enabled else "Disabled")
print("Conversion tool : " + conversion_tool)
print("Applications will be fixed : ", end="")
print(",".join(fix_only) if fix_only else "All")

if not choice:
    print("1 - Apply")
    print("2 - Revert")
    try:
        choice = int(input("Please choose: "))
        if choice not in [1, 2]:
            exit("Please try again")
    except ValueError:
        exit("Please choose a valid value!")
    except KeyboardInterrupt:
        exit("")

if choice == 1:
    print("Applying now..\n")
    install(fix_only, icon_path)
elif choice == 2:
    print("Reverting now..\n")
    reinstall(fix_only, icon_path)

print("\nDone, Thank you for using the Hardcode-Tray fixer!")
