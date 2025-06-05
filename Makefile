run_api:
	uvicorn main:app --reload

install_dependences:
	virtualenv my-env
	source my-env/bin/activate
	pip install -r requirements.txt