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
from urllib.parse import quote

from time import time, sleep

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

    __gtype_name__ = 'GnomeMatrixClientApi'

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
        'port': (
            int, 'Port', 'Port of remote server', 1,
            GLib.MAXUINT16, 8448,
            GObject.PARAM_READWRITE,
            ),
        'authenticated': (
            bool, 'Authenticated', 'Have successfully authenticated',
            False, GObject.PARAM_READWRITE,
        ),
        'tls:': (
            bool, 'TLS', 'Connect using HTTPS', False,
            GObject.PARAM_READWRITE,
            ),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.hostname = kwargs['hostname']
#        self.port = '
        self.port = kwargs['port']
        self.username = kwargs['username']
        self.password = kwargs['password']
        self.home_server = None
        self.userid = kwargs['username']

        self.token = None # token for future interactions
        self.next_batch = None # time for next sync
        self.transactionid = None

        self.base_url = 'https://%s:%s'%(self.hostname,self.port)
        self.api_path = "/_matrix/client/r0"

        self.sync_filter = ''
        self.cur_room = ''
        self.transactionid = 0
        self.default_room_alias='#test:matrix.org'
        self.default_room_id=''
        self.sendqueue = []
        self.wait_for_response = False

        self._session = Soup.Session.new()


        for prop in ('username', 'password'):
            self.connect('notify::' + prop, self._on_authentication)

#        for prop in ('hostname', 'port', 'tls'):
#            self.connect('notify::' + prop, self._on_server_changed)

#        if self.username and self.password:
#            self._session.add_feature(Soup.AuthBasic)

    def _on_authentication(self, session, message, auth, retrying):

        if not retrying and self.username and self.passwword:
            logging.warning('Authenticating as []'.format(self.username))
            auth.authenticate(self.username,self.password)

    def do_get_property(self, prop):
        return getattr(self,prop.name.replace('-','_'))

    def do_set_property(self, prop, value):
        setattr(self, prop.name.replace('-', '_'), value)

    def session_get(self, arguments, callback=None):
        self._make_request_async('session-set', arguments, callback=callback)

    def _on_message_finish(self, session, message, user_data=None):


        if user_data:
            logging.warning("in on_message, to handle %s"%(user_data.__name__))
        else:
            print("there is no callback")

        status_code = message.props.status_code
        logging.debug('Got response code: {} ({})'.format(Soup.Status(status_code).value_name,
                                                        status_code))
        print("status code = %d"%(status_code))

        self.wait_for_response = False

        if status_code == Soup.Status.UNAUTHORIZED:
           if not self.login or not self.password:
                logging.warning('Requires login and password')
           else:
               logging.warning('Failed to authenticate using {}'.format(self.login))

        response_str = message.props.response_body_data.get_data().decode('UTF-8')

        if not 200 <= status_code < 300:
            logging.warning('Response was not successful')
            print("output is:%s"%(response_str))
            return

        print("the json response is %s"%response_str)
        response = json.loads(response_str)

#        logging.debug('<<<\n{}'.format(pprint.pformat(response)))
        if user_data:
            user_data(response)

        print("now checking to see if we have something else to send",
            self.sendqueue)

# after we come back from handling the callback, we want to check if we have
# something we have to send.

        if self.sendqueue and self.wait_for_response is False: # check if we have anything in our sendqueue
            [method, url, content, query_params,
            headers, callback] = self.sendqueue.pop()
            print ("making the call with:",method, url, content, query_params, headers, callback)
            self._make_request_async(method, url, content, query_params={},
                                      headers={}, callback=None)


    def _create_message(self,method, url, payload):
        msg = Soup.Message.new(method, url)
        msg.set_request("application/json", Soup.MemoryUse.COPY,
                        bytes(payload,'UTF-8'))
        return msg

    def _make_request_async(self, method, url, content=None,
                                query_params={}, headers={}, callback=None):

        # create our message that we want to send
        #FIXME: test 'method' to make sure it is valid

        #TODO validate that method is correct (GET, POST, PUT)

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
            try:
                payload = json.dumps(content)
            except TypeError :
                print("not a valid input for json.dump")

        msg_to_send = self._create_message(method, req_url, payload)
        print("queuing message %s"%(req_url))
        print("with payload %s"%content)
        self.wait_for_response = True
        self._session.queue_message(msg_to_send, self._on_message_finish,
                                    user_data=callback)

    def _handle_default_room_id(self,response):
        """ handles response from query of room id from room alias """

        print("in handle_default_room_id = %s"%(response["room_id"]))

        self.default_room_id = response["room_id"]
        self.props.authenticated = True
#        GLib.timeout_add_seconds(4, self._handle_sync)

    def _handle_login(self,response):
        """ call back for login """

        self.userid = response["user_id"]
        self.token = response["access_token"]
        self.home_server = response["home_server"]

        print("token is %s"%self.token)


        # get a defaeult room on login.
        room_id_query_url = "/directory/room/%s"%(quote(self.default_room_alias))

        if self.wait_for_response:
            self.sendqueue.append(["GET", room_id_query_url, None, None, None,
                                    'self._handle_default_room_id'])
        else:
            self._make_request_async('GET', room_id_query_url,content=None,
                                query_params={}, headers={},
                                callback=self._handle_default_room_id)


    def login(self, login_type="m.login.password"):
        """ perform matrix login """


        content = {
            "type": login_type,
            "user": self.username,
            "password": self.password
        }

        logging.warning("sending request")

        self._make_request_async('POST', '/login', content,
                                  callback=self._handle_login)

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

    def _handle_join(self, response):
        """ handle the ouput from a join room """

        room_id = (
            response['room_id'] if "room_id" in response else
                                                self.room_id_or_alias
                   )
        print ("in _handle_join")
        print ("room id = %s"%(room_id))
        self.cur_room = room_id # save which room we are in

    def join_room(self, room_id_or_alias):
        """ join a room """

        if not room_id_or_alias:
            print ("not a valid room id")

        self.room_id_or_alias = room_id_or_alias # need to save this


        path = "/join/%s" % quote(room_id_or_alias)
        print("path in join_room is %s"%(path))

        print("joining room")
#        self._make_request_async("POST", path, callback=self._handle_join)
        if self.wait_for_response:
            self.sendqueue.append(["POST", path, None, None, None,
                                    'self._handle_join'])
        else:
            self._make_request_async("POST", path, callback=self._handle_join)

    def send_message(self, message, msgtype="m.text", room_id=None):
        """ sends a message of type 'm.text' to the current room """

        if not room_id:
            room_id = self.default_room_id

        self.sendmsg(msgtype, message, room_id, self.transactionid)

    def sendmsg(self, msgtype, message, room_id, transactionid=None):
        """ sends a message of any type to a room """
        content = {
            "body":message,
            "msgtype":msgtype
        }

        print ("I am in sendmsg")
        if not transactionid:
            transactionid = str(self.transactionid) + str(int(time() * 1000))

        self.transactionid = self.transactionid + 1

        if not room_id:
            room_id = self.default_room_id

#        url_path = "/rooms/%s/send/m.room.message/%s"%(quote(room_id),
#                                           quote(str(self.transactionid)))
        url_path = "/rooms/%s/send/m.room.message"%(quote(room_id))
        logging.warn("sending urlpath = %s"%(url_path))
        print("********")
        print("we are waitingn for response?", self.wait_for_response)
        print("content = %s"%(content))
        print("********")
        if self.wait_for_response:
            print("we are queuing this request")
            self.sendqueue.append(["POST", url_path, content, None, None, None])
        else:
            self._make_request_async("PUT", url_path, content)

    def _handle_sync_output(self, response):

        logging.warning("sent an emit")
        # capture the next batch so we know what to sync against next time.
        self.next_batch = response['next_batch']
        self.emit("messages-received", 42)

    def _handle_sync(self, since=None, timeout_ms=3000, filter=None,
                     full_state=None, set_presence=None):

        filter = '{ "room": { "timeline": { "limit": 20 } } }'

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
