"""
Interface for extraction plugins.

Plugins are used for extracting more complex data and should be used
only if they can't fit parsers design. They can't be used in the
standard `fields` associative array.

The main advantage of plugins (as the cost of clean template
integration) is full access to the output. It allows plugins to e.g.
set multiple output entires.

Each plugin is a module (file) in package `plugins` that provides at a minimum the `extract`
function with those arguments:

def extract(settings, optimized_str, output)
"""
