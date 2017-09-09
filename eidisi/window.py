#!/usr/bin/env python3
#
# window.py
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
from .settings import Settings


@GtkTemplate(ui='/me/ramkrishna/Eidisi/ui/main.ui')
class ApplicationWindow(Gtk.ApplicationWindow):

    __gtype_name__ = 'ApplicationWindow'

    client = GObject.Property(type=GnomeMatrixClientApi)
    header = GtkTemplate.Child()
    contentbox = GtkTemplate.Child()
    chatbox = GtkTemplate.Child()
    statusbar = GtkTemplate.Child()
    entry = GtkTemplate.Child()

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.init_template()

        self.client = kwargs['client']
        self.client.connect('messages-received', self._on_message_received)
        self.client.connect('authenticated', self._on_authenticated)
        self.client.connect('auth-failed', self._on_auth_failed)

        self.settings = Gio.Settings.new('me.ramkrishna.Eidisi')
        for prop in ['username', 'password', 'hostname', 'port']:
           self.settings.bind(prop, self.client, prop, Gio.SettingsBindFlags.GET)

        self._add_action = Gio.SimpleAction.new('join', GLib.VariantType('s'))
        self._add_action.connect('activate', self._on_join_room)
        self.add_action(self._add_action)

        # start authentication

        self.client.login()

        #self.client.connect('notify::connected', self._on_connected_change)

    def _on_message_received(self, message):

        print("I received the message: %s"%(message))

    def _on_authenticated(self, value):

        print ("we are authenticated")

        self.statusbar.push(self.statusbar.get_context_id("loginauth"), "Connected")

    def _on_auth_failed(self, message):

        print ("authentication failed")

    def _on_join_room(self, action,param):

        print("I clicked on the plus button!")
        # Load the settings to see if we need to provide login details

        settings = Gio.Settings.new('me.ramkrishna.Eidisi')
        if settings.get_string("username") != None and \
           settings.get_string("password") != None and \
           settings.get_string("hostname") != None:
                dialog = Settings(transient_for=self, modal=True)
        else:
            pass

    def _connect(self, hostname, port, username, password):
        print ("hello!")

    def _add_action(self):
        print("I got nothing")
