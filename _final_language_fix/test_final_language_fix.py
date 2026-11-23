import ast,importlib.util,shutil,tempfile,unittest
from pathlib import Path
import APPLY_FINAL_LANGUAGE_FIX as fix

class FinalLanguageTests(unittest.TestCase):
    def test_wording(self):
        ns={};exec(fix.DISPLAY,ns)
        self.assertEqual(ns['decision_task']('Imagine in the scenario below.'),'Imagine in the scenario above.')
        t=ns['study_task']('Assess using this reference table and these study objectives: Runtime + Energy.')
        self.assertIn('shown after the explanation',t);self.assertTrue(t.endswith('Runtime + Energy.'))
    def test_form_placement(self):
        source='''def run():
    if initial is None:
        section("Initial evaluation", __import__("awareml.studies.task_context_revision",fromlist=["TRUST_INSTRUCTION"]).TRUST_INSTRUCTION)
        with st.form("p16v3_initial_{}".format(order)):
            a = _likert("I am confident in the AI assistant.")
            b = _likert("The AI assistant is reliable.")
            c = _likert("I can trust the AI assistant.")
            pc = _likert("How likely is the explanation to be factually correct?")
'''
        out=fix.patch(fix.TARGETS[2],source);tree=ast.parse(out)
        form=next(x for x in ast.walk(tree) if isinstance(x,ast.With))
        self.assertEqual(ast.dump(form.body[0]),ast.dump(ast.parse('st.write(ASSISTANT_INSTRUCTION)').body[0]))
        self.assertEqual(ast.dump(form.body[4]),ast.dump(ast.parse('st.write(EXPLANATION_INSTRUCTION)').body[0]))
        self.assertEqual(fix.patch(fix.TARGETS[2],out),out)
    def test_unknown_source_rejected(self):
        with self.assertRaises(ValueError):fix.patch(fix.TARGETS[0],'# different source')
    def test_table_preserved(self):
        source="def card():\n    st.write(trial.get('prompt'))\n    st.dataframe(frame, hide_index=True)\n"
        out=fix.patch(fix.TARGETS[1],source)
        self.assertIn('st.dataframe(frame, hide_index=True)',out)
        self.assertEqual(fix.patch(fix.TARGETS[1],out),out)

if __name__=='__main__':unittest.main(verbosity=2)
