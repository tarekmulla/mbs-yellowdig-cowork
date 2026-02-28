.PHONY: setup install fetch publish clean help

VENV    := .venv
PYTHON  := $(VENV)/bin/python
PIP     := $(VENV)/bin/pip

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "  setup    Create virtual environment and install dependencies"
	@echo "  install  Install/update dependencies into existing venv"
	@echo "  fetch    Fetch posts from Yellowdig → posts.json"
	@echo "  publish  Publish analysis.json to Notion"
	@echo "  clean    Remove the virtual environment"

setup: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo ""
	@echo "Setup complete. Next: edit config.json with your API keys."

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

fetch: $(VENV)/bin/activate
	$(PYTHON) fetch_posts.py

publish: $(VENV)/bin/activate
	$(PYTHON) publish_digest.py

clean:
	rm -rf $(VENV)
