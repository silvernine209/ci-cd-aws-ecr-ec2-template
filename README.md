# API Service Template (FastAPI + Docker + AWS CI/CD)

This repository is a template for a FastAPI backend service with a GitHub Actions CI/CD pipeline that builds Docker images, pushes them to AWS ECR, and updates Kubernetes manifests (via Kustomize) for deployment.

## Getting Started

### 1. Instantiate the Template
Create a new repository from this template.

### 2. Configure the Project
Run a search and replace across the entire repository to replace the following placeholders with your project's specific values:

| Placeholder | Description | Example Value |
|-------------|-------------|---------------|
| `REPLACE_ME_APP_NAME` | Name of your application / service | `my-payment-api` |
| `REPLACE_ME_AWS_REGION` | AWS Region for ECR and deployment | `us-east-1` |
| `REPLACE_ME_AWS_ACCOUNT_ID` | AWS Account ID | `123456789012` |
| `REPLACE_ME_PORT` | Port the application runs on | `3000` |

### 3. Application Setup
- **app.py**: Contains a basic FastAPI "Hello World". Add your routers and business logic here.
- **Dockerfile**: Python 3.9 slim image. Adjust dependencies as needed.
- **requirements.txt**: List your Python dependencies here.

### 4. CI/CD Setup (.github/workflows)
The pipelines are configured to:
- Build and push Docker images to ECR.
- Update Image Tags in Kustomize manifests.
- Commit changes back to the repository (GitOps pattern).

**Required GitHub Secrets:**
| Secret Name | Description |
|-------------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS Access Key for CI user |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Access Key for CI user |
| `ECR_REPO_NAME` | Name of the ECR repository (e.g., `my-payment-api`) |
| `GITHUB_TOKEN` | Automatically provided by GitHub Actions (used to push changes) |

### 5. Kubernetes Manifests
Located in `manifests/`.
- **base/**: Common resources (Deployment, Service, Ingress).
- **overlays/qa**: QA specific configuration.
- **overlays/prod**: Prod specific configuration.

### Deployment Flow
1. **QA**: Push to `main` branch triggers QA build & deploy.
2. **Prod**: Push to `prod` branch triggers Prod build & deploy.

## Local Development

```bash
pip install -r requirements.txt
python app.py
```
or
```bash
uvicorn app:app --reload
```

## Infrastructure Setup Guide

### 1. Prerequisites
- **AWS CLI** installed and configured.
- **kubectl** installed and pointing to your cluster.
- **Cluster Admin** access to your Kubernetes environment.

### 2. AWS Resources Setup

#### A. Elastic Container Registry (ECR)
This service stores your Docker images. Run the following command to create the repository:

```bash
aws ecr create-repository \
    --repository-name <REPLACE_ME_APP_NAME> \
    --region <REPLACE_ME_AWS_REGION>
```
*Note: Ensure the repository name matches the `REPLACE_ME_APP_NAME` used in your configuration.*

#### B. SSM Parameter Store (Secrets)
The application pulls configuration from AWS Systems Manager (SSM) Parameter Store via Kubernetes External Secrets.

**Required IAM Permissions for Cluster Nodes:**
Your Kubernetes Worker Nodes (EC2) must have an IAM Role with `AmazonSSMReadOnlyAccess` (or a scoped policy) to read these parameters.

**Create Parameters:**
Run the following commands for each environment variable your application needs (replace values as needed):

```bash
# Example for Production Environment
aws ssm put-parameter \
    --name "/<REPLACE_ME_APP_NAME>/prod/OPENAI_API_KEY" \
    --value "sk-..." \
    --type "SecureString" \
    --region <REPLACE_ME_AWS_REGION>

aws ssm put-parameter \
    --name "/<REPLACE_ME_APP_NAME>/prod/DB_CONNECTION_STRING" \
    --value "postgres://user:pass@host:5432/db" \
    --type "SecureString" \
    --region <REPLACE_ME_AWS_REGION>
```

**Note on External Secret Manifests:**
Check `manifests/overlays/prod/external-secret.yaml`. The `key` fields (e.g., `/REPLACE_ME_APP_NAME/prod/OPENAI_API_KEY`) must match exactly the names you created in SSM.

#### C. IAM User for CI/CD Pipeline
GitHub Actions needs an IAM User to build and push images to ECR.

1.  **Create Policy `GitHubActionECRPolicy`**:
    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:GetRepositoryPolicy",
                    "ecr:DescribeRepositories",
                    "ecr:ListImages",
                    "ecr:DescribeImages",
                    "ecr:BatchGetImage",
                    "ecr:InitiateLayerUpload",
                    "ecr:UploadLayerPart",
                    "ecr:CompleteLayerUpload",
                    "ecr:PutImage"
                ],
                "Resource": "*"
            }
        ]
    }
    ```
2.  **Create User**: Create a programatic IAM user (e.g., `github-ci-user`) and attach the policy above.
3.  **Get Credentials**: Generate an **Access Key ID** and **Secret Access Key**.

---

### 3. Kubernetes Cluster Setup

This template uses the legacy `kubernetes-external-secrets` controller (deprecated but simple).

1.  **Install the Controller** (if not present):
    ```bash
    helm repo add external-secrets https://external-secrets.github.io/kubernetes-external-secrets/
    helm install external-secrets external-secrets/kubernetes-external-secrets
    ```

2.  **Node Permissions**:
    Ensure the IAM Role attached to your Kubernetes EC2 Nodes has:
    -   `AmazonEC2ContainerRegistryReadOnly` (to pull images)
    -   `AmazonSSMReadOnlyAccess` (to fetch secrets)

3.  **GitOps / CD**:
    Install **ArgoCD** or **Flux** and point it to this repository's `manifests/overlays/prod` folder.

---

### 4. GitHub Repository Setup

To connect your repository to AWS, add the following **Secrets** in GitHub:

1.  Navigate to **Settings** > **Secrets and variables** > **Actions**.
2.  Click **New repository secret**.
3.  Add the following:

| Secret Name | Value | Purpose |
|-------------|-------|---------|
| `AWS_ACCESS_KEY_ID` | `<Your_IAM_Access_Key>` | Authenticates CI user (from Step 2C). |
| `AWS_SECRET_ACCESS_KEY` | `<Your_IAM_Secret_Key>` | Authenticates CI user (from Step 2C). |
| `ECR_REPO_NAME` | `<REPLACE_ME_APP_NAME>` | Name of the ECR repo (from Step 2A). |

**Repositories Permissions:**
Go to **Settings** > **Actions** > **General** > **Workflow permissions** and select **Read and write permissions**. This is required for the pipeline to commit the new image tag back to the repository.

## License
MIT
