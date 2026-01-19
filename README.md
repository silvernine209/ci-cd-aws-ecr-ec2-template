# ci-cd-aws-ecr-ec2-template

Reusable GitHub Actions CI/CD pipeline template for:
- Building Docker images
- Pushing to AWS Elastic Container Registry (ECR)
- Deploying to AWS EC2 instances
- Supporting QA and Prod branch workflows

This repository is designed to be used as a template for backend services that require automated Docker builds, multi-environment releases, and AWS deployment automation.

## Features

- Docker image build workflows
- ECR push automation
- QA and Prod branch triggers
- EC2 deployment via AWS CLI / SSM / CodeDeploy (configurable)
- GitHub Actions reusable workflows

## Getting Started

1. **Create a new repository** from this template.
2. Configure GitHub Secrets:
   - `AWS_ROLE_TO_ASSUME_QA`
   - `AWS_ROLE_TO_ASSUME_PROD`
   - `QA_EC2_INSTANCE_ID`
   - `PROD_EC2_INSTANCE_ID`
3. Customize `.github/workflows` for your project.
4. Update AWS IAM roles and EC2 setup to support deploy steps.
5. Push to `qa` and merge to `prod` to trigger CI/CD.

## Usage

**Pipeline triggers**
- Push to `qa`: Builds the Docker image, pushes to ECR, deploys to QA EC2.
- Merge to `prod`: Builds the Docker image, pushes to ECR, deploys to Prod EC2.

**Workflow structure**
Workflows live in `.github/workflows/`, and share reusable build logic.

## Contributing

Contributions and improvements are welcome.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
