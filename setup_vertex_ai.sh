#!/bin/bash

# ViMax Vertex AI Setup Script
# This script helps you configure ViMax to use Google Vertex AI

set -e

echo "=================================================="
echo "  ViMax + Google Vertex AI Setup"
echo "=================================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not found!"
    echo "Please install Google Cloud SDK first:"
    echo "  https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "✅ Google Cloud SDK found"
echo ""

# Get current project
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)

if [ -z "$CURRENT_PROJECT" ]; then
    echo "No GCP project configured."
    echo ""
    echo "Please enter your Google Cloud Project ID:"
    read -r PROJECT_ID
    gcloud config set project "$PROJECT_ID"
else
    echo "Current GCP project: $CURRENT_PROJECT"
    echo ""
    echo "Use this project? (y/n)"
    read -r USE_CURRENT

    if [ "$USE_CURRENT" != "y" ]; then
        echo "Please enter your Google Cloud Project ID:"
        read -r PROJECT_ID
        gcloud config set project "$PROJECT_ID"
    else
        PROJECT_ID=$CURRENT_PROJECT
    fi
fi

echo ""
echo "Using project: $PROJECT_ID"
echo ""

# Authenticate
echo "Authenticating with Google Cloud..."
gcloud auth application-default login

echo ""
echo "✅ Authentication complete"
echo ""

# Enable required APIs
echo "Enabling required APIs..."
echo "  - AI Platform API"
echo "  - Compute Engine API"

gcloud services enable aiplatform.googleapis.com
gcloud services enable compute.googleapis.com

echo ""
echo "✅ APIs enabled"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
if command -v uv &> /dev/null; then
    echo "Using uv..."
    uv add google-cloud-aiplatform
    uv sync
else
    echo "Using pip..."
    pip install google-cloud-aiplatform
fi

echo ""
echo "✅ Dependencies installed"
echo ""

# Update config files
echo "Updating configuration files with your project ID..."

# Update idea2video_vertex.yaml
sed -i.bak "s/YOUR_GCP_PROJECT_ID/$PROJECT_ID/g" configs/idea2video_vertex.yaml
echo "  ✓ configs/idea2video_vertex.yaml"

# Update script2video_vertex.yaml
sed -i.bak "s/YOUR_GCP_PROJECT_ID/$PROJECT_ID/g" configs/script2video_vertex.yaml
echo "  ✓ configs/script2video_vertex.yaml"

# Clean up backup files
rm -f configs/*.bak

echo ""
echo "✅ Configuration files updated"
echo ""

# Verify access to models
echo "Verifying access to Vertex AI models..."
echo "Please visit the following URL to check model availability:"
echo "  https://console.cloud.google.com/vertex-ai/publishers?project=$PROJECT_ID"
echo ""
echo "Make sure you have access to:"
echo "  - Veo 3 (video generation)"
echo "  - Imagen 3 (image generation)"
echo "  - Gemini 2.5 Flash (chat/planning)"
echo ""

echo "=================================================="
echo "  ✅ Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "  1. Verify model access at the URL above"
echo "  2. Run your first video:"
echo "     python main_idea2video_vertex.py"
echo "     OR"
echo "     python main_script2video_vertex.py"
echo ""
echo "Documentation: VERTEX_AI_INTEGRATION.md"
echo "=================================================="
