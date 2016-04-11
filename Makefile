all:
	@echo "No all rule, only clean"

clean:
	$(RM) -r paste_bottle/pastes/PASTE-*
	find . -iname "*.pyc" -exec rm {} \;
