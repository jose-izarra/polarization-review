.PHONY: assess-all-topics

assess-all-topics:
	@files=$$(ls data/items/items_*.json 2>/dev/null); \
	if [ -z "$$files" ]; then \
		echo "No data/items/items_*.json files found."; \
		exit 1; \
	fi; \
	printf '%s\n' $$files | xargs -n 1 -P 4 -I {} uv run scripts/assess_from_file.py "{}"
