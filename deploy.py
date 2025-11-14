"""
Deployment script for Cloud Run
"""
import subprocess
import sys
import os

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"\n==> {description}")
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"ERROR: {description} failed")
        print(result.stderr)
        return False
    
    print(result.stdout)
    return True

def deploy_to_cloud_run():
    """Deploy backend to Google Cloud Run."""
    project_id = os.getenv("GCP_PROJECT_ID")
    region = os.getenv("GCP_REGION", "us-central1")
    service_name = "rnrltradehub-backend"
    
    if not project_id:
        print("ERROR: GCP_PROJECT_ID environment variable not set")
        return False
    
    steps = [
        # Build Docker image
        (
            f"gcloud builds submit --tag gcr.io/{project_id}/{service_name}",
            "Building Docker image"
        ),
        
        # Deploy to Cloud Run
        (
            f"gcloud run deploy {service_name} "
            f"--image gcr.io/{project_id}/{service_name} "
            f"--platform managed "
            f"--region {region} "
            f"--allow-unauthenticated "
            f"--set-env-vars DATABASE_URL=$$DATABASE_URL,"
            f"JWT_SECRET=$$JWT_SECRET,"
            f"SENDGRID_API_KEY=$$SENDGRID_API_KEY "
            f"--memory 512Mi "
            f"--cpu 1 "
            f"--max-instances 10 "
            f"--min-instances 1 "
            f"--timeout 300",
            "Deploying to Cloud Run"
        ),
        
        # Run database migrations
        (
            f"gcloud run jobs execute db-migrations --region {region}",
            "Running database migrations"
        )
    ]
    
    for command, description in steps:
        if not run_command(command, description):
            return False
    
    print("\n✅ Deployment completed successfully!")
    print(f"Service URL: https://{service_name}-{region}.run.app")
    return True

if __name__ == "__main__":
    success = deploy_to_cloud_run()
    sys.exit(0 if success else 1)
