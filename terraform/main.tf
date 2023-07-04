variable "region" {
  default = "us-east-1"
  type    = string
}

variable "bucket_name" {
  default = "meirdev-upload-files"
  type    = string
}

provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "example_bucket" {
  bucket = var.bucket_name
}

resource "aws_iam_role" "example_lambda" {
  name = "example_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "example_lambda_role_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.example_lambda.name
}

resource "aws_iam_role_policy_attachment" "example_lambda_role_s3" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
  role       = aws_iam_role.example_lambda.name
}

data "archive_file" "example_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/"
  output_path = "${path.module}/../lambda_files.zip"
}

resource "aws_lambda_function" "example_lambda" {
  filename      = data.archive_file.example_lambda.output_path
  function_name = "example_lambda"
  role          = aws_iam_role.example_lambda.arn
  handler       = "example_lambda.handler"
  runtime       = "python3.10"

  environment {
    variables = {
      BUCKET_NAME   = aws_s3_bucket.example_bucket.id
      BUCKET_REGION = var.region
    }
  }
}

resource "aws_lambda_function_url" "example_lambda" {
  function_name      = aws_lambda_function.example_lambda.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = true
    allow_origins     = ["*"]
    allow_methods     = ["*"]
    allow_headers     = ["date", "keep-alive"]
    expose_headers    = ["keep-alive", "date"]
    max_age           = 86400
  }
}

output "example_lambda" {
  value = aws_lambda_function_url.example_lambda.function_url
}