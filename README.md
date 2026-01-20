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
| `REPLACE_ME_AWS_REGION` | AWS Region for ECR and deployment | `REPLACE_ME_AWS_REGION` |
| `REPLACE_ME_AWS_ACCOUNT_ID` | AWS Account ID | `123456789012` |
| `REPLACE_ME_PORT` | Port the application runs on | `REPLACE_ME_PORT` |

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
---

## Full AWS + EKS Setup Guide (End-to-end)

This section consolidates a practical, step-by-step setup for AWS ECR, IAM, GitHub Secrets, and an EKS Kubernetes cluster, plus common pitfalls and fixes. Example values below are tailored for this project:

- App name: `REPLACE_ME_APP_NAME`
- AWS account ID: `REPLACE_ME_AWS_ACCOUNT_ID`
- AWS region: `REPLACE_ME_AWS_REGION`
- Port: `REPLACE_ME_PORT`

### 0. Account, MFA, and Credentials Safety
- Enable MFA on your AWS root account.
- Prefer an Admin IAM user (with `AdministratorAccess`) for day‑to‑day administration instead of using the root user.
- Use AWS profiles to avoid mixing credentials:

```bash
| `AWS_ACCESS_KEY_ID` | AWS Access Key for CI user |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Access Key for CI user |
| `ECR_REPO_NAME` | Name of the ECR repository (e.g., `my-payment-api`) |
| `GITHUB_TOKEN` | Automatically provided by GitHub Actions (used to push changes) |

### 5. Kubernetes Manifests
Located in `manifests/`.
- **base/**: Common resources (Deployment, Service, Ingress).
- **overlays/qa**: QA specific configuration.
- **overlays/prod**: Prod specific configuration.

### 1. Create ECR Repository (Admin or PowerUser)
If your CI user can't create repositories, create ECR with the admin profile first:

```bash

### Deployment Flow
1. **QA**: Push to `main` branch triggers QA build & deploy.
2. **Prod**: Push to `prod` branch triggers Prod build & deploy.

Note the `repositoryUri` returned, e.g. `REPLACE_ME_AWS_ACCOUNT_ID.dkr.ecr.REPLACE_ME_AWS_REGION.amazonaws.com/REPLACE_ME_APP_NAME`.

### 2. Create GitHub CI/CD IAM User
Create a programmatic user (e.g., `github-ci-user`) and attach ECR permissions. You can use the minimal push policy from the earlier section or attach the managed policy for broader ECR operations:

- Managed policy (simple): `arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser`

This allows pushing images and managing repositories. Then generate access keys for this user.

### 3. Add GitHub Repository Secrets
In GitHub → Settings → Secrets and variables → Actions → New repository secret, add:

- `AWS_ACCESS_KEY_ID` → Access key for `github-ci-user`
- `AWS_SECRET_ACCESS_KEY` → Secret key for `github-ci-user`
- `ECR_REPO_NAME` → `REPLACE_ME_APP_NAME`

Also set: Settings → Actions → General → Workflow permissions → Read and write permissions.

### 4. Create an EKS Cluster (Console – Recommended)

1) Create Cluster IAM Role:
- IAM → Roles → Create role → AWS service → EKS → EKS Cluster → Next → (policy `AmazonEKSServiceRolePolicy` attached) → Name `EKSClusterRole` → Create.

2) Create Cluster:
- EKS → Clusters → Create cluster.
- Name: `REPLACE_ME_APP_NAME-cluster`.
- Kubernetes version: choose a stable version (1.31 recommended for new setups). 1.34 works but requires up-to-date add-ons.
- Cluster service role: `EKSClusterRole`.
- VPC/Subnets: select your VPC and typically 2–3 subnets across different AZs.
- Disable “EKS Auto Mode” unless you specifically need it (it requires extra policies like `AmazonEKSComputePolicy`, `AmazonEKSNetworkingPolicy`, etc.).
- Create and wait for status `ACTIVE`.

3) Create Node IAM Role:
- IAM → Roles → Create role → AWS service → EC2 → Next.
- Attach policies: `AmazonEKSWorkerNodePolicy`, `AmazonEKS_CNI_Policy`, `AmazonEC2ContainerRegistryReadOnly`, and `AmazonSSMManagedInstanceCore` (essential for debugging/session manager).
- Name: `EKSNodeRole` → Create.

4) Configure IAM Access Entry (Critical Step):
Modern EKS (1.23+) uses Access Entries. For standard Amazon Linux nodes, you must explicitly set the "EC2 Linux" type to avoid identity mismatches.
- EKS Console → Select Cluster `REPLACE_ME_APP_NAME-cluster` → **Access** tab.
- Click **Create access entry**.
- **IAM Principal**: Select `EKSNodeRole`.
- **Type**: Select **EC2 Linux** (Important: Do not use Standard/EC2 default, which is for Bottlerocket).
- Click **Create**.
*Note: If you skip this, nodes may fail to join with "User system:node:i-xxx cannot get resource" errors.*

5) Create Managed Node Group:
- Cluster → Compute tab → Create node group.
- Name: `REPLACE_ME_APP_NAME-nodes`.
- Node IAM role: `EKSNodeRole`.
- AMI type: Amazon Linux 2023 (x86_64) Standard.
- Instance type: `t3.medium` (cost-effective to start).
- Disk: `20` GiB.
- Desired/Min/Max: start with 1–2 nodes.
- Subnets: pick 2 from different AZs (simpler networking).
- Create and wait for `ACTIVE`.

6) Configure OIDC & IAM Trust (Critical for External Secrets):
   This step is required for the External Secrets Operator to authenticate with AWS.

   **A. Associate OIDC Provider:**
   1. Go to EKS Console → Cluster `REPLACE_ME_APP_NAME-cluster` → **Access** (or Overview).
   2. Locate **OpenID Connect provider URL**.
   3. If not associated, click **Associate Identity Provider**.

   **B. Update IAM Role Trust Policy:**
   Your node role needs to trust this OIDC provider.
   1. Go to IAM Console → Roles → `EKSNodeRole`.
   2. Click **Trust relationships** → **Edit trust policy**.
   3. Update the JSON to include the OIDC statement. Ensure you replace `123456789012` with your account ID and matching OIDC ID.

   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Principal": { "Service": "ec2.amazonaws.com" },
               "Action": "sts:AssumeRole"
           },
           {
               "Effect": "Allow",
               "Principal": {
                   "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.REPLACE_ME_AWS_REGION.amazonaws.com/id/YOUR_OIDC_ID_HERE"
               },
               "Action": "sts:AssumeRoleWithWebIdentity",
               "Condition": {
                   "StringEquals": {
                       "oidc.eks.REPLACE_ME_AWS_REGION.amazonaws.com/id/YOUR_OIDC_ID_HERE:sub": "system:serviceaccount:external-secrets:external-secrets",
                       "oidc.eks.REPLACE_ME_AWS_REGION.amazonaws.com/id/YOUR_OIDC_ID_HERE:aud": "sts.amazonaws.com"
                   }
               }
           }
       ]
   }
   ```

7) Configure kubectl locally:

```bash
aws eks update-kubeconfig --name REPLACE_ME_APP_NAME-cluster --region REPLACE_ME_AWS_REGION

## Local Development

```bash
pip install -r requirements.txt
python app.py

### 5. Install External Secrets Controller
This template expects Kubernetes External Secrets to sync SSM parameters into K8s Secrets.

```bash
```
or
```bash
uvicorn app:app --reload

### 6. Create SSM Parameter Store Entries
Match keys to `manifests/overlays/prod/external-secret.yaml` (updated to `/REPLACE_ME_APP_NAME/prod/...`). Start minimally:

```bash
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


### 7. CI/CD Pipelines
- Push to `main` triggers QA pipeline; push to `prod` triggers Prod pipeline.

**Required Permissions for CI User:**
The `github-ci-user` needs three sets of permissions:
1.  **ECR**: To push Docker images (handled by `AmazonEC2ContainerRegistryPowerUser` or custom policy).
2.  **EKS Describe**: To run `aws eks update-kubeconfig`.
    ```bash
    aws iam put-user-policy \
        --user-name github-ci-user \
        --policy-name GitHubActionEKSView \
        --policy-document '{"Version": "2012-10-17","Statement": [{"Effect": "Allow","Action": ["eks:DescribeCluster"],"Resource": "*"}]}'
    ```
3.  **Cluster Authorization**: To run `kubectl apply`.
    *Note: This must be run by the Cluster Creator/Admin.*
    ```bash
    aws eks create-access-entry --cluster-name REPLACE_ME_APP_NAME-cluster --principal-arn arn:aws:iam::REPLACE_ME_AWS_ACCOUNT_ID:user/github-ci-user --type STANDARD --username github-ci-user
    aws eks associate-access-policy --cluster-name REPLACE_ME_APP_NAME-cluster --principal-arn arn:aws:iam::REPLACE_ME_AWS_ACCOUNT_ID:user/github-ci-user --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy --access-scope type=cluster
    ```

### 8. Kubernetes Add-ons (for newer K8s like 1.34)
If using Kubernetes / Access Entry Mismatch**:
    - **Symptom**: Nodes launch in EC2 but don't appear in `kubectl get nodes`. Logs show `User "system:node:i-..." cannot get resource "csinodes"`.
    - **Fix (Applies to EKS 1.23+)**: EKS expects the node to identify as an Instance ID (`i-123`), but Amazon Linux identifies as a DNS name (`ip-172...`).
      1. Go to EKS Console → Access.
      2. Delete the Entry for your node role if it says type `EC2` or `Standard`.
      3. Create a new Entry for the role with type `EC2_LINUX`.
- **Nodes fail RBAC (Legacy aws-auth)**:
    - If not using Access Entries (older clusters), create/patch `aws-auth`
- **Nodes failed to join / NodeCreationFailure**:
  - Use 2 subnets across different AZs to start (simplifies networking).
  - Verify node role policies: `AmazonEKSWorkerNodePolicy`, `AmazonEKS_CNI_Policy`, `AmazonEC2ContainerRegistryReadOnly`.
  - Ensure cluster security group allows traffic from the node security group.
  - For K8s 1.34, update add-ons to matching versions.
  - Recreate the node group if stuck; occasionally EC2 boot timing causes transient failures.
- **Nodes fail RBAC (aws-auth missing/empty)**:
    - Confirm kubeconfig access: `aws eks update-kubeconfig --name <cluster> --region REPLACE_ME_AWS_REGION`.
    - Create/patch `aws-auth` to map the node role:

        ```bash
        kubectl apply -f - <<'EOF'
        apiVersion: v1
        kind: ConfigMap
        metadata:
            name: aws-auth
            namespace: kube-system
        data:
            mapRoles: |
                - rolearn: arn:aws:iam::REPLACE_ME_AWS_ACCOUNT_ID:role/EKSNodeRole
                    username: system:node:{{EC2PrivateDNSName}}
                    groups:
                        - system:bootstrappers
                        - system:nodes
        EOF
        ```

    - Then recreate the node group (or let a rolling replace happen) and check: `kubectl get nodes`.
- **AccessDenied on ECR create**:
  - Create repositories with an admin profile, or attach `AmazonEC2ContainerRegistryPowerUser` to the CI user.
- **kubectl unauthorized**:
  - Re-run `aws eks update-kubeconfig ...` and verify IAM principal has EKS access.
- **Secrets not appearing**:
  - Ensure External Secrets controller is installed and SSM keys exactly match the `external-secret.yaml` `data.key` values.

### 10. Security & Hygiene
- Never commit credentials; store keys in GitHub Secrets and AWS SSM.
- Add `.env` to `.gitignore` if you use local env files.
- Rotate IAM access keys regularly; enable MFA on root and admins.

### 11. Testing & Validation

Once you push code to GitHub and the Action completes (Green), verify the deployment in your terminal.

**1. Watch the Rollout:**
Wait for Kubernetes to gracefully update the pods.
```bash
kubectl rollout status deployment/REPLACE_ME_APP_NAME -n qa-REPLACE_ME_APP_NAME
```
*   *Success:* "successfully rolled out"
*   *Stuck?* Press `Ctrl+C` and check pods (Step 2).

**2. Verify Secrets & Pods:**
If pods are failing, it's usually because Secrets failed to sync.
```bash
# Check Secret Status (Must be "True")
kubectl get externalsecret -n qa-REPLACE_ME_APP_NAME

# Check Pod Status (Must be "Running")
kubectl get pods -n qa-REPLACE_ME_APP_NAME
```
*   *Status `SecretSyncedError`?* Your IAM Trust Policy or OIDC setup is likely wrong (See Step 6).
*   *Status `CreateContainerConfigError`?* The pod cannot find the secret. Fix the SecretSyncedError first.
*   *Status `CrashLoopBackOff`?* The app started but crashed. Check app logs:
    ```bash
    kubectl logs -l app.kubernetes.io/name=REPLACE_ME_APP_NAME -n qa-REPLACE_ME_APP_NAME
    ```

**3. Test the API (Port Forwarding):**
Since we don't have a public domain yet, tunnel to the pod locally:
```bash
kubectl port-forward svc/REPLACE_ME_APP_NAME 8080:80 -n qa-REPLACE_ME_APP_NAME
```
Then open in browser: [http://localhost:8080/](http://localhost:8080/) or [http://localhost:8080/docs](http://localhost:8080/docs) (Swagger UI).

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
#### D. Deployment Permissions
The Github Actions user (`github-ci-user`) is not your Admin user. It cannot just "see" the cluster. You must explicitly grant it rights:

1.  **EKS View Permission** (AWS IAM): Gives the robot permission to run `aws eks describe-cluster`.
2.  **Cluster RBAC** (Kubernetes Auth): Gives the robot permission to `kubectl apply` manifests.

Refer to **Step 7** above for the exact commands to run.

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

You must install the **External Secrets Operator** and create the **Namespaces** before the pipeline runs.

**Prerequisites:**
- `kubectl` installed.
- `helm` installed (`brew install helm` on macOS).
- `aws` CLI configured with cluster admin access.

1.  **Install External Secrets Operator** (via Helm):
    *Note: This installs Custom Resource Definitions (CRDs). If your pipeline fails with "no matches for kind ExternalSecret", the CRDs are likely missing.*
    ```bash
    helm repo add external-secrets https://charts.external-secrets.io
    helm install external-secrets \
       external-secrets/external-secrets \
        -n external-secrets \
        --create-namespace \
        --set installCRDs=true
    ```

2.  **Create Namespaces**:
    The pipeline tries to deploy to specific namespaces defined in `kustomization.yaml`. You must create them first:
    ```bash
    kubectl create namespace qa-REPLACE_ME_APP_NAME
    kubectl create namespace prod-REPLACE_ME_APP_NAME
    ```

3.  **Node Permissions**:
    Ensure the IAM Role attached to your Kubernetes EC2 Nodes (`EKSStandardNodeRole`) has:
    -   `AmazonEC2ContainerRegistryReadOnly` (to pull images)
    -   `AmazonSSMManagedInstanceCore` (to fetch secrets, if using Instance Profile auth)

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
