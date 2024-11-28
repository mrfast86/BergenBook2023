# BergenBook Makefile

# Install dependencies
install:
    pip install -r requirements.txt

# Edit BergenBook.py
edit:
    @echo "Edit the EDIT section in BergenBook.py before running"

.PHONY: install edit