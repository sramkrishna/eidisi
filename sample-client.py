#!/usr/bin/env python3
# sample-client.py
#
# Copyright (C) 2017 Sri Ramkrishna <sri@ramkrishna.me>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import (
    GLib,
    GObject,
)

import sys
import time
from eidisi.EidisiMatrixOps import GnomeMatrixClientApi
from getpass import getpass


def main():
    """ test client """


#    client.login(user=myuser,password=mypass)
    client.login()
#    client.join_room("#matrix:matrix.org")
#    client.send_message("test hello")


def _on_authenticated(*args):
    """ We have authenticated to matrix server """

    print("I have come here")
    client.join_room("#matrix:matrix.org")
    print("sleeping for 10 seconds")
    print("status for waiting for response is", client.wait_for_response)
#    time.sleep(20)
    client.send_message("test hello")

if __name__ == '__main__':


    myuser = input("Matrix Username: ")
    mypass = getpass(prompt='Matrix Password: ', stream=None)

    client = GnomeMatrixClientApi(hostname='matrix.org', username=myuser,
                                  port=8448, password=mypass)
    client.connect('notify::authenticated',_on_authenticated)
    main()
    mainloop = GLib.MainLoop()
    mainloop.run()

