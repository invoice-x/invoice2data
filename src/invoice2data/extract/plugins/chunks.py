"""
Plugin to extract chunks of lines from an invoice.

Worked on by Sam Slater
"""

import re
import logging as logger

DEFAULT_OPTIONS = {'field_separator': r'\s+', 'line_separator': r'\n'}


def extract(self, content, output):
    """Try to extract Chunk from the invoice"""
    chunks = []
    for chunk in self['chunks']:
        # First apply default options.
        plugin_settings = DEFAULT_OPTIONS.copy()
        plugin_settings.update(chunk)
        chunk = plugin_settings

        # Validate settings
        assert 'chunk' in chunk, 'Chunk regex missing'

        start = re.search(chunk['start'], content) if 'start' in chunk.keys() else None
        end = re.search(chunk['end'], content) if 'end' in chunk.keys() else None

        content_section = content
        # refine content section if start and end have been declared.
        if start and end:
            content_section = content[start.end(): end.start()]
        looping = True
        if 'chunk_start' in chunk and 'chunk_end' in chunk:
            chunk_start = re.search(chunk['chunk_start'], content_section)
            chunk_end = re.search(chunk['chunk_end'], content_section)
            if chunk_start is None or chunk_end is None:
                logger.debug("Chunk start and end cannot be found")
                looping = False
            while looping:
                filtered_chunk = content_section[chunk_start.end(): chunk_end.start()]
                logger.debug("Line content is - " + filtered_chunk)
                found_content = re.search(chunk['chunk'], filtered_chunk)
                # if content has been found add it to the output otherwise stop the loop
                if found_content:
                    content = {
                        field: value.strip() if value else ''
                        for field, value in found_content.groupdict().items()
                    }
                    chunks.append(content)
                    content_section = content_section[chunk_end.end():len(content_section) - 1]
                    # stop the loop if 'repeat' is not specified or not equal to True
                    if "False" == chunk.get('repeat', "False"):
                        looping = False
                else:
                    looping = False
        types = chunk.get('types', [])
        for row in chunks:
            for name in row.keys():
                if name in types:
                    row[name] = self.coerce_type(row[name], types[name])
        if chunks:
            output['chunks'] = chunks
