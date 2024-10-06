# -*- coding: utf-8 -*-

import uuid
from typing import Dict


def convert_ios_hierarchy(data: Dict, scale: int) -> Dict:

    def __travel(node):
        node['_id'] = str(uuid.uuid4())
        node['_type'] = node.pop('type', "null")
        node['id'] = node.pop('rawIdentifier', "null")
        if 'rect' in node:
            rect = node['rect']
            node['rect'] = {k: v * scale for k, v in rect.items()}

        # Recursively process children nodes
        if 'children' in node:
            node['children'] = [__travel(child) for child in node['children']]

        # Sort the keys
        keys_order = ['_type', 'label', 'name', 'id', 'value']
        sorted_node = {k: node[k] for k in keys_order if k in node}
        sorted_node.update({k: node[k] for k in node if k not in keys_order})

        return sorted_node

    return __travel(data)