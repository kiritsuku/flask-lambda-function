module "table_user" {
  source  = "terraform-aws-modules/dynamodb-table/aws"
  version = "3.1.1"

  name      = "${var.stack_name}-user-v1"
  hash_key  = "userId"

  attributes = [
    {
      name = "userId"
      type = "S"
    },
    {
      name = "email"
      type = "S"
    },
  ]

  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5

  global_secondary_indexes = [
    {
      name               = "email-index"
      hash_key           = "email"
      projection_type    = "KEYS_ONLY"
      read_capacity      = 5
      write_capacity     = 5
    },
  ]

  tags = local.tags
}
