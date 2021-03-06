import inflection
import os
import pprint

from solar.core import resource
from solar import utils


RESOURCE_HEADER_TEMPLATE = """
from solar.core.resource import Resource
"""


RESOURCE_CLASS_TEMPLATE = """


class {class_name}(Resource):
    _metadata = {{
        'actions': {meta_actions},
        'actions_path': '{actions_path}',
        'base_path': '{base_path}',
        'input': {meta_input},
        'handler': '{handler}',
    }}

    {input_properties}
"""


RESOURCE_INPUT_PROPERTY_TEMPLATE = """
    @property
    def {name}(self):
        return self.args['{name}']

    @{name}.setter
    def {name}(self, value):
        #self.args['{name}'].value = value
        #self.set_args_from_dict({{'{name}': value}})
        self.update({{'{name}': value}})
"""


def compile(meta):
    destination_file = utils.read_config()['resources-compiled-file']

    resource.prepare_meta(meta)
    meta['class_name'] = '{}Resource'.format(
        inflection.camelize(meta['base_name'])
    )
    meta['meta_actions'] = pprint.pformat(meta['actions'])
    meta['meta_input'] = pprint.pformat(meta['input'])

    print meta['base_name'], meta['class_name']

    if not os.path.exists(destination_file):
        with open(destination_file, 'w') as f:
            f.write(RESOURCE_HEADER_TEMPLATE.format(**meta))

    with open(destination_file, 'a') as f:
        input_properties = '\n'.join(
            RESOURCE_INPUT_PROPERTY_TEMPLATE.format(name=name)
            for name in meta['input']
        )
        f.write(RESOURCE_CLASS_TEMPLATE.format(
            input_properties=input_properties, **meta)
        )
