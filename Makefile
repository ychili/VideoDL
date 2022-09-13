PANDOC_MAN_OPTS = --metadata=pandoc-version:false --metadata=hyphenate:true

# Doc sources in DOCSDIR -> doc output in DATADIR
DOCSDIR = docs
DATADIR = data
# If any of these files are changed, update the datestamp:
DOC_SRC = $(addprefix $(DOCSDIR)/,video-dl.1.rst VideoDL.conf.5.rst include/SYNOPSIS.rst include/OPTIONS.rst include/CONFIGKEYS.rst)
METADATA = $(DATADIR)/version.yaml $(DATADIR)/date.yaml
PANDOC_METADATA_OPTS = $(addprefix --metadata-file=, $(METADATA))

docs: $(DATADIR)/MANUAL.txt $(DATADIR)/video-dl.1.gz $(DATADIR)/VideoDL.conf.5.gz

clean:
	rm $(DATADIR)/*

%.gz: %
	gzip -9 -c $< > $@

$(DATADIR)/video-dl.1: $(DOCSDIR)/video-dl.1.rst $(METADATA) $(DOCSDIR)/include/SYNOPSIS.rst $(DOCSDIR)/include/OPTIONS.rst | $(DATADIR)
	pandoc --to "man" --standalone \
		$(PANDOC_MAN_OPTS) $(PANDOC_METADATA_OPTS) \
		--metadata-file=$(DOCSDIR)/video-dl.1.yaml \
		$(DOCSDIR)/video-dl.1.rst -o $(DATADIR)/video-dl.1

$(DATADIR)/VideoDL.conf.5: $(DOCSDIR)/VideoDL.conf.5.rst $(METADATA) $(DOCSDIR)/include/CONFIGKEYS.rst | $(DATADIR)
	pandoc --to "man" --standalone \
		$(PANDOC_MAN_OPTS) $(PANDOC_METADATA_OPTS) \
		--metadata-file=$(DOCSDIR)/VideoDL.conf.5.yaml \
		$(DOCSDIR)/VideoDL.conf.5.rst -o $(DATADIR)/VideoDL.conf.5

$(DATADIR)/version.yaml: video_dl.py
	./scripts/get_version.py video_dl.py > $(DATADIR)/version.yaml

$(DATADIR)/date.yaml: $(DOC_SRC)
	./scripts/get_mtime.py $? > $(DATADIR)/date.yaml

# Cross-platform, readable summary of the above
$(DATADIR)/MANUAL.txt: $(DOCSDIR)/Manual.rst $(METADATA) | $(DATADIR)
	pandoc --to "plain" --standalone \
		$(METADATA) $(DOCSDIR)/Manual.rst -o $(DATADIR)/MANUAL.txt

$(DATADIR):
	mkdir $(DATADIR)
