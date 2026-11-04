"""Final display wording; reviewed scientific stimulus identities remain unchanged."""
PATCH_VERSION = "morten_final_language_20261102"
ASSISTANT_INSTRUCTION = ("For the next three statements, rate the AI assistant as presented in this trial: "
    "its recommendation and supporting explanation, considered with the scenario, study task and reference table. "
    "These are judgments of the assistant, not explanation-only ratings.")
EXPLANATION_INSTRUCTION = ("The following questions concern only the explanation text: "
    "its factual correctness, fluency and how confident it sounds.")

def decision_task(text):
    return text.replace("in the scenario below", "in the scenario above")

def study_task(text):
    return text.replace("using this reference table and these study objectives:",
        "using the table under Study reference evidence, shown after the explanation, "
        "and these study objectives:")
