from ..schema.nexusphp import AttendanceHR



class MainClass(AttendanceHR):
    URL = 'https://www.pthome.net/'
    USER_CLASSES = {
        'downloaded': [1073741824000, 3221225472000],
        'share_ratio': [6, 9],
        'days': [280, 700]
    }
