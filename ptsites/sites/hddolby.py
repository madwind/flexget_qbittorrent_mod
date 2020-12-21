from ..schema.nexusphp import AttendanceHR


class MainClass(AttendanceHR):
    URL = 'https://www.hddolby.com/'
    USER_CLASSES = {
        'downloaded': [1099511627776, 8796093022208],
        'share_ratio': [4, 5.5],
        'days': [112, 336]
    }
