#!/usr/bin/env python3
# join_room.py
#
# Copyright (C) 2017 Sriram Ramkrishna <sri@ramkrishna.me>
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

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

from gi.repository import (
    GLib,
    GObject,
    Gio,
    Gdk,
    Gtk,
)

from .gi_composites import GtkTemplate
from .EidisiMatrixOps import GnomeMatrixClientApi

@GtkTemplate(ui='/me/ramkrishna/Eidisi/ui/login_details.ui')
class LoginDetails(Gtk.Dialog):
    __gtype_name__ = 'login_details'

    homeserver = GtkTemplate.Child()
    portnum = GtkTemplate.Child()
    username = GtkTemplate.Child()
    password= GtkTemplate.Child()


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.init_template()

        self.set_response_sensitive(Gtk.ResponseType.OK, True)
        self.settings = Gio.Settings.new('me.ramkrishna.Eidisi')

        self.password.set_visibility(False)

        self.cancellable = Gio.Cancellable.new()

#        self.connect('response', lambda dialog, response: dialog.destroy())
        self.connect('response', self.handle_pref_response)

    def do_resonse(self, response_id):
        print("I got called")
        if response_id == Gtk.ResponseType.OK:
            print("response is OK")

    @GtkTemplate.Callback
    def handle_pref_response(self, dialog, responseid):

        if responseid == Gtk.ResponseType.OK:
            print("we clicked OK")
            self.hostname = self.homeserver.get_text()
            self.port = int(self.portnum.get_text())
            self.userid = self.username.get_text()
            self.passwd = self.password.get_text()

#            self.settings.set_string('username', username)
#            self.settings.set_string('password', password)
#            self.settings.set_uint16('port', port)
#            self.settings.set_string('hostname', hostname)

            print ("the value for homeserver is: ** %s **"%(self.hostname))
            print ("the value for username is: ** %s **"%(self.userid))

        elif responseid == Gtk.ResponseType.CANCEL:
            print("we clicked cancel")

        dialog.destroy()

    @GtkTemplate.Callback
    def handle_pref_cancel(self, button):
        self.response(Gtk.ResponseType.CANCEL)
        print("we are doing nothing")
