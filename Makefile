.PHONY: assess-all-topics run-pipeline-topics

ASSESS_ITEMS ?= \
	data/items_abortion.json \
	data/items_gun_control.json \
	data/items_inflation.json \
	data/items_nasa_funding.json

# Split TOPICS on commas only; xargs default whitespace splitting breaks topics with spaces.
run-pipeline-topics:
	@if [ -z "$(TOPICS)" ]; then \
		echo "No topics provided. Usage: make run-pipeline-topics TOPICS=\"abortion,gun control\""; \
	else \
		printf '%s' "$(TOPICS)" | tr ',' '\n' | awk 'NF' | tr '\n' '\0' | xargs -0 -n 1 -P 4 -I {} uv run scripts/run_pipeline.py --topic "{}"; \
	fi

assess-all-topics:
	@if [ -z "$(strip $(ASSESS_ITEMS))" ]; then \
		echo "No ASSESS_ITEMS defined in Makefile."; \
		exit 1; \
	fi; \
	printf '%s\n' $(ASSESS_ITEMS) | xargs -n 1 -P 4 -I {} sh -c 'uv run scripts/assess_from_file.py "$$1" $${2:+--note "$$2"}' _ {} "$(NOTE)"
