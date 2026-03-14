# Core Services

CORE SERVICES is an external repo that is managed from outside, 

**Do not touch this repo while using it inside another project**

## Environment Variables

## POSTGRESS create_db.py
DB_URL=
DB_HOST=
DB_PORT=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=

### oauth2_service.py
Required-google:
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

Required-facebook:
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=

### email_service.py
Required:
SENDGRID_API_KEY=
FROM_EMAIL=
APP_NAME=

Optional:
EMAIL_TEMPLATES_DIR

### specific_emails.py
Required:
APP_NAME=
FRONTEND_URL=
Also requires all environment variables from `email_service.py`.

### openai_service.py
Required:
OPENAI_API_KEY=

### langfuse_service.py
Required:
LANGFUSE_SECRET_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_HOST=

### logger_service.py
Add slack-sdk in requirements.txt
Optional:
SLACK_TOKEN=
SLACK_CHANNEL=
ENVIRONMENT=


### auth_service.py
Required
this file needs models.py and schema.py to work properly

YOU ARE ALSO REQUIRED TO INSTALL THOSE LIBRARIES: 
Required:
slack-sdk
alembic
psycopg2-binary

## Example Files

The following example files are provided as templates:
- `example-compose.yaml`
- `example-start.sh`
- `example.Dockerfile`

**Important:** These are example files only. Do not modify them. Create identical files in the root of your project (without the `example-` prefix) and customize them as needed.