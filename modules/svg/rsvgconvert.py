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
from modules.utils import execute
from modules.svg.svg import SVG


class RSVGConvert(SVG):
    """Inkscape implemntation of SVG Interface."""

    def __init__(self, colors):
        """Init function."""
        super(RSVGConvert, self).__init__(colors)
        self.cmd = "rsvg-convert"
        if not self.is_installed():
            raise RSVGConvertNotInstalled

    def convert_to_png(self, input_file, output_file, width=None, height=None):
        """Convert svg to png."""
        cmd = [self.cmd, "-f", "png", "-o", output_file]
        if width and height:
            cmd.extend(["-w", str(width), "-h", str(height)])
        cmd.append(input_file)
        execute(cmd)


class RSVGConvertNotInstalled(Exception):
    """Exception raised when Inkscape is not installed."""

    def __init__(self):
        """Init Exception."""
        super(RSVGConvertNotInstalled, self).__init__()
