import unittest

import base

from solar.core import resource
from solar.core import signals


class TestResource(base.BaseResourceTest):
    def test_resource_args(self):
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  value:
    schema: int
    value: 0
        """)

        sample1 = self.create_resource(
            'sample1', sample_meta_dir, {'value': 1}
        )
        self.assertEqual(sample1.args['value'].value, 1)

        # test default value
        sample2 = self.create_resource('sample2', sample_meta_dir, {})
        self.assertEqual(sample2.args['value'].value, 0)

    def test_connections_recreated_after_load(self):
        """
        Create resource in some process. Then in other process load it.
        All connections should remain the same.
        """
        sample_meta_dir = self.make_resource_meta("""
id: sample
handler: ansible
version: 1.0.0
input:
  value:
    schema: int
    value: 0
        """)

        def creating_process():
            sample1 = self.create_resource(
                'sample1', sample_meta_dir, {'value': 1}
            )
            sample2 = self.create_resource(
                'sample2', sample_meta_dir, {}
            )
            signals.connect(sample1, sample2)
            self.assertEqual(sample1.args['value'], sample2.args['value'])

        creating_process()

        signals.CLIENTS = {}

        sample1 = resource.load('sample1')
        sample2 = resource.load('sample2')

        sample1.update({'value': 2})
        self.assertEqual(sample1.args['value'], sample2.args['value'])


if __name__ == '__main__':
    unittest.main()
