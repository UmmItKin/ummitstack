# Output is <SID>_<NAME>.pdf. Set NAME to what the assignment asks for, e.g. exe03.
NAME := answer
SID := $(shell sed -n 's/.*\\newcommand{\\SID}{\(.*\)}/\1/p' private.tex)
JPGS := $(patsubst screenshots/%.png,jpg/%.jpg,$(wildcard screenshots/*.png))

$(SID)_$(NAME).pdf: answer.md private.tex header.tex codetitle.lua style.tex $(JPGS)
	pandoc answer.md -H header.tex -H private.tex -H style.tex --lua-filter=codetitle.lua --pdf-engine=xelatex -o $@

# xelatex takes minutes on full-size PNGs; JPEG copies build in seconds.
jpg/%.jpg: screenshots/%.png
	@mkdir -p jpg
	magick $< -quality 92 $@
