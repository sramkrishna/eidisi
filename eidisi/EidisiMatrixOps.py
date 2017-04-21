#!/usr/bin/env python3
# Copyright Sriram Ramkrishna <sri@ramkrishna.me>
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.#

import json
import pprint
import logging
import urllib.parse
import urllib.request
import gi
gi.require_version('Soup', '2.4')

from gi.repository import (
    GLib,
    GObject,
    Gio,
    Soup,
)

MATRIX_V2_API_PATH = "/_matrix/client/r0"

class GnomeMatrixClientApi(GObject.Object):
    """GObject based Matrix Client """

    __gtype_name__ = 'Client'

    __gsignals__ = {
        'messages-received': (GObject.SIGNAL_RUN_FIRST, None, (int,))
    }
    __gproperties__ = {
        'username': (
            str, 'Username', 'Username to login with', '',
            GObject.PARAM_READWRITE
            ),
        'password': (
            str, 'Password', 'Password to login with', '',
            GObject.PARAM_READWRITE,
            ),
        'hostname': (
            str, 'Hostname', 'Hostname of remote server', '',
            GObject.PARAM_READWRITE,
            ),
        'port:': (
            int, 'Port', 'Port of remote server', 1,
            GLib.MAXUINT16, 9091,
            GObject.PARAM_READWRITE,
            ),
        'tls:': (
            bool, 'TLS', 'Connect using HTTPS', False,
            GObject.PARAM_READWRITE,
            ),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.hostname = 'matrix.org'
        self.port =''
        self.username = ''
        self.password = ''
        self.token = None # token for future interactions
        self.home_server = None
        self.userid = None
        self.next_batch = None

        self.base_url = 'https://%s:%s'%(self.hostname,self.port)
        self.api_path = "/_matrix/client/r0"

        self._session = Soup.Session.new()


        for prop in ('username', 'password'):
            self.connect('notify::' + prop, self._on_authentication)

#        for prop in ('hostname', 'port', 'tls'):
#            self.connect('notify::' + prop, self._on_server_changed)

#        if self.username and self.password:
#            self._session.add_feature(Soup.AuthBasic)

    def _on_authentication(self, session, message, auth, retrying):

        if not retrying and self.username and self.passwword:
            logging.info('Authenticating as []'.format(self.username))
            auth.authenticate(self.username,self.password)

    def do_get_property(self, prop):
        return getattr(self,prop.name.replace('-','_'))

    def do_set_property(self, prop, value):
        setattr(self, prop.name.replace('-', '_'), value)

    def session_get(self, arguments, callback=None):
        self._make_request_async('session-set', arguments, callback=callback)

    def _on_message_finish(self, session, message, user_data=None):


        logging.info("in on_message")

        status_code = message.props.status_code
        logging.debug('Got response code: {} ({})'.format(Soup.Status(status_code).value_name,

                                                        status_code))
        print("status code = %d"%(status_code))

        if status_code == Soup.Status.UNAUTHORIZED:
           if not self.login or not self.password:
                logging.warning('Requires login and password')
           else:
               logging.warning('Failed to authenticate using {}'.format(self.login))

        if not 200 <= status_code < 300:
            logging.warning('Response was not successful')
            return

        response_str = message.props.response_body_data.get_data().decode('UTF-8')
        response = json.loads(response_str)

#        logging.debug('<<<\n{}'.format(pprint.pformat(response)))


        if user_data:
            user_data(response)

    def _create_message(self,method, url, payload):
        msg = Soup.Message.new(method, url)
        msg.set_request("application/json", Soup.MemoryUse.COPY,
                        bytes(payload,'UTF-8'))
        return msg

    def _make_request_async(self, method, url, content=None,
                                query_params={}, headers={}, callback=None):

        # create our message that we want to send
        #FIXME: test 'method' to make sure it is valid

        query_uri = ""
        payload = ""

        if self.token:
            query_params["access_token"] = self.token
            query_params["user_id"] = self.userid

            query_uri=urllib.parse.urlencode(query_params)

        if query_uri:
            req_url = self.base_url + self.api_path + url+'?'+query_uri
        else:
            req_url = self.base_url + self.api_path + url
#        print(req_url)
        if content is not None:
            payload = json.dumps(content)
        msg_to_send = self._create_message(method, req_url, payload)
        self._session.queue_message(msg_to_send, self._on_message_finish,
                                    user_data=callback)

    def _handle_login(self,response):
        """ call back for login """

        self.userid = response["user_id"]
        self.token = response["access_token"]
        self.home_server = response["home_server"]

        GLib.timeout_add_seconds(2, self._handle_sync)


    def login(self, login_type="m.login.password", **kwargs):
        """ perform matrix login """

        content = {
            "type": login_type
        }

        for keys in kwargs:
            content[keys] = kwargs[keys]

        self._make_request_async('POST', '/login', content, callback=self._handle_login)

    def _handle_register(self, response):
        """ handle register call """

        self.userid = response["user_id"]
        self.token = response["access_token"]
        self.home_server = response["access_token"]

    def register(self, login_type="m.login.password", **kwargs):
        """ performs /register """

        content = {
            "type": login_type
        }

        for key in kwargs:
            content[key] = kwargs[key]

        self._make_request_async('POST', '/register', content,
                                 self._handle_register)

    def logout(self):
        """ perform /logout """

        self._make_request_async("POST","/logout")

    def create_room(self, alias=None, is_public=False, invitees=()):
        """ Create a room """

        content = {
            "visibility": "public" if is_public else "private"
        }

        if alias:
            content["room_alias_name"] = alias

        if invitees:
            content["invite"] = invitees

        self._make_request_async('POST', '/createRoom', content)

    def join_room(self, room_id_or_alias):
        """ join a room """

        if not room_id_or_alias:
            print ("not a valid room id")

        path = "/join/%s" % quote(room_id_or_alias)

        self._make_request_async("POST", path)

    def sendmsg(self, msgtype, message):
        """ sends a message to a room """
        content = {
            "msgtype": msgtype,
            "body": message
        }

    def _handle_sync_output(self, response):

        logging.info("sent an emit")
        # capture the next batch so we know what to sync against next time.
        self.next_batch = response['next_batch']
        self.emit("messages-received", 42)

    def _handle_sync(self, since=None, timeout_ms=3000, filter=None,
                     full_state=None, set_presence=None):

        request = {
            "timeout": timeout_ms
        }

        if self.next_batch:
            request["since"] = self.next_batch
        if filter:
            request["filter"] = filter

        if full_state:
            request["full_state"] = full_state

        if set_presence:
            request["set_presence"] = set_presence

        self._make_request_async("GET", "/sync", query_params=request,
                                    callback=self._handle_sync_output)

        return True
