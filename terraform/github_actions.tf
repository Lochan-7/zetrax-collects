# GitHub Actions OIDC — lets the repo's workflows assume an AWS role with no long-lived keys.

variable "github_repo" {
  description = "GitHub owner/repo allowed to assume the deploy role."
  type        = string
  default     = "Lochan-7/zetrax-collects"
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["ffffffffffffffffffffffffffffffffffffffff"] # AWS validates the real cert against its own trust store; this value is a placeholder AWS accepts.
}

data "aws_iam_policy_document" "github_actions_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:*"]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name               = "${var.name_prefix}-github-actions"
  assume_role_policy = data.aws_iam_policy_document.github_actions_trust.json
}

# Services this stack provisions, plus read/write on the Terraform state bucket.
data "aws_iam_policy_document" "github_actions_deploy" {
  statement {
    sid    = "StackServices"
    effect = "Allow"
    actions = [
      "apigateway:*",
      "cloudfront:*",
      "dynamodb:*",
      "iam:*",
      "lambda:*",
      "logs:*",
      "s3:*",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "StateLocking"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]
    resources = [
      "arn:aws:s3:::zetrax-tfstate-794692801848",
      "arn:aws:s3:::zetrax-tfstate-794692801848/*",
    ]
  }
}

resource "aws_iam_role_policy" "github_actions_deploy" {
  name   = "deploy"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_deploy.json
}

output "github_actions_role_arn" {
  value = aws_iam_role.github_actions.arn
}
