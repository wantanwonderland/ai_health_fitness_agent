#!/bin/bash
# Purpose: To deploy the App to Cloud Run.

# Google Cloud Project ID
PROJECT=gengpt-master

# Google Cloud Region
LOCATION=us-central1

# Deploy app from source code
gcloud run deploy health-ai-agent --source . --region=$LOCATION --project=$PROJECT --allow-unauthenticated