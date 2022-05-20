from ..schema.nexusphp import AttendanceHR


class MainClass(AttendanceHR):
    URL = 'http://hdzone.me/'
    USER_CLASSES = {
        'downloaded': [8796093022208],
        'share_ratio': [5.5],
        'days': [70]
    }
