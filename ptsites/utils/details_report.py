import re
from datetime import datetime

from flexget import db_schema
from flexget.manager import Session
from loguru import logger
from sqlalchemy import Column, String, Integer, Float

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

try:
    import pandas as pd
except ImportError:
    pd = None

UserDetailsBase = db_schema.versioned_base('user_details', 0)

suffix = {'B': 1, 'K': 1024, 'M': 1048576, 'G': 1073741824, 'T': 1099511627776, 'P': 1125899906842624,
          'E': 1152921504606846976, 'Z': 1180591620717411303424}

math_suffix = {'': 1, 'K': 1000, 'M': 1000000, 'B': 1000000000}


class UserDetailsEntry(UserDetailsBase):
    __tablename__ = 'user_details'

    site = Column(String, primary_key=True)
    uploaded = Column(Integer, index=True, nullable=True)
    downloaded = Column(Integer, index=True, nullable=True)
    share_ratio = Column(Float, index=True, nullable=True)
    points = Column(Float, index=True, nullable=True)
    seeding = Column(Integer, index=True, nullable=True)
    leeching = Column(Integer, index=True, nullable=True)
    hr = Column(Integer, index=True, nullable=True)

    def __str__(self):
        x = ['site={0}'.format(self.site)]
        if self.uploaded:
            x.append('uploaded={0}'.format(self.uploaded))
        if self.downloaded:
            x.append('downloaded={0}'.format(self.downloaded))
        if self.share_ratio:
            x.append('share_ratio={0}'.format(self.share_ratio))
        if self.points:
            x.append('points={0}'.format(self.points))
        if self.seeding:
            x.append('seeding={0}'.format(self.seeding))
        if self.leeching:
            x.append('leeching={0}'.format(self.leeching))
        if self.hr:
            x.append('hr={0}'.format(self.hr))
        return ' '.join(x)


class DetailsReport:
    def build(self, task):
        if not (plt and pd):
            logger.warning('Dependency does not exist: [matplotlib, pandas]')
            return
        if not task.accepted and not task.failed:
            return

        session = Session()

        columns = ['site',
                   'uploaded',
                   'downloaded',
                   'share_ratio',
                   'points',
                   'seeding',
                   'leeching',
                   'hr', ]

        data = {
            'sort_column': [],
            'default_order': []
        }

        total_details = {}

        total_changed = {}

        for column in columns:
            data[column] = []
            total_details[column] = 0
            total_changed[column] = 0

        order = len(task.all_entries)

        for entry in task.all_entries:
            data['default_order'].append(order)
            order = order - 1
            user_details_db = self._get_user_details(session, entry['site_name'])
            if user_details_db is None:
                user_details_db = UserDetailsEntry(
                    site=entry['site_name'],
                    uploaded=0,
                    downloaded=0,
                    share_ratio=0,
                    points=0,
                    seeding=0,
                    leeching=0,
                    hr=0
                )
                session.add(user_details_db)
                session.commit()
                user_details_db = self._get_user_details(session, entry['site_name'])

            # failed
            if not entry.get('details'):
                for column in columns:
                    value = getattr(user_details_db, column)
                    if entry.failed:
                        data[column].append(self.buid_data_text(column, value) + '*')
                    else:
                        data[column].append(self.buid_data_text(column, value))
                    if not entry.get('do_not_count') and column not in ['site']:
                        self.count(total_details, column, value)
                data['sort_column'].append(0)
                continue

            # now
            details_now = {}
            for key, value in entry['details'].items():
                details_now[key] = self.transfer_data(key, value)

            # changed
            details_changed = {}
            for key, value_now in details_now.items():
                if value_now != '*':
                    details_changed[key] = value_now - getattr(user_details_db, key)
                else:
                    details_changed[key] = '*'
            if details_changed['uploaded'] == '*':
                data['sort_column'].append(0)
            else:
                data['sort_column'].append(details_changed['uploaded'])

            # append to data
            data['site'].append(entry['site_name'])
            for column in columns:
                if column == 'site':
                    continue
                data[column].append('{}{}'.format(self.buid_data_text(column, getattr(user_details_db, column)),
                                                  self.buid_data_text(column, details_changed[column], append=True)))
                if total_details.get(column) is None:
                    total_details[column] = 0
                if total_changed.get(column) is None:
                    total_changed[column] = 0
                if not entry.get('do_not_count') and column not in ['share_ratio', 'points']:
                    total_details[column] = total_details[column] + getattr(user_details_db, column)
                    if details_changed[column] != '*':
                        total_changed[column] = total_changed[column] + details_changed[column]

            # update db
            for key, value in details_now.items():
                if value != '*':
                    setattr(user_details_db, key, value)
            session.commit()

        data['site'].append('total')
        for column in columns:
            if column == 'site':
                continue
            data[column].append('{}{}'.format(self.buid_data_text(column, total_details[column]),
                                              self.buid_data_text(column, total_changed[column], append=True)))
        data['sort_column'].append(float('inf'))
        data['default_order'].append(float('inf'))
        df = pd.DataFrame(data)
        df.sort_values(by=['sort_column', 'default_order'], ascending=False, inplace=True)
        df.drop(columns=['sort_column', 'default_order'], inplace=True)
        line_count = len(data['site'])
        fig = plt.figure(figsize=(8, line_count / 1.8))
        plt.axis('off')
        colors = []
        for x in df.values:
            cc = []
            for y in x:
                if '\n-' in y:
                    cc.append('#f38181')
                elif '+' in y:
                    cc.append('#95e1d3')
                elif '*' in y:
                    cc.append('#eff48e')
                else:
                    cc.append('white')
            colors.append(cc)
        col_widths = [0.15, 0.16, 0.16, 0.13, 0.14, 0.1, 0.1, 0.06]
        table = plt.table(cellText=df.values, cellColours=colors, bbox=[0, 0, 1, 1], colLabels=df.columns,
                          colWidths=col_widths,
                          loc='best')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        fig.tight_layout()
        plt.title(datetime.now().replace(microsecond=0))
        plt.savefig('details_report.png', bbox_inches='tight', dpi=300)

    def _get_user_details(self, session, site):
        user_details = session.query(UserDetailsEntry).filter(
            UserDetailsEntry.site == site).one_or_none()
        return user_details

    def convert_suffix(self, details_value):
        keys = list(suffix.keys())
        keys.reverse()
        for key in keys:
            found = re.search(key, details_value)
            if found:
                num = re.search('[\\d.]+', details_value).group()
                if num:
                    return float(num) * suffix[key]

    def build_suffix(self, details_value, specifier):
        if details_value == 0:
            return '0'
        for key, value in suffix.items():
            num = details_value / value
            if num < 1000:
                return specifier.format(round(num, 3), key)

    def build_math_suffix(self, details_value, specifier):
        for key, value in math_suffix.items():
            num = details_value / value
            if num < 1000:
                return specifier.format(round(num, 3), key).rstrip()

    def buid_data_text(self, key, value, append=False):
        if value == '*' or key == 'site':
            return value
        if value == 0 and append:
            return ''
        if key in ['uploaded', 'downloaded']:
            if append:
                specifier = '\n{:+g} {}iB'
            else:
                specifier = '{:g} {}iB'
            return self.build_suffix(value, specifier)
        if key in ['points']:
            if append:
                specifier = '\n{:+g} {}'
            else:
                specifier = '{:g} {}'
            return self.build_math_suffix(value, specifier)
        if append:
            return '\n{:+g}'.format(value)
        else:
            return '{:g}'.format(value)

    def transfer_data(self, key, value):
        if value == '*':
            return value
        if key in ['uploaded', 'downloaded']:
            return float(self.convert_suffix(value))
        return float(value)

    def count(self, count_dict, key, value):
        if key not in ['share_ratio', 'points']:
            count_dict[key] = count_dict[key] + value
