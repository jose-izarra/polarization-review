.PHONY: assess-all-topics run-pipeline-topics

run-pipeline-topics:
	@if [ -z "$(TOPICS)" ]; then \
		echo "No topics provided. Usage: make run-pipeline-topics TOPICS=\"abortion,gun control,the dress is blue\""; \
	else \
		echo "$(TOPICS)" | tr ',' '\n' | xargs -n 1 -P 4 -I {} uv run scripts/run_pipeline.py --topic "{}"; \
	fi

assess-all-topics:
	@files=$$(ls data/items_*.json 2>/dev/null); \
	if [ -z "$$files" ]; then \
		echo "No data/items_*.json files found."; \
		exit 1; \
	fi; \
	printf '%s\n' $$files | xargs -n 1 -P 4 -I {} sh -c 'uv run scripts/assess_from_file.py "$$1" $${2:+--note "$$2"}' _ {} "$(NOTE)"
