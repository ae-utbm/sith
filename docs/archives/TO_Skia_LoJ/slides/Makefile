LATEX := pdflatex
TARGET := slide.pdf

.PHONY: all clean distclean

all: $(TARGET) clean

%.pdf: %.tex
	echo "Building pdf"
	$(LATEX) --shell-escape $<
	rm -f $@
	$(LATEX) --shell-escape $<

clean:
	rm -f *.log *.nav *.snm *.aux *.out *.toc *.pyg

distclean: clean
	rm -f $(TARGET)
