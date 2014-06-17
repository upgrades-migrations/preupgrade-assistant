GROUP_FILES=$(shell find . -name group.xml -printf "%h/%f ")
OSCAP=oscap

all: all-xccdf.xml guide.html sds-datastream.xml

all-xccdf.xml: template.xml $(GROUP_FILES) utils/xccdf_compose.py
	utils/xccdf_compose.py .
	$(OSCAP) xccdf validate-xml all-xccdf.xml

all-resolved-xccdf.xml: all-xccdf.xml
	$(OSCAP) xccdf resolve -o all-resolved-xccdf.xml all-xccdf.xml

guide.html: all-resolved-xccdf.xml
	$(OSCAP) xccdf generate guide all-resolved-xccdf.xml > guide.html

eval: all-resolved-xccdf.xml
	$(OSCAP) xccdf eval all-resolved-xccdf.xml; exit 0

results.xml: all-resolved-xccdf.xml
	$(OSCAP) xccdf eval --results results.xml all-resolved-xccdf.xml; exit 0

report.html: results.xml
	$(OSCAP) xccdf generate report results.xml > report.html

sds-datastream.xml: all-resolved-xccdf.xml
	utils/xml_append.py all-resolved-xccdf.xml dummy-oval-rule.xml > all-resolved-xccdf-dummyoval.xml
	$(OSCAP) ds sds-compose all-resolved-xccdf-dummyoval.xml sds-datastream-unformated.xml
	xmllint --format sds-datastream-unformated.xml > sds-datastream.xml
	rm sds-datastream-unformated.xml
	rm all-resolved-xccdf-dummyoval.xml

install: all-resolved-xccdf.xml guide.html
	./install.sh $(DESTDIR)

clean:
	rm -f "all-xccdf.xml"
	rm -f "all-resolved-xccdf.xml"
	rm -f "guide.html"
	rm -f "results.xml"
	rm -f "report.html"
	rm -f "sds-datastream.xml"
