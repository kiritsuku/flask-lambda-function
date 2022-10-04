module "python_lambda_layer" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.0.0"

  create_layer = true

  layer_name               = "${var.stack_name}-python-lambda-layer"
  compatible_runtimes      = ["python3.9"]
  compatible_architectures = ["x86_64"]

  source_path = "../python-lamdba-layer/__pycache__/lambda-layer"

  tags = local.tags
}

