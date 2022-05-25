from abc import ABC

from .detail import Detail
from .message import Message
from .reseed import Reseed
from ..base.request import Request
from ..base.sign_in import SignIn


class SiteBase(Request, SignIn, Detail, Message, Reseed, ABC):
    pass
