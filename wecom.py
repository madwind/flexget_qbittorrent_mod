import time
from datetime import timedelta, datetime

import requests
from flexget import db_schema, plugin
from flexget.event import event
from flexget.manager import Session
from flexget.plugin import PluginError
from loguru import logger
from sqlalchemy import Column, Integer, String, DateTime, Boolean

_PLUGIN_NAME = 'wecom'

_CORP_ID = 'corp_id'
_CORP_SECRET = 'corp_secret'
_AGENT_ID = 'agent_id'
_TO_USER = 'to_user'
_GET_ACCESS_TOKEN_URL = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corp_id}&corpsecret={corp_secret}'
_POST_MESSAGE_URL = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
_UPLOAD_IMAGE = 'https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={access_token}&type=image'
_TEXT_LIMIT = 1024

AccessTokenBase = db_schema.versioned_base('wecom_access_token', 0)
MessageBase = db_schema.versioned_base('message', 0)

logger = logger.bind(name=_PLUGIN_NAME)


class AccessTokenEntry(AccessTokenBase):
    __tablename__ = 'wecom_access_token'

    id = Column(String, primary_key=True)
    corp_id = Column(String, index=True, nullable=True)
    corp_secret = Column(String, index=True, nullable=True)
    access_token = Column(String, primary_key=True)
    expires_in = Column(Integer, index=True, nullable=True)
    gmt_modify = Column(DateTime, index=True, nullable=True)

    def __str__(self):
        x = ['id={0}'.format(self.id)]
        if self.corp_id:
            x.append('corp_id={0}'.format(self.corp_id))
        if self.corp_secret:
            x.append('corp_secret={0}'.format(self.corp_secret))
        if self.access_token:
            x.append('access_token={0}'.format(self.access_token))
        if self.expires_in:
            x.append('expires_in={0}'.format(self.expires_in))
        if self.gmt_modify:
            x.append('gmt_modify={0}'.format(self.gmt_modify))
        return ' '.join(x)


class MessageEntry(MessageBase):
    __tablename__ = 'message'

    id = Column(Integer, primary_key=True)
    content = Column(String, index=True, nullable=True)
    sent = Column(Boolean, index=True, nullable=True)

    def __str__(self):
        x = ['id={0}'.format(self.id)]
        if self.content:
            x.append('content={0}'.format(self.content))
        if self.sent:
            x.append('sent={0}'.format(self.sent))
        return ' '.join(x)


class WeComNotifier:
    _corp_id = None
    _corp_secret = None
    _agent_id = None
    _to_user = None

    schema = {
        'type': 'object',
        'properties': {
            _CORP_ID: {'type': 'string'},
            _CORP_SECRET: {'type': 'string'},
            _AGENT_ID: {'type': 'string'},
            _TO_USER: {'type': 'string'},
            'image': {'type': 'string'}
        },
        'additionalProperties': False,
    }

    def notify(self, title, message, config):
        if not message.strip():
            return
        self._parse_config(config)
        session = Session()

        self._save_message(message, session)
        session.commit()

        message_list = session.query(MessageEntry).filter(MessageEntry.sent == False).all()

        try:
            if access_token := self._get_access_token(session, self._corp_id, self._corp_secret):
                for message_entry in message_list:
                    self._send_msgs(message_entry, access_token)
                    time.sleep(1)
                    if message_entry.sent:
                        session.delete(message_entry)
                        session.commit()
                if self.image:
                    self._send_images(access_token)
        except Exception as e:
            raise PluginError(str(e))

    def _parse_config(self, config):
        self._corp_id = config.get(_CORP_ID)
        self._corp_secret = config.get(_CORP_SECRET)
        self._agent_id = config.get(_AGENT_ID)
        self._to_user = config.get(_TO_USER)
        self.image = config.get('image')

    def _save_message(self, msg, session):
        msg_limit, msg_extend = self._get_msg_limit(msg)

        message_entry = MessageEntry(
            content=msg_limit,
            sent=False
        )
        session.add(message_entry)

        if msg_extend:
            self._save_message(msg_extend, session)

    def _request(self, method, url, **kwargs):
        try:
            response_json = requests.request(method, url, **kwargs, timeout=60).json()
            if response_json.get('errcode') != 0:
                raise PluginError(response_json)
            return response_json
        except Exception as e:
            raise PluginError(str(e))

    def _send_msgs(self, message_entry, access_token):
        data = {
            'touser': self._to_user,
            'msgtype': 'text',
            'agentid': self._agent_id,
            'text': {'content': message_entry.content},
            'safe': 0,
            'enable_id_trans': 0,
            'enable_duplicate_check': 0,
            'duplicate_check_interval': 1800
        }
        response_json = self._request('post', _POST_MESSAGE_URL.format(access_token=access_token.access_token),
                                      json=data)
        if response_json.get('errcode') == 0:
            message_entry.sent = True
        else:
            logger.error(f'request_data: {data}, response_json: {response_json}')

    def _get_msg_limit(self, msg):
        msg_encode = msg.encode()
        if len(msg_encode) < _TEXT_LIMIT:
            return msg, ''
        msg_lines = msg.split('\n')
        msg_limit_len = 0
        for line in msg_lines:
            line_len = len(line.encode())

            if msg_limit_len == 0 and line_len >= _TEXT_LIMIT:
                return msg_encode[:_TEXT_LIMIT].decode(), msg_encode[_TEXT_LIMIT:].decode()

            if msg_limit_len + line_len + 1 < _TEXT_LIMIT:
                msg_limit_len += line_len + 1
            else:
                return msg_encode[:msg_limit_len].decode(), msg_encode[msg_limit_len:].decode()

    def _get_access_token(self, session, corp_id, corp_secret):
        logger.debug('loading cached access token')
        access_token = self._get_cached_access_token(session, corp_id, corp_secret)
        logger.debug('found cached access token: {0}'.format(access_token))
        update = False
        if access_token:
            if access_token.gmt_modify > datetime.now() - timedelta(seconds=access_token.expires_in):
                logger.debug('all access token found in cache')
                return access_token
            else:
                update = True
        logger.debug('loading new access token')
        new_access_token = self._get_new_access_token(corp_id, corp_secret)
        logger.debug('found new access token: {0}'.format(access_token))

        if update:
            logger.info('saving updated access_token to db')
            access_token.access_token = new_access_token.access_token
            access_token.expires_in = new_access_token.expires_in
            access_token.gmt_modify = new_access_token.gmt_modify
        else:
            session.add(new_access_token)
        session.commit()

        return new_access_token

    def _get_access_token_n_update_db(self, session):
        access_token, has_new_access_token = self._get_access_token(session, self._corp_id, self._corp_secret)
        logger.debug('access_token={}', access_token)

        if not access_token:
            raise PluginError(
                'no access token found'
            )
        else:
            if not access_token.access_token:
                logger.warning('no access_token found for corp_id: {} and corp_secret: {}', self._corp_id,
                               self._corp_secret)
            if has_new_access_token:
                self._update_db(session, access_token)

        return access_token

    def _get_cached_access_token(self, session, corp_id, corp_secret):
        access_token = session.query(AccessTokenEntry).filter(
            AccessTokenEntry.id == '{}{}'.format(corp_id, corp_secret)).one_or_none()

        return access_token

    def _get_new_access_token(self, corp_id, corp_secret):
        response_json = self._request('get',
                                      _GET_ACCESS_TOKEN_URL.format(corp_id=corp_id, corp_secret=corp_secret))

        entry = AccessTokenEntry(
            id='{}{}'.format(corp_id, corp_secret),
            corp_id=corp_id,
            corp_secret=corp_secret,
            access_token=response_json.get('access_token'),
            expires_in=response_json.get('expires_in'),
            gmt_modify=datetime.now()
        )
        return entry

    def _get_media_id(self, access_token):
        file = ('images', ('flexget.png', open(self.image, 'rb'), 'image/png')),
        response_json = self._request('post', _UPLOAD_IMAGE.format(access_token=access_token.access_token),
                                      files=file)
        return response_json.get('media_id')

    def _send_images(self, access_token):
        media_id = self._get_media_id(access_token)
        if media_id is None:
            return
        data = {
            "touser": self._to_user,
            "msgtype": "image",
            "agentid": self._agent_id,
            "image": {
                "media_id": media_id
            }
        }
        self._request('post', _POST_MESSAGE_URL.format(access_token=access_token.access_token),
                      json=data)


@event('plugin.register')
def register_plugin():
    plugin.register(WeComNotifier, _PLUGIN_NAME, api_ver=2, interfaces=['notifiers'])
