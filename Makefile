all:
	@echo "No all rule, only clean"

clean:
	$(RM) -r pastes/PASTE-*
	find . -iname "*.pyc" -exec rm {} \;
