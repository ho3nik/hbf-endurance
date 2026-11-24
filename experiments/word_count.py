"""IEEE Micro word count: text (abstract, body, bio) + references + 250 words per average-size float.
Full-width floats (figure*/table*) are counted at 375 words to stay on the safe side."""
import re, sys, os
P = os.path.join(os.path.dirname(__file__), "..", "paper")
s = open(os.path.join(P, "main.tex")).read()
mac = dict(re.findall(r'\\newcommand\{\\([A-Za-z]+)\}\{([^}]*)\}', open(os.path.join(P, "numbers.tex")).read()))
body = s[s.index("\\begin{abstract}"):s.index("\\end{document}")]
floats = re.findall(r'\\begin\{(table\*?|figure\*?)\}', body)
body = re.sub(r'\\begin\{(table\*?|figure\*?)\}.*?\\end\{\1\}', ' ', body, flags=re.S)
body = re.sub(r'\\bibliographystyle\{[^}]*\}|\\bibliography\{[^}]*\}', ' ', body)
body = re.sub(r'\\([A-Za-z]+)\{\}', lambda m: mac.get(m.group(1), ' '), body)
body = re.sub(r'\\cite\{[^}]*\}|\\ref\{[^}]*\}|\\label\{[^}]*\}|\\eqref\{[^}]*\}', ' ', body)
body = re.sub(r'\\begin\{equation\}.*?\\end\{equation\}', ' EQ ', body, flags=re.S)
body = re.sub(r'\\[A-Za-z]+\*?', ' ', body)
text = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'.,%\-]*", body))
bbl = open(os.path.join(P, "main.bbl")).read()
bbl = re.sub(r'\\[A-Za-z]+\*?|\{|\}|~', ' ', bbl)
refs = len(re.findall(r"[A-Za-z0-9][^\s]*", bbl))
nfl = sum(375 if f.endswith("*") else 250 for f in floats)
ab = s[s.index("\\begin{abstract}") + 16:s.index("\\end{abstract}")]
ab = re.sub(r'\\([A-Za-z]+)\{\}', lambda m: mac.get(m.group(1), ' '), ab)
ab = re.sub(r'\\[A-Za-z]+', ' ', ab)
print(f"text {text}, references {refs} ({open(os.path.join(P, 'main.bbl')).read().count(chr(92) + 'bibitem')} items), floats {len(floats)} -> {nfl}; total {text + refs + nfl} of 6000; abstract {len(ab.split())} of 150")
