# Note‑App ( FastAPI - AWS - CDK )

Tiny serverless toy project for file uploads ("Notes"):

* **FastAPI + Mangum** – application layer  
* **AWS Lambda (container image)** – compute  
* **API Gateway** – HTTPS entry  
* **DynamoDB** – Note metadata  
* **S3** – optional file attachment storage  
* **AWS Python CDK** – IaC
* **pytest + moto** – AWS‑free tests (run in CI)

---

## Getting started

1. clone & install
```bash
git clone https://github.com/DeepBlockDeepak/NotesAppCDK.git
cd note-app
poetry install --with dev
```

2. run FastAPI locally (no AWS calls)
```bash
poetry run uvicorn note_app.main:app --port 8000
```
Ping the test endpoint:
```bash
curl http://127.0.0.1:8000/api/v1/ping
# {"message":"pong"}
```

3. open http://127.0.0.1:8000/docs

## Unit Tests
Tests won't make real AWS calls — `moto` mocks DynamoDB & S3.
```bash
poetry run pytest -q
```

## Deploy to AWS
```bash
# build, bootstrap once, then deploy
npm i -g aws-cdk  # CDK CLI
cdk bootstrap
poetry run cdk deploy
```
