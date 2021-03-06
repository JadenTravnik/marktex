import re
import os

def convert_table(match):
    text = match.group(1)
    # Remove starting |
    text = re.sub(r'(^|\n)\|\s*', r'\1', text)
    # Remove trailing | and replace with \\
    text = re.sub(r'\s*\|(\n|$)', r' \\\\\1', text)
    # Use remaining |'s to align values.
    text = re.sub('\s*\|\s*', ' & ', text)
    lines = text.split('\n')
    headers, alignment, *content = lines
    # Center alignment.
    alignment = re.sub(':-+: ', 'c', alignment)
    # Right alignment.
    alignment = re.sub(':-+ ', 'r', alignment)
    # Left alignment.
    alignment = re.sub('-+:? ', 'l', alignment)
    # Remove everything that was left in the alignment string.
    alignment = re.sub('[^lcr ]', '', alignment)
    # Put everything together, remembering to escape curly braces because they
    # are used in Python's format.
    return """
\\begin{{table}}
\\begin{{tabular}}{{{1}}}
\\toprule
{0}
\\midrule
{2}
\\bottomrule
\\end{{tabular}}
\\end{{table}}
""".format(headers, alignment, '\n'.join(content))

languages = """
cucumber 	abap 	ada 	ahk
antlr 	apacheconf 	applescript 	as
aspectj 	autoit 	asy 	awk
basemake 	bash 	bat 	bbcode
befunge 	bmax 	boo 	brainfuck
bro 	bugs 	c 	ceylon
cfm 	cfs 	cheetah 	clj
cmake 	cobol 	cl 	console
control 	coq 	cpp 	croc
csharp 	css 	cuda 	cyx
d 	dg 	diff 	django
dpatch 	duel 	dylan 	ec
erb 	evoque 	fan 	fancy
fortran 	gas 	genshi 	glsl
gnuplot 	go 	gosu 	groovy
gst 	haml 	haskell 	hxml
html 	http 	hx 	idl
irc 	ini 	java 	jade
js 	json 	jsp 	kconfig
koka 	lasso 	livescrit 	llvm
logos 	lua 	mako 	mason
matlab 	minid 	monkey 	moon
mxml 	myghty 	mysql 	nasm
newlisp 	newspeak 	numpy 	ocaml
octave 	ooc 	perl 	php
plpgsql 	postgresql 	postscript 	pot
prolog 	psql 	puppet 	python
qml 	ragel 	raw 	ruby
rhtml 	sass 	scheme 	smalltalk
sql 	ssp 	tcl 	tea
tex 	text 	vala 	vgl
vim 	xml 	xquery 	yaml 
"""

def include_source(match):
    language = match.group(2)
    if language not in languages:
        language = 'latex'
    path = os.path.abspath(match.group(1)).replace('\\', '/')
    return r'\inputminted[fontsize=\small]{{{}}}{{{}}}'.format(language, path)

def include_image(match):
    path = os.path.abspath(match.groups()[-1]).replace('\\', '/')
    if len(match.groups()) == 1:
        return r"""
\begin{{center}}
\includegraphics[width=\linewidth,height=0.8\textheight,keepaspectratio]{{{}}}
\end{{center}}
""".format(path)
    else:
        return r"""
\begin{{figure}}
\begin{{center}}
\includegraphics[width=\linewidth,height=0.7\textheight,keepaspectratio]{{{}}}
\caption{{{}}}
\end{{center}}
\end{{figure}}
""".format(path, match.group(1))

def include_latex(match):
    path = os.path.abspath(match.groups()[-1]).replace('\\', '/')
    return r'\input{' + path + '}'


math_rules = [
    ['*', '\\cdot'],
    ['~~', '\\approx'],
    ['~=', '\\congr'],
    ['==', '\\equiv'],
    ['!=', '\\neq'],
    ['!<=', '\\nleq'],
    ['!>=', '\\ngeq'],
    ['<=', '\\leq'],
    ['>=', '\\qeg'],
    ['+-', '\\pm'],

    [' <-> ', '\\leftrightarrow'],
    [' <=> ', '\\Leftrightarrow'],
    [' |-> ', '\\mapsto'],
    [' <- ', '\\leftarrow'],
    [' <= ', '\\Leftarrow'],
    [' -> ', '\\rightarrow'],
    [' => ', '\\Rightarrow'],

    [' in ', ' \\in '],
    [' mod ', ' \\mod '],

    ['(', '\\left('],
    [')', '\\right)'],
    ['[', '\\left['],
    [']', '\\right]'],

    #['/', '\\div'],
    #['*', '\\times'],
]

def include_math(match):
    text = match.group(1)
    multiline = '\n' in text
    text = text.strip()
    # Group numbers to avoid problems with x^123 .
    text = re.sub(r'(-?\d+)', r'{\1}', text)
    for rule, replacement in math_rules:
        text = text.replace(rule, ' {} '.format(replacement))
    text = re.sub(r'(^|[^a-zA-Z])(log|sin|cos|tan|lim|gcd|ln)([^a-zA-Z]|$)', r'\1\\\2\3', text)
    text = re.sub(r'(^|[^a-zA-Z])(inf)([^a-zA-Z]|$)', r'\1\infty\3', text)
    if multiline:
        text = re.sub(r'\n+', r'\\\\''\n', text).strip('\n')
        if '&' in text:
            text = '\\begin{aligned}\n' + text + '\n\\end{aligned}'
        return '\\begin{gather*}\n' + text + '\n\\end{gather*}'
    else:
        return '$' + text + '$'


rules = [
        # Latex hates unescaped characters.
        (r'([$#%])', r'\\\1'),

        # Replace single linebreaks with double linebreaks.
        (r'([^\n])\n([^\n])', r'\1\n\n\2'),

        # Annotations using {text}(annotation) syntax.
        # Hackish because we enter math mode needlessly, but I found no other
        # way.
        (r'\{([^\n]+?)\}\(([^\n]+?)\)', r'$\\underbrace{\\text{\1}}_{\\text{\2}}$'),

        # Two dollars start math mode.
        (r'\\\$\\\$([^$]+?)\\\$\\\$', include_math),


        # Tables as such:
        #
        # | Header 1 | Header 2 | Header 3 |
        # |---------:|:--------:|:---------|
        # | Value    |   Value  |    Value |
        # | Value    |   Value  |    Value |
        # | Value    |   Value  |    Value |
        (r'(?<=\n\n)((?:^\|.+?\|\n)+)', convert_table),

        # Simple images using !(image.jpg) syntax.
        (r'^!\(([^)]+?\.(?:jpg|jpeg|gif|png|bmp|pdf|tif))\)$', include_image),

        # Latex embedding with !(text.tex) syntax.
        (r'^!\(([^)]+?\.tex)\)$', include_latex),

        # Code embedding with !(code.py) syntax.
        (r'^!\(([^)]+?\.(\w+))\)$', include_source),

        # Captioned images using ![caption](image.jpg) syntax.
        (r'^!\[([^\]]+?)\]\(([^)]+?)\)$', include_image),
        
        # [Text links](example.org)
        (r'(?<=\W)\[([^\]]*)\]\(([^)]+?)\)(?=\W)', r'\\href{\2}{\\underline{\1}}'),

        # Add \item to each bullet point.
        (r'^- ?([^-][^\n]*)$', r'\item \1'),

        # Begin and end itemize for bullet points.
        (r'((?:^\\item [^\n]+$(?:\\pause|\n)*){2,})',
r"""
\\begin{itemize}
\1
\\end{itemize}
"""),

        # **bold**
        (r'(^|\W)\*\*(.+?)\*\*([^\w\d*]|$)', r'\1\\textbf{\2}\3'),

        # *italics*
        #(r'(^|\s)\*([^\n]+?)\*([^\w\d*]|$)', r'\1\\textit{\2}\3'),
]


def translate(extra_rules, src, header, footer):
    # To avoid processing what should be verbatim (`` and two-spaces indented)
    # we remove all verbatim code, replacing with a unique value, and reinsert
    # after all rules are done.
    from uuid import uuid4
    verbatim_replacement = str(uuid4())
    verbatims = []

    def remove_verbatim(match):
        print(match.group(1))
        n = len(verbatims)
        verbatims.append(match.group(1))
        return verbatim_replacement + str(n) + '!'
    src = re.sub(r'((?:^[ \t]{2}.*\n)+|`.*?[^\\]`)', remove_verbatim, src, flags=re.MULTILINE)

    for rule, replacement in extra_rules + rules:
        src = re.sub(rule, replacement, src, flags=re.MULTILINE | re.DOTALL)

    def reinsert_verbatim(match):
        v = verbatims[int(match.group(1))]
        v = v.replace('{', r'\{')
        v = v.replace('}', r'\}')
        if '\n' in v:
            return r"""\begin{{minted}}[fontsize=\small]{{latex}}
{}
\end{{minted}}""".format(verbatims.pop())
        else:
            return '\\texttt{{\\lstinline{{{}}}}}'.format(v.strip('`'))
    src = re.sub(verbatim_replacement + r'(\d+)!', reinsert_verbatim, src)

    return header + src + footer
