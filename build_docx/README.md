# LaTeX -> Word

`tex2docx.py` rebuilds `paper/Paper.docx` from `paper/main.tex` so the Word file
is a fully editable copy of `paper/main.pdf`: same two-column IEEE geometry,
same eight pages, references alone on page 8, and all ten floats on the same
page and column as the PDF.

    LEAD=$(cat lead.txt) python3 tex2docx.py     # writes Paper.docx

Word has no float algorithm, so figures and tables are placed with `w:framePr`
(figures) and `w:tblpPr` (tables) anchored to the top of the page text area.
Which page a float lands on follows from which page its anchor paragraph falls
on, so `shift.json` records a per-float anchor offset in body paragraphs -
positive defers a float, negative lets it overtake earlier floats the way
LaTeX's separate figure and table queues do.

`check.py` measures a build against `paper/main.pdf`; `opt.py` searches leading
and anchor offsets until pages, reference page and float positions all match.
