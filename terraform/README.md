# Terraform

The whole Zetrax Collects stack — DynamoDB, IAM, Lambda, API Gateway, S3 and CloudFront — defined as code.

State lives in `s3://zetrax-tfstate-794692801848/zetrax-collects/terraform.tfstate`, encrypted and versioned. Locking uses the S3 backend's native lockfile (Terraform ≥ 1.10), no DynamoDB table required.

## Usage

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

A clean plan should report `No changes. Your infrastructure matches the configuration.`

## Updating the Lambda

Edit `../lambda/lambda_function.py` and run `terraform apply`. The zip is rebuilt from source and the function is updated when its hash changes.

## Updating the frontend

Edit the files in `../frontend/` and run `terraform apply`. CloudFront caches aggressively — invalidate manually if you need the new copy immediately:

```bash
aws cloudfront create-invalidation --distribution-id $(terraform output -raw cloudfront_distribution_id) --paths '/*'
```

## Outputs

- `site_url` — the CloudFront URL
- `api_url` — the API Gateway endpoint
- `frontend_bucket` — the S3 bucket name
- `cloudfront_distribution_id` — for cache invalidations

## Notes

- The API Gateway was originally created via "quick create", which the AWS provider refuses to import piece by piece. It's modelled on the API resource itself with `target = <lambda arn>` and `ignore_changes = [target]`; changing it would replace the API and the URL would change.
- The CloudFront distribution serves the S3 bucket's **public website endpoint** over HTTP. Migrating to a private bucket + origin access control (OAC) is a reasonable follow-up.
- All resources are tagged `Project = zetrax-collects`, `ManagedBy = terraform`.
