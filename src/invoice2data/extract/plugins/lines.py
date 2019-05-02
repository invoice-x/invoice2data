"""
Plugin to extract individual lines from an invoice.

Initial work and maintenance by Holger Brunn @hbrunn
"""

import re
import logging as logger

DEFAULT_OPTIONS = {'field_separator': r'\s+', 'line_separator': r'\n'}


def extract(self, content, output):
    """Try to extract lines from the invoice"""
    lines = []
    for line in self['lines']:
        # First apply default options.
        plugin_settings = DEFAULT_OPTIONS.copy()
        plugin_settings.update(line)
        line = plugin_settings

        # Validate settings
        assert 'start' in line, 'Lines start regex missing'
        assert 'end' in line, 'Lines end regex missing'
        assert 'line' in line, 'Line regex missing'

        start = re.search(line['start'], content)
        end = re.search(line['end'], content)
        if not start or not end:
            logger.warning('no lines found - start %s, end %s', start, end)
            return
        content_section = content[start.end(): end.start()]
        current_row = {}
        if 'first_line' not in line and 'last_line' not in line:
            line['first_line'] = line['line']
        for line_content in re.split(line['line_separator'], content_section):
            # if the line has empty lines in it , skip them
            if not line_content.strip('').strip('\n') or not line_content:
                continue
            if 'first_line' in line:
                match = re.search(line['first_line'], line_content)
                if match:
                    if 'last_line' not in line:
                        if current_row:
                            lines.append(current_row)
                        current_row = {}
                    if current_row:
                        lines.append(current_row)
                    current_row = {
                        field: value.strip() if value else ''
                        for field, value in match.groupdict().items()
                    }
                    continue
            if 'last_line' in line:
                match = re.search(line['last_line'], line_content)
                if match:
                    for field, value in match.groupdict().items():
                        current_row[field] = '%s%s%s' % (
                            current_row.get(field, ''),
                            current_row.get(field, '') and '\n' or '',
                            value.strip() if value else '',
                        )
                    if current_row:
                        lines.append(current_row)
                    current_row = {}
                    continue
            match = re.search(line['line'], line_content)
            if match:
                for field, value in match.groupdict().items():
                    current_row[field] = '%s%s%s' % (
                        current_row.get(field, ''),
                        current_row.get(field, '') and '\n' or '',
                        value.strip() if value else '',
                    )
                continue
            logger.debug('ignoring *%s* because it doesn\'t match anything', line_content)
        if current_row:
            lines.append(current_row)

        types = line.get('types', [])
        for row in lines:
            for name in row.keys():
                if name in types:
                    row[name] = self.coerce_type(row[name], types[name])

        if lines:
            output['lines'] = lines
