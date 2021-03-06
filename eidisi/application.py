#!/usr/bin/env python3
#
# application.py
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
from .window import ApplicationWindow
from .settings import Settings

class Application(Gtk.Application):
    __gtype_name_ = "Application"

   # used to check to see if username and password exists

    version = GObject.Property(type=str, flags=GObject.ParamFlags.CONSTRUCT_ONLY|GObject.ParamFlags.READWRITE)

    def __init__(self, **kwargs):
        super().__init__(application_id='me.ramkrishna.Eidisi',
                         flags=Gio.ApplicationFlags.HANDLES_OPEN, **kwargs)
        if GLib.get_prgname() == '__main__.py':
            GLib.set_prgname('eidsi')

        self.window = None
        self.client = None
        self.settings = Gio.Settings.new('me.ramkrishna.Eidisi')

    def do_startup(self):
        Gtk.Application.do_startup(self)

        action = Gio.SimpleAction.new('quit')
        action.connect('activate', lambda act, param: self.quit())
        self.add_action(action)

        action = Gio.SimpleAction.new('about')
        action.connect('activate', self.on_about)
        self.add_action(action)

        action = Gio.SimpleAction.new('settings')
        action.connect('activate', self.on_settings)
        self.add_action(action)

        action = Gio.SimpleAction.new('join')
        action.connect('activate', self._on_joinroom)
        self.add_action(action)

    def do_activate(self):
        def on_window_destroy(window):
            self.window = None
#            self.client.props.timeout = 30 # We can relax the timer if there is no UI

        if not self.window:
            print("username is",self.settings['username'])
            if self.settings['username'] != None and \
               self.settings['password'] != None and \
               self.settings['hostname'] != None:

                    self.client = GnomeMatrixClientApi(username=self.settings['username'],
                                                       password=self.settings['password'],
                                                       hostname=self.settings['hostname'],
                                                       port=self.settings['port'])

#            for prop in ['username', 'password', 'hostname', 'port']:
#                self.settings.bind(prop, self.client, prop, Gio.SettingsBindFlags.GET)

            self.window = ApplicationWindow(application=self, client=self.client)
            self.window.connect('destroy', on_window_destroy)
            self.client.login()

            self.window.present()


    def do_shutdown(self):
        Gtk.Application.do_shutdown(self)

    def _on_joinroom():
        print("oh yeah, we got clicked!")

    def on_settings(self, action, params):

        dialog = Settings(modal=True)
        dialog.present()

    def on_about(self, action, param):
        about = Gtk.AboutDialog(transient_for=self.window, modal=True,
                                license_type=Gtk.License.GPL_3_0,
                                authors=['Sriram Ramkrishna', ],
                                copyright='Copyright © 2017 Sriram Ramkrishna',
                                logo_icon_name='me.ramkrishna.Eidisi',
                                version=self.version)
        about.present() 
