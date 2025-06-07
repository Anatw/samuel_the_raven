import re

# List of words to recognize
NAMES = {"Alma", "Anat", "Chaya", "Gopal", "Samuel", "Zighy"}
WORDS = {"Gvina", "Hatula", "Keter", "Hey"}


# Consolidated regex patterns for name corrections
NAME_CORRECTIONS_REGEX = {
    r"\balma\b": "Alma",
    r"\bhomer\b": "Alma",
    r"\b(annette|alert|anna it|and annette)\b": "Anat",
    r"\b.*net.*\b": "Anat",
    r"\b(higher|fire)\b": "Chaya",
    r"\bgopal\b": "Gopal",
    r"\b(go pow|go pal|go pull|go pop|go pearl|go po.*)\b": "Gopal",
    r"\b(ziggy|siggy)\b": "Zighy",
    r"\b(for tuna|kettle|get there|get ill)\b": "Keter",
    r"\b(sam|sam will|samuel|someone|somewhere)\b": "Samuel",
    r"\bhey\b": "Hey",
    r"\b(had to l|to allow|dollar|hat to la)\b": "Hatula",
    r"\b(greener|green)\b": "Gvina",
    r"\b^give.*\b": "Gvina",
    r"\bs\w*\W*well\b": "Samuel",
}

KNOWN_PHRASES = {"Hey Samuel"}

# def correct_name(word):
#     for pattern, correction in NAME_CORRECTIONS_REGEX.items():
#         if re.search(pattern, word, re.IGNORECASE):
#             return correction
#     return word  # Return the original word if no match is found