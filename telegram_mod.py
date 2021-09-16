import copy

from PIL import Image
from flexget import plugin
from flexget.components.notify.notifiers.telegram import TelegramNotifier
from flexget.event import event
from flexget.manager import Session
from flexget.plugin import PluginWarning

try:
    import telegram
    from telegram.error import ChatMigrated, TelegramError
    from telegram.utils.request import NetworkError
except ImportError:
    telegram = None
    TelegramError = None
    ChatMigrated = None

_IMAGE_ATTR = 'image'
_TEXT_LIMIT = 4096
_PLUGIN_NAME = 'telegram_mod'


def dict_merge(dict1, dict2):
    for i in dict2:
        if isinstance(dict1.get(i), dict) and isinstance(dict2.get(i), dict):
            dict_merge(dict1[i], dict2[i])
        else:
            dict1[i] = dict2[i]
    return dict1


class TelegramNotifierMod(TelegramNotifier):
    schema = dict_merge(copy.deepcopy(TelegramNotifier.schema), {
        'properties': {
            _IMAGE_ATTR: {'type': 'string'}
        }
    })

    def notify(self, title, message, config):
        if not message.strip():
            return
        session = Session()
        chat_ids = self._real_init(session, config)

        if not chat_ids:
            return
        msg_limits = self._get_msg_limits(message)
        for msg_limit in msg_limits:
            self._send_msgs(msg_limit, chat_ids, session)
        if self._image:
            self._send_photo(self._image, chat_ids, session)

    def _parse_config(self, config):
        super(TelegramNotifierMod, self)._parse_config(config)

        self._image = config.get(_IMAGE_ATTR)

    def _get_msg_limits(self, msg):
        msg_limits = ['']
        if len(msg) < _TEXT_LIMIT:
            return [msg]
        msg_lines = msg.split('\n')
        for line in msg_lines:
            if len(msg_limits[-1] + line) > _TEXT_LIMIT and len(msg_limits[-1]) > 0:
                msg_limits.append('')
            msg_limits[-1] = msg_limits[-1] + line

    def _send_photo(self, image, chat_ids, session):
        for chat_id in (x.id for x in chat_ids):
            try:
                photo = Image.open(image)
                width = photo.width
                height = photo.height
                if width + height > 10000 or width / height > 20:
                    try:
                        self._bot.sendDocument(chat_id=chat_id, document=open(image, 'rb'))
                    except ChatMigrated as e:
                        try:
                            self._bot.sendDocument(chat_id=e.new_chat_id, document=open(image, 'rb'))
                            self._replace_chat_id(chat_id, e.new_chat_id, session)
                        except TelegramError as e:
                            raise PluginWarning(e.message)
                else:
                    try:
                        self._bot.sendPhoto(chat_id=chat_id, photo=open(image, 'rb'))
                    except ChatMigrated as e:
                        try:
                            self._bot.sendPhoto(chat_id=e.new_chat_id, photo=open(image, 'rb'))
                            self._replace_chat_id(chat_id, e.new_chat_id, session)
                        except TelegramError as e:
                            raise PluginWarning(e.message)

            except TelegramError as e:
                raise PluginWarning(e.message)


@event('plugin.register')
def register_plugin():
    plugin.register(TelegramNotifierMod, _PLUGIN_NAME, api_ver=2, interfaces=['notifiers'])
