CC=pdflatex

all: rapport clean

rapport: Rapport.tex
	@echo "Compiling "$<
	$(CC) $<
	$(CC) $<

clean:
	@echo "Cleaning folder"
	rm *.aux; rm *.log; rm *.out; rm *.toc; rm *.snm; rm *.nav; rm *.lof

