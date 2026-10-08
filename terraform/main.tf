locals {
  table_name = "${var.name_prefix}-pack-history"
}

# ---------------------------------------------------------------- DynamoDB
resource "aws_dynamodb_table" "pack_history" {
  name         = local.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pack_id"

  attribute {
    name = "pack_id"
    type = "S"
  }
}

# --------------------------------------------------------------------- IAM
data "aws_iam_policy_document" "lambda_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "dynamo_access" {
  statement {
    # Live policy also allows GetItem/UpdateItem; the Lambda only needs these two.
    actions   = ["dynamodb:PutItem", "dynamodb:Scan"]
    resources = [aws_dynamodb_table.pack_history.arn]
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${var.name_prefix}-pack-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "dynamo" {
  name   = "DynamoDBAccess"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.dynamo_access.json
}

# ------------------------------------------------------------------ Lambda
data "archive_file" "lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/lambda_function.py"
  output_path = "${path.module}/.build/function.zip"
}

resource "aws_lambda_function" "pack_opener" {
  function_name    = "${var.name_prefix}-pack-opener"
  description      = "Opens a weighted-random Pokemon TCG pack and stores it in DynamoDB."
  role             = aws_iam_role.lambda.arn
  runtime          = var.lambda_runtime
  handler          = "lambda_function.lambda_handler"
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
}

# ------------------------------------------------------------- API Gateway
resource "aws_apigatewayv2_api" "api" {
  name          = "${var.name_prefix}-pack-api"
  protocol_type = "HTTP"
  # Quick-create: AWS made the default route, Lambda integration and auto-deploy $default stage itself.
  target = aws_lambda_function.pack_opener.arn

  lifecycle {
    ignore_changes = [target] # not readable after import; changing it would replace the API (and its URL)
  }

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET"]
    allow_headers = ["content-type"]
  }
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "APIGatewayInvokePack"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.pack_opener.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

