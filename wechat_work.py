from datetime import timedelta, datetime

import requests
from flexget import db_schema, plugin
from flexget.event import event
from flexget.manager import Session
from flexget.plugin import PluginError
from loguru import logger
from sqlalchemy import Column, Integer, String, DateTime

_PLUGIN_NAME = 'wechat_work'

_CORP_ID = 'corp_id'
_CORP_SECRET = 'corp_secret'
_AGENT_ID = 'agent_id'
_TO_USER = 'to_user'
_GET_ACCESS_TOKEN_URL = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corp_id}&corpsecret={corp_secret}'
_POST_MESSAGE_URL = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
_UPLOAD_IMAGE = 'https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={access_token}&type=image'
_TEXT_LIMIT = 1024

AccessTokenBase = db_schema.versioned_base('wechat_work_access_token', 0)

logger = logger.bind(name=_PLUGIN_NAME)


class AccessTokenEntry(AccessTokenBase):
    __tablename__ = 'wechat_work_access_token'

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


class WeChatWorkNotifier:
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
        access_token = self._real_init(Session(), config)

        if not access_token:
            return
        self._send_msgs(message, access_token)
        if self.image:
            self._send_images(access_token)

    def _parse_config(self, config):
        self._corp_id = config.get(_CORP_ID)
        self._corp_secret = config.get(_CORP_SECRET)
        self._agent_id = config.get(_AGENT_ID)
        self._to_user = config.get(_TO_USER)
        self.image = config.get('image')

    def _real_init(self, session, config):
        self._parse_config(config)
        access_token = self._get_access_token_n_update_db(session)
        return access_token

    def _request(self, method, url, **kwargs):
        try:
            return requests.request(method, url, **kwargs)
        except Exception as e:
            raise PluginError(str(e))

    def _send_msgs(self, msg, access_token):
        msg_limit, msg_extend = self._get_msg_limit(msg)

        data = {
            'touser': self._to_user,
            'msgtype': 'text',
            'agentid': self._agent_id,
            'text': {'content': msg_limit},
            'safe': 0,
            'enable_id_trans': 0,
            'enable_duplicate_check': 0,
            'duplicate_check_interval': 1800
        }
        response_json = self._request('post', _POST_MESSAGE_URL.format(access_token=access_token.access_token),
                                      json=data).json()
        if response_json.get('errcode') != 0:
            logger.error(response_json)

        if msg_extend:
            self._send_msgs(msg_extend, access_token)

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

    def _get_access_token_n_update_db(self, session):
        corp_id = self._corp_id
        corp_secret = self._corp_secret

        access_token, has_new_access_token = self._get_access_token(session, corp_id, corp_secret)
        logger.debug('access_token={}', access_token)

        if not access_token:
            raise PluginError(
                'no access token found'
            )
        else:
            if not access_token.access_token:
                logger.warning('no access_token found for corp_id: {} and corp_secret: {}', corp_id, corp_secret)
            if has_new_access_token:
                self._update_db(session, access_token)

        return access_token

    def _get_access_token(self, session, corp_id, corp_secret):
        logger.debug('loading cached access token')
        access_token = self._get_cached_access_token(session, corp_id, corp_secret)
        logger.debug('found cached access token: {0}'.format(access_token))

        if access_token:
            if access_token.gmt_modify > datetime.now() - timedelta(seconds=access_token.expires_in):
                logger.debug('all access token found in cache')
                return access_token, False
            else:
                self._delete_db(session, access_token)

        logger.debug('loading new access token')
        new_access_token = self._get_new_access_token(corp_id, corp_secret)
        logger.debug('found new access token: {0}'.format(access_token))

        return new_access_token, bool(new_access_token)

    @staticmethod
    def _get_cached_access_token(session, corp_id, corp_secret):
        access_token = session.query(AccessTokenEntry).filter(
            AccessTokenEntry.id == '{}{}'.format(corp_id, corp_secret)).one_or_none()

        return access_token

    def _get_new_access_token(self, corp_id, corp_secret):
        response_json = self._request('get',
                                      _GET_ACCESS_TOKEN_URL.format(corp_id=corp_id, corp_secret=corp_secret)).json()

        entry = AccessTokenEntry(
            id='{}{}'.format(corp_id, corp_secret),
            corp_id=corp_id,
            corp_secret=corp_secret,
            access_token=response_json.get('access_token'),
            expires_in=response_json.get('expires_in'),
            gmt_modify=datetime.now()
        )
        return entry

    def _update_db(self, session, access_token):
        logger.info('saving updated access_token to db')

        session.add(access_token)
        session.commit()

    def _delete_db(self, session, access_token):
        logger.info('delete access_token from db')

        session.delete(access_token)
        session.commit()

    def _get_media_id(self, access_token):
        file = ('images', ('flexget.png', open(self.image, 'rb'), 'image/png')),
        response_json = self._request('post', _UPLOAD_IMAGE.format(access_token=access_token.access_token),
                                      files=file).json()
        if response_json.get('errcode') != 0:
            logger.error(response_json)
        else:
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
        response_json = self._request('post', _POST_MESSAGE_URL.format(access_token=access_token.access_token),
                                      json=data).json()
        if response_json.get('errcode') != 0:
            logger.error(response_json)


@event('plugin.register')
def register_plugin():
    plugin.register(WeChatWorkNotifier, _PLUGIN_NAME, api_ver=2, interfaces=['notifiers'])
