<h1 align="center">Email Management System</h1>

<p align="center">
  A Streamlit app for managing contacts, templates, outbound emails, reminders, and LLM-assisted drafting.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Streamlit-App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/Database-TinyDB-0A7EA4?style=for-the-badge" alt="TinyDB">
  <img src="https://img.shields.io/badge/Version-v1-1F8B4C?style=for-the-badge" alt="Version v1">
</p>

---

## 1) Project Overview

### What this app does today

- Manages recipient profiles (name, email, title, profession)
- Manages reusable email templates
- Sends emails immediately using SMTP credentials (`yagmail`)
- Stores sent-email records in TinyDB
- Creates reminder records and manages them from a dedicated page
- Stores a user profile/signature and can append signature while composing
- Includes an LLM comparison chatbot page (OpenAI vs AWS Bedrock) with shared guardrails, local retrieval context, and basic metrics

> Best suited for local/internal workflows and prototyping.

---

## 2) Run Locally

### Prerequisites

- Python `3.11+`
- `pip`

### Step 1: Clone and enter the project

```bash
git clone <your-repo-url>
cd email-management-system
```

### Step 2: Create a virtual environment

```bash
python -m venv .venv
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Create your `.env` file

```bash
cp .env.example .env
```

Fill in the keys you need:

| Key | Required | Purpose |
|---|---|---|
| `EMAIL_SENDER` | Yes (for send) | Sender email address for SMTP |
| `EMAIL_PASSWORD` | Yes (for send) | Sender app password / SMTP password |
| `OPENAI_API_KEY` | Yes (for OpenAI chatbot) | Enables OpenAI provider |
| `OPENAI_MODEL` | No | OpenAI model override (default: `gpt-4.1-nano`) |
| `AWS_REGION` | No | AWS region for Bedrock/CloudWatch |
| `BEDROCK_MODEL_ID` | No | Bedrock model ID |
| `LLM_REDACT_PII` | No | Redact sensitive values in outputs |
| `LLM_ENABLE_CLOUDWATCH` | No | Toggle telemetry logging to CloudWatch |
| `CLOUDWATCH_LOG_GROUP` | No | CloudWatch log group name |
| `CLOUDWATCH_LOG_STREAM` | No | CloudWatch log stream name |

### Step 5: Run the app

```bash
streamlit run src/Home.py
```

### Safe `.env` template for pushing

Use this as `.env.example` (safe to commit):

```env
# SMTP (required for Send Now)
EMAIL_SENDER=
EMAIL_PASSWORD=

# OpenAI (required for OpenAI provider calls)
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-nano

# AWS Bedrock (optional, boto3 uses normal AWS credential chain)
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=amazon.nova-micro-v1:0

# Chatbot guardrails/telemetry (optional)
LLM_REDACT_PII=true
LLM_ENABLE_CLOUDWATCH=false
CLOUDWATCH_LOG_GROUP=email-management/llm-comparison
CLOUDWATCH_LOG_STREAM=
```

---

## 3) Next Steps

### Upcoming features

1. Implement real scheduled sending with a background worker/queue (e.g., APScheduler/Celery)
2. Build out `Schedules`, `Search`, and `Dashboard` pages (currently placeholders)
3. Add profile/template edit actions (not only add/delete)
4. Add tests for DB operations, email sending path, and LLM service adapters
5. Add authentication and role-based access before production use

### Note to users

Feel free to use this template, and please star the repo if it helps you.

