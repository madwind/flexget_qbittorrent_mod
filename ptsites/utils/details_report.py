from __future__ import annotations

import re
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont
from datetime import datetime
from dateutil.parser import parse
from flexget import db_schema
from flexget.manager import Session
from flexget.task import Task
from loguru import logger
from matplotlib.font_manager import findfont, FontProperties
from pandas import DataFrame
from sqlalchemy import Column, String, Integer, Float, Date

try:
    import matplotlib.pyplot as plt
    import matplotlib

    matplotlib.use('agg')
except ImportError:
    plt = None

try:
    import pandas as pd
except ImportError:
    pd = None

UserDetailsBase = db_schema.versioned_base('user_details', 0)

suffix = {'B': 1, 'K': 1024, 'M': 1048576, 'G': 1073741824, 'T': 1099511627776, 'P': 1125899906842624,
          'E': 1152921504606846976, 'Z': 1180591620717411303424}

math_suffix = {'': 1, 'K': 1000, 'M': 1000000, 'B': 1000000000, 'T': 1000000000000, 'P': 1000000000000000}


class UserDetailsEntry(UserDetailsBase):
    __tablename__ = 'user_details'

    site = Column(String, primary_key=True)
    uploaded = Column(Integer, nullable=True)
    downloaded = Column(Integer, nullable=True)
    share_ratio = Column(Float, nullable=True)
    join_date = Column(Date, nullable=True)
    points = Column(Float, nullable=True)
    seeding = Column(Integer, nullable=True)
    leeching = Column(Integer, nullable=True)
    hr = Column(Integer, nullable=True)

    def __str__(self):
        x = ['site={0}'.format(self.site)]
        if self.uploaded:
            x.append('uploaded={0}'.format(self.uploaded))
        if self.downloaded:
            x.append('downloaded={0}'.format(self.downloaded))
        if self.share_ratio:
            x.append('share_ratio={0}'.format(self.share_ratio))
        if self.join_date:
            x.append('join_date={0}'.format(self.join_date))
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
    def build(self, task: Task) -> None:
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

        user_classes_dict = {}

        for column in columns:
            data[column] = []
            total_details[column] = 0
            total_changed[column] = 0

        order = len(task.all_entries)

        for entry in task.all_entries:
            user_classes_dict[entry['site_name']] = entry.get('user_classes')
            if entry.get('do_not_draw'):
                continue

            data['default_order'].append(order)
            order = order - 1
            user_details_db = self._get_user_details(session, entry['site_name'])
            if user_details_db is None:
                user_details_db = UserDetailsEntry(
                    site=entry['site_name'],
                    uploaded=0,
                    downloaded=0,
                    share_ratio=0,
                    join_date=datetime.now().date(),
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
                    failed_suffix = '*' if entry.failed else ''
                    data[column].append(self.build_data_text(column, value) + failed_suffix)
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
                details_changed[key] = value_now - getattr(user_details_db, key) if value_now != '*' and key not in [
                    'join_date'] else '*'
            data['sort_column'].append(0 if details_changed['uploaded'] == '*' else details_changed['uploaded'])

            # append to data
            for column in columns:
                if column == 'site':
                    data['site'].append(self.build_data_text(column, entry['site_name']))
                    continue
                data[column].append('{}{}'.format(self.build_data_text(column, getattr(user_details_db, column)),
                                                  self.build_data_text(column, details_changed[column], append=True)))
                if total_details.get(column) is None:
                    total_details[column] = 0
                if total_changed.get(column) is None:
                    total_changed[column] = 0
                if not entry.get('do_not_count') and column not in ['share_ratio', 'points']:
                    total_details[column] = total_details[column] + getattr(user_details_db, column)
                    if details_changed[column] != '*':
                        total_changed[column] += details_changed[column]

            # update db
            for key, value in details_now.items():
                if key == 'join_date':
                    value = parse(value)
                if value != '*':
                    setattr(user_details_db, key, value)
            session.commit()

        data['site'].append('total')
        for column in columns:
            if column == 'site':
                continue
            data[column].append('{}{}'.format(self.build_data_text(column, total_details[column]),
                                              self.build_data_text(column, total_changed[column], append=True)))
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
        self.draw_user_classes(user_classes_dict, session, df)

    def _get_user_details(self, session: Session, site):
        user_details = session.query(UserDetailsEntry).filter(
            UserDetailsEntry.site == site).one_or_none()
        return user_details

    def convert_suffix(self, details_value: str) -> float | None:
        keys = list(suffix.keys())
        keys.reverse()
        for key in keys:
            if re.search(key, details_value) and (num_match := re.search('[\\d.]+', details_value)):
                return float(num_match.group()) * suffix[key]
        return None

    def build_suffix(self, details_value, specifier: str) -> str | None:
        if details_value == 0:
            return '0'
        for key, value in suffix.items():
            if (num := details_value / value) < 1000:
                return specifier.format(round(num, 3), key)
        return None

    def build_math_suffix(self, details_value, specifier: str) -> str | None:
        for key, value in math_suffix.items():
            if (num := details_value / value) < 1000:
                return specifier.format(round(num, 3), key).rstrip()
        return None

    def build_data_text(self, key: str, value, append=False) -> str | None:
        if key == 'site':
            if len(value) > 12:
                str_list = list(value)
                str_list.insert(12, '\n')
                value = ''.join(str_list)
            return value
        if value == '*':
            return value
        if value == 0 and append:
            return ''
        if key in ['uploaded', 'downloaded']:
            specifier = '\n{:+g} {}iB' if append else '{:g} {}iB'
            return self.build_suffix(value, specifier)
        if key in ['share_ratio', 'points']:
            specifier = '\n{:+g} {}' if append else '{:g} {}'
            return self.build_math_suffix(value, specifier)
        return '\n{:+g}'.format(value) if append else '{:g}'.format(value)

    def transfer_data(self, key: str, value) -> float:
        if value == '*' or key in ['join_date']:
            return value
        if key in ['uploaded', 'downloaded']:
            return float(self.convert_suffix(value))
        return float(value)

    def count(self, count_dict: dict, key, value) -> None:
        if key not in ['share_ratio', 'points']:
            count_dict[key] = count_dict[key] + value

    def draw_user_classes(self, user_classes_dict: dict, session: Session, df: DataFrame) -> None:
        img = Image.open('details_report.png').convert("RGBA")
        tmp = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(tmp)
        start_x = 32
        start_y, cell_height = self.find_start_y(img, start_x)
        cell_width = 342
        start_y = start_y + cell_height
        colors = [(0, 104, 250, 127), (111, 11, 217, 127), (217, 96, 11, 127)]
        font_path = findfont(FontProperties(family=['sans-serif']))
        for i in range(len(df.values)):
            site_name = re.sub('\\*|', '', df.values[i][0].replace('\n', ''))
            mid_y = start_y + i * cell_height
            y, cell_content_height = self.get_cell_position(img, start_x, mid_y)
            if user_classes := user_classes_dict.get(site_name):
                site_details = self._get_user_details(session, site_name)
                if data := self.build_user_classes_data(user_classes, site_details, colors):
                    bar_height = cell_content_height / len(data)
                    j = 0
                    font, height = self.get_perfect_font(bar_height, cell_width, font_path, data.keys())
                    for name, value in data.items():
                        draw.rectangle(((start_x, y + bar_height * j), (
                            start_x + (cell_width * value[0]),
                            y + bar_height * (j + 1) - 2)), fill=value[1])
                        draw.text((start_x, y + bar_height * j + (bar_height - height) / 2), name, font=font,
                                  fill=(158, 158, 158, 127))
                        j += 1
        Image.alpha_composite(img, tmp).convert("RGB").quantize(colors=256).save('details_report.png')

    def build_user_classes_data(self, user_classes: dict, site_details,
                                colors: list[tuple[int, int, int, int]]) -> None:
        data = {}
        if (downloaded_class := user_classes.get('downloaded')) and (
                share_ratio_class := user_classes.get('share_ratio')) and not user_classes.get(
            'uploaded'):
            uploaded = []
            for i in range(len(downloaded_class)):
                uploaded.append(downloaded_class[i] * share_ratio_class[i])
            uploaded_classes = {'uploaded': uploaded}
            uploaded_classes.update(user_classes)
            user_classes = uploaded_classes

        for name, value in user_classes.items():
            db_value = (datetime.now().date() - site_details.join_date).days if name == 'days' else getattr(
                site_details, name, None)
            if db_value is None:
                logger.error(f'get data: {name} error')
                return
            data[name] = self.build_single_data(value, db_value, colors)
        return data

    def set_default_data(self, data, length):
        if not data:
            default_data = []
            for i in range(length):
                default_data.append(0)
            return default_data
        else:
            return data

    def build_single_data(self, value_tuple, value, colors: list[tuple[int, int, int, int]]) -> tuple[
        float, tuple[int, int, int, int]]:
        percent = 1 if (max_value := value_tuple[-1]) == 0 else value / max_value
        if percent > 1:
            percent = 1
        i = 0
        for v in value_tuple:
            if value >= v:
                i += 1
        if len(value_tuple) == 1:
            i = -i
        return percent, colors[i]

    def find_start_y(self, img: Image.Image, start_x: int) -> tuple[float, int]:
        start_y = 0
        pass_black = True
        cell_height = 0
        for i in range(img.size[1]):
            pixel = img.getpixel((start_x, i))
            if not start_y:
                if pixel[0] == 0 and pixel[1] == 0 and pixel[2] == 0:
                    start_y = i
            elif pass_black:
                if pixel[0] != 0 or pixel[1] != 0 or pixel[2] != 0:
                    pass_black = False
            elif pixel[0] == 0 and pixel[1] == 0 and pixel[2] == 0:
                cell_height = i - start_y
                break
        return start_y + (cell_height / 2), cell_height

    def get_cell_position(self, img: Image.Image, start_x, start_y) -> tuple[int, int]:
        y = 0
        to_top = 0
        to_bottom = 0
        for i in range(img.size[1]):
            if start_y - i > 0:
                pixel = img.getpixel((start_x, start_y - i))
                if pixel[0] == 0 and pixel[1] == 0 and pixel[2] == 0:
                    y = start_y - i + 1
                    to_top = i
                    break

        for i in range(img.size[1]):
            if start_y + i < img.size[1]:
                pixel = img.getpixel((start_x, start_y + i))
                if pixel[0] == 0 and pixel[1] == 0 and pixel[2] == 0:
                    to_bottom = i
                    break
        return y, to_top + to_bottom

    def get_perfect_font(self, bar_height: float, cell_width: int, font_path: str, keys) -> tuple[
        FreeTypeFont, int]:
        font_size = float('inf')
        font_height = 0
        for key in keys:
            calc_font_size, calc_height = self.calc_font(bar_height, cell_width, font_path, key, font_size)
            if font_size > calc_font_size:
                font_size = calc_font_size
                font_height = calc_height
        return ImageFont.truetype(font_path, font_size), font_height

    def calc_font(self, bar_height: float, cell_width: int, font_path: str, test_str, font_size_start) -> tuple:
        if font_size_start == float('inf'):
            font_size_start = 1
        perfect_height = bar_height - 4
        font_size = font_size_start
        font_tmp = ImageFont.truetype(font_path, font_size)
        _, _, width, height = font_tmp.getbbox(test_str)
        if height > perfect_height or width > cell_width - 20:
            while height > perfect_height or width > cell_width - 20:
                font_size += -1
                font_tmp = ImageFont.truetype(font_path, font_size)
                _, _, width, height = font_tmp.getbbox(test_str)
        else:
            while height < perfect_height and width < cell_width - 20:
                font_size += 1
                font_tmp = ImageFont.truetype(font_path, font_size)
                _, _, width, height = font_tmp.getbbox(test_str)
        font_size = font_size if font_size > 0 else 1
        return font_size, height
