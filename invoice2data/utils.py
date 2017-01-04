"""
Keep helper functions not related to specific module.
"""

import yaml
from collections import OrderedDict

# borrowed from http://stackoverflow.com/a/21912744
def ordered_load(
        stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict
):
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)

    return yaml.load(stream, OrderedLoader)
