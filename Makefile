.PHONY: lint

lint:
	ruff check --select I --fix && ruff format

export:
	poetry export --without-hashes --without dev -f requirements.txt -o requirements.txt

start-streamlit:
	nohup streamlit run coin_data/app/__main__.py &

stop-streamlit:
	lsof -ti:8501 | xargs kill

start-streamlit-prod:
	nohup poetry run streamlit run coin_data/app/__main__.py &

stop-streamlit-prod:
	lsof -ti:8501 | xargs kill

start-scraping:
	python coin_data/exchanges/pumpfun/__main__.py $(filter-out $@,$(MAKECMDGOALS))

%:
	@:
