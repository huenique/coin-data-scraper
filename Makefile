.PHONY: lint

lint:
	ruff check --select I --fix && ruff format

export:
	poetry export --without-hashes --without dev -f requirements.txt -o requirements.txt

start-streamlit:
	nohup poetry run streamlit run coin_data/app/__main__.py &

stop-streamlit:
	lsof -ti:8501 | xargs kill

start-streamlit-prod:
	nohup poetry run streamlit run coin_data/app/__main__.py &

stop-streamlit-prod:
	lsof -ti:8501 | xargs kill

start-scraping:
	poetry run python coin_data/exchanges/pumpfun/__main__.py $(filter-out $@,$(MAKECMDGOALS))

start-service:
	poetry run gunicorn -k uvicorn.workers.UvicornWorker -w 1 -b 0.0.0.0:8000 coin_data.server.api:app

%:
	@:
