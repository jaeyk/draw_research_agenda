import unittest
from tools import agenda_to_mermaid as atm


class TestAgendaParsing(unittest.TestCase):
    def test_parse_tagged(self):
        txt = "[theme]T[/theme] [component time=past]A[/component] [component time=current]B[/component] [subcomponent of=B]C[/subcomponent] [relation:enables]A->B[/relation:enables]"
        model = atm.parse(txt)
        self.assertEqual(model['theme'], 'T')
        names = [c['name'] for c in model['components']]
        self.assertIn('A', names)
        self.assertIn('B', names)
        self.assertIn('C', names)
        self.assertTrue(any(r['type']=='enables' for r in model['relations']))

    def test_mermaid_output(self):
        txt = "[theme]Root[/theme] [component time=current]X[/component]"
        model = atm.parse(txt)
        m = atm.to_mermaid(model, orientation='vertical')
        self.assertIn('graph TD', m)
        self.assertIn('Root', m)
        self.assertIn('X', m)
        m2 = atm.to_mermaid(model, orientation='horizontal')
        self.assertIn('graph LR', m2)

    def test_dot_output(self):
        txt = "[theme]Root[/theme] [component time=future]Y[/component]"
        model = atm.parse(txt)
        d = atm.to_dot(model)
        self.assertIn('subgraph', d) or self.assertIn('cluster_Future'.lower(), d.lower())
        self.assertIn('Root', d)
        self.assertIn('Y', d)


if __name__ == '__main__':
    unittest.main()
