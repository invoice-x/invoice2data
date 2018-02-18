"""
Interface for extraction plugins.

Each plugin is a module (file) in package `plugins` that provides at a minimum the `extract`
function with those arguments:

def extract(settings, optimized_str, output)
"""