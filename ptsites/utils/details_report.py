from __future__ import annotations

import re
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from numbers import Real
from dateutil.parser import parse
from flexget import db_schema
from flexget.manager import Session
from flexget.task import Task
from loguru import logger
from sqlalchemy import Column, String, Integer, Float, Date

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
    report_width = 2400
    margin = 32
    title_height = 96
    header_height = 84
    row_height = 132
    column_widths = (0.15, 0.16, 0.16, 0.13, 0.14, 0.10, 0.10, 0.06)

    colors = {
        'canvas': '#F4F7F9',
        'header': '#263238',
        'header_text': '#FFFFFF',
        'grid': '#B0BEC5',
        'outer_grid': '#78909C',
        'text': '#263238',
        'muted_text': '#607D8B',
        'positive_text': '#00796B',
        'negative_text': '#C62828',
        'normal': '#FFFFFF',
        'alternate': '#FAFBFC',
        'positive': '#D7F2EC',
        'negative': '#FFD9DC',
        'warning': '#FFF7B2',
        'total': '#E3EDF3',
        'site_badge': (255, 255, 255, 224),
    }

    def build(self, task: Task) -> None:
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
        order = sorted(
            range(len(data['site'])),
            key=lambda index: (data['sort_column'][index], data['default_order'][index]),
            reverse=True
        )
        rows = [[data[column][index] for column in columns] for index in order]
        self.draw_report(columns, rows, user_classes_dict, session)

    def _get_user_details(self, session: Session, site):
        user_details = session.query(UserDetailsEntry).filter(
            UserDetailsEntry.site == site).one_or_none()
        return user_details

    def convert_suffix(self, details_value: str | Real, suffix: dict) -> float | None:
        if isinstance(details_value, Real):
            return float(details_value)
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
        if isinstance(value, Real):
            return float(value)
        elif key in ['uploaded', 'downloaded']:
            return float(self.convert_suffix(value, suffix))
        elif key in ['points']:
            return float(self.convert_suffix(value, math_suffix))
        else:
            return float(value)

    def count(self, count_dict: dict, key, value) -> None:
        if key not in ['share_ratio', 'points']:
            count_dict[key] = count_dict[key] + value

    def draw_report(self, columns: list[str], rows: list[list[str]], user_classes_dict: dict,
                    session: Session) -> None:
        report_height = self.title_height + self.header_height + self.row_height * len(rows) + self.margin
        image = Image.new('RGB', (self.report_width, report_height), self.colors['canvas'])
        draw = ImageDraw.Draw(image, 'RGBA')

        title = f'PT Sign-in Report  |  {datetime.now().replace(microsecond=0)}'
        title_font = self._load_font(38, bold=True)
        self._draw_centered(draw, (self.margin, 0, self.report_width - self.margin, self.title_height), title,
                            title_font, self.colors['text'])

        table_width = self.report_width - self.margin * 2
        widths = [round(table_width * width) for width in self.column_widths]
        widths[-1] += table_width - sum(widths)
        positions = [self.margin]
        for width in widths:
            positions.append(positions[-1] + width)

        header_top = self.title_height
        header_bottom = header_top + self.header_height
        header_font = self._load_font(29, bold=True)
        for index, column in enumerate(columns):
            box = (positions[index], header_top, positions[index + 1], header_bottom)
            draw.rectangle(box, fill=self.colors['header'])
            self._draw_centered(draw, box, column.replace('_', ' '), header_font, self.colors['header_text'])

        class_colors = [(38, 132, 255, 105), (126, 72, 214, 105), (239, 127, 26, 105)]
        for row_index, row in enumerate(rows):
            top = header_bottom + row_index * self.row_height
            bottom = top + self.row_height
            site_name = row[0].replace('\n', '').replace('*', '')
            is_total = site_name == 'total'
            user_class_data = None
            if user_classes := user_classes_dict.get(site_name):
                site_details = self._get_user_details(session, site_name)
                user_class_data = self.build_user_classes_data(user_classes, site_details, class_colors)

            for column_index, value in enumerate(row):
                box = (positions[column_index], top, positions[column_index + 1], bottom)
                fill = self._cell_color(value, row_index, is_total)
                draw.rectangle(box, fill=fill)
                if column_index == 0 and user_class_data:
                    self._draw_user_class_cell(draw, box, value, user_class_data)
                else:
                    self._draw_cell_text(draw, box, value, is_site=column_index == 0,
                                         bold=is_total or column_index == 0)

            draw.line((self.margin, bottom, self.report_width - self.margin, bottom),
                      fill=self.colors['grid'], width=2)

        table_bottom = header_bottom + len(rows) * self.row_height
        for position in positions:
            draw.line((position, header_top, position, table_bottom), fill=self.colors['grid'], width=2)
        draw.rectangle((self.margin, header_top, self.report_width - self.margin, table_bottom),
                       outline=self.colors['outer_grid'], width=3)
        draw.line((self.margin, header_bottom, self.report_width - self.margin, header_bottom),
                  fill=self.colors['outer_grid'], width=3)

        image.save('details_report.png', optimize=True)

    def _cell_color(self, value: str, row_index: int, is_total: bool) -> str:
        if '\n-' in value:
            return self.colors['negative']
        if '+' in value:
            return self.colors['positive']
        if '*' in value:
            return self.colors['warning']
        if is_total:
            return self.colors['total']
        return self.colors['alternate'] if row_index % 2 else self.colors['normal']

    def _draw_cell_text(self, draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], value: str,
                        is_site: bool = False, bold: bool = False) -> None:
        value = str(value)
        if is_site or '\n' not in value:
            font = self._fit_font(draw, value, box[2] - box[0] - 20, box[3] - box[1] - 16, 31, bold)
            color = '#8A6D00' if '*' in value else self.colors['text']
            self._draw_centered(draw, box, value, font, color)
            return

        main, delta = value.split('\n', 1)
        main_font = self._fit_font(draw, main, box[2] - box[0] - 18, 48, 31, bold)
        delta_font = self._fit_font(draw, delta, box[2] - box[0] - 18, 42, 27, True)
        main_size = self._text_size(draw, main, main_font)
        delta_size = self._text_size(draw, delta, delta_font)
        gap = 5
        content_height = main_size[1] + delta_size[1] + gap
        y = box[1] + (box[3] - box[1] - content_height) / 2
        self._draw_centered(draw, (box[0], int(y), box[2], int(y + main_size[1])), main, main_font,
                            self.colors['text'])
        delta_color = self.colors['negative_text'] if delta.startswith('-') else self.colors['positive_text']
        self._draw_centered(draw, (box[0], int(y + main_size[1] + gap), box[2], box[3]), delta, delta_font,
                            delta_color)

    def _draw_user_class_cell(self, draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], value: str,
                              user_class_data: dict) -> None:
        band_height = (box[3] - box[1]) / len(user_class_data)
        label_font = self._load_font(20, bold=True)
        for index, (name, (percent, color)) in enumerate(user_class_data.items()):
            top = box[1] + band_height * index
            bottom = box[1] + band_height * (index + 1)
            progress_right = box[0] + (box[2] - box[0]) * percent
            if progress_right > box[0]:
                draw.rectangle((box[0], top, progress_right, bottom - 1), fill=color)
            label = name.replace('_', ' ')
            label_box = (box[0] + 8, int(top), box[2] - 8, int(bottom))
            self._draw_left_centered(draw, label_box, label, label_font, (69, 90, 100, 175))

        site_text = value.replace('\n', '')
        site_font = self._fit_font(draw, site_text, box[2] - box[0] - 24, box[3] - box[1] - 24, 30, True)
        text_width, text_height = self._text_size(draw, site_text, site_font)
        badge_left = max(box[0] + 8, box[2] - text_width - 28)
        badge_top = box[1] + (box[3] - box[1] - text_height - 16) / 2
        badge_box = (int(badge_left), int(badge_top), box[2] - 8, int(badge_top + text_height + 16))
        draw.rounded_rectangle(badge_box, radius=10, fill=self.colors['site_badge'],
                               outline=(96, 125, 139, 110), width=2)
        self._draw_centered(draw, badge_box, site_text, site_font, self.colors['text'])

    def _draw_centered(self, draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str,
                       font, fill) -> None:
        width, height = self._text_size(draw, text, font)
        x = box[0] + (box[2] - box[0] - width) / 2
        y = box[1] + (box[3] - box[1] - height) / 2
        bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=4, align='center')
        draw.multiline_text((x - bbox[0], y - bbox[1]), text, font=font, fill=fill, spacing=4, align='center')

    def _draw_left_centered(self, draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str,
                            font, fill) -> None:
        _, height = self._text_size(draw, text, font)
        bbox = draw.textbbox((0, 0), text, font=font)
        y = box[1] + (box[3] - box[1] - height) / 2
        draw.text((box[0] - bbox[0], y - bbox[1]), text, font=font, fill=fill)

    def _fit_font(self, draw: ImageDraw.ImageDraw, text: str, max_width: int, max_height: int,
                  start_size: int, bold: bool = False):
        for size in range(start_size, 15, -1):
            font = self._load_font(size, bold)
            width, height = self._text_size(draw, text, font)
            if width <= max_width and height <= max_height:
                return font
        return self._load_font(16, bold)

    def _load_font(self, size: int, bold: bool = False):
        cache = getattr(self, '_font_cache', {})
        key = (size, bold)
        if key in cache:
            return cache[key]

        regular_fonts = (
            'DejaVuSans.ttf',
            'Arial.ttf',
            r'C:\Windows\Fonts\segoeui.ttf',
            r'C:\Windows\Fonts\arial.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
            '/usr/share/fonts/TTF/DejaVuSans.ttf',
        )
        bold_fonts = (
            'DejaVuSans-Bold.ttf',
            'Arial Bold.ttf',
            r'C:\Windows\Fonts\segoeuib.ttf',
            r'C:\Windows\Fonts\arialbd.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf',
            '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
        )
        for font_name in bold_fonts if bold else regular_fonts:
            try:
                font = ImageFont.truetype(font_name, size)
                cache[key] = font
                self._font_cache = cache
                return font
            except OSError:
                continue
        try:
            font = ImageFont.load_default(size=size)
        except TypeError:
            font = ImageFont.load_default()
        cache[key] = font
        self._font_cache = cache
        return font

    @staticmethod
    def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
        bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=4, align='center')
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

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
