# Package Lambda code into a zip
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda_function.py"
  output_path = "${path.module}/function.zip"
}

# Create Lambda function with existing role
resource "aws_lambda_function" "audit_afs_eng_lambda" {
  function_name = "audit-afs-eng-lambda_function"
  runtime       = "python3.13"
  role          = "arn:aws:iam::774305593404:role/audit-afs-eng"
  handler       = "lambda_function.lambda_handler"
  filename      = data.archive_file.lambda_zip.output_path
}
