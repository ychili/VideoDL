PYTHON ?= python3

PANDOC_MAN_OPTS = --metadata=pandoc-version:false --metadata=hyphenate:true

# Doc sources in DOCSDIR -> doc output in DATADIR
DOCSDIR = docs
DATADIR = data
# If any of these files are changed, update the datestamp:
DOC_SRC = $(addprefix $(DOCSDIR)/,video-dl.1.rst VideoDL.conf.5.rst include/SYNOPSIS.rst include/OPTIONS.rst include/CONFIGKEYS.rst)
METADATA = $(DATADIR)/version.yaml $(DATADIR)/date.yaml
PANDOC_METADATA_OPTS = $(addprefix --metadata-file=, $(METADATA))

git_available = $(shell git rev-parse --is-inside-work-tree 2>/dev/null)

docs: $(DATADIR)/MANUAL.txt $(DATADIR)/video-dl.1.gz $(DATADIR)/VideoDL.conf.5.gz

clean:
	rm -rf $(DATADIR)

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

$(DATADIR)/version.yaml: video_dl.py | $(DATADIR)
	$(PYTHON) scripts/get_version.py video_dl.py > $(DATADIR)/version.yaml

$(DATADIR)/date.yaml: $(DOC_SRC) | $(DATADIR)
# See if we are in a checked out repo. Then, print the committer date.
# If not, fall back on the old method of getting the max mtime.
# This should work whether the user is building from a checked out Git repo
# or whether the user is building from a source distribution (tarball).
ifeq ($(git_available),true)
	# Set the manual date from the Git committer date.
	printf 'date: %s\n' "$$(git log -1 --pretty=format:%cs $(DOC_SRC))" \
		> $(DATADIR)/date.yaml
else
	# Set the manual date from the files' mtime.
	$(PYTHON) scripts/get_mtime.py $(DOC_SRC) > $(DATADIR)/date.yaml
endif

# Cross-platform, readable summary of the above
$(DATADIR)/MANUAL.txt: $(DOCSDIR)/Manual.rst $(METADATA) | $(DATADIR)
	pandoc --to "plain" --standalone \
		$(METADATA) $(DOCSDIR)/Manual.rst -o $(DATADIR)/MANUAL.txt

$(DATADIR):
	mkdir -p $(DATADIR)

test:
	$(PYTHON) -m doctest video_dl.py
	$(PYTHON) -m unittest tests/test*.py


.PHONY: docs clean test
