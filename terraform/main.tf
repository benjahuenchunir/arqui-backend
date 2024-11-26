provider "aws" {
  region = var.region
}

# ==================== IAM Roles and Policies ====================

# define a role, which will be assumed by CodeDeploy service
resource "aws_iam_role" "codedeploy_role" {
  name = "appexample-dev-codedeploy-role-us-east-1"
  assume_role_policy = jsonencode({
    Version: "2012-10-17",
    Statement: [
      {
        "Sid": "",
        "Effect": "Allow",
        "Principal": {
          "Service": "codedeploy.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "codedeploy_role_policy_attachment" {
  role       = aws_iam_role.codedeploy_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSCodeDeployRole"
}

# define a role, which will be assumed by a codedeploy app inside an EC2-instance during a deployment
resource "aws_iam_role" "codedeploy_ec2_role" {
  name = "appexample-dev-EC2-codedeploy-role-us-east-1"
  assume_role_policy = jsonencode({
    Version: "2012-10-17",
    Statement: [
      {
        "Sid": "",
        "Effect": "Allow",
        "Principal": {
          "Service": "ec2.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  })
}

# define a policy, which allows access to S3 bucket with artifacts
resource "aws_iam_policy" "codedeploy_ec2_to_s3_policy" {
  name        = "appexample-dev-EC2-codedeploy-to-S3-policy-us-east-1"
  description = "Allow access to S3 bucket with artifacts"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:Get*", "s3:List*"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_codedeploy_ec2_to_s3_policy" {
  role       = aws_iam_role.codedeploy_ec2_role.name
  policy_arn = aws_iam_policy.codedeploy_ec2_to_s3_policy.arn
}

# attach the policy to the role
resource "aws_iam_role_policy_attachment" "attach_ssminstancecore_policy" {
  role       = aws_iam_role.codedeploy_ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# define an instance profile, which will be used by an EC2-instance
resource "aws_iam_instance_profile" "attach" {
  name = "appexample-dev-EC2-codedeploy-instanceprofile-us-east-1"
  role = aws_iam_role.codedeploy_ec2_role.name
}

# ==================== S3-Buckets ====================

# define a bucket for storing build artifacts
resource "aws_s3_bucket" "build_artifacts_bucket" {
  bucket = "iic2173-back-terraform"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "build_artifacts_bucket_versioning" {
  bucket = aws_s3_bucket.build_artifacts_bucket.id
  versioning_configuration {
    status = "Disabled"
  }
}

# ==================== Compute Resources ====================

resource "aws_security_group" "application_sg" {
  name        = "application-sg"
  description = "application-sg"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# define a launch template, which will be used by an autoscaling group
resource "aws_launch_template" "auto_scaling_launch_template_test" {
  name_prefix   = "auto_scaling_launch_template_test"
  iam_instance_profile {
    name = aws_iam_instance_profile.attach.name
  }
  image_id      = var.ami
  instance_type = "t2.micro"
  vpc_security_group_ids = [aws_security_group.application_sg.id]
  key_name = var.key_name

  user_data = filebase64("userdata.sh")
}

# define an autoscaling group
resource "aws_autoscaling_group" "autoscaling_group" {
  name                      = "appexample-dev-autoscaling-group-us-east-1"
  desired_capacity          = 1
  max_size                  = 1
  min_size                  = 1
  health_check_grace_period = 300
  health_check_type         = "EC2"
  force_delete              = true
  availability_zones = ["us-east-1a"]
  launch_template {
    id      = aws_launch_template.auto_scaling_launch_template_test.id
    version = "$Latest"
  }
}

# ==================== Codedeploy ====================

# define a CodeDeploy application
resource "aws_codedeploy_app" "codedeploy_app" {
  name = "iic2173-app-terraform"
  compute_platform = "Server"
}

# define a CodeDeploy deployment group
resource "aws_codedeploy_deployment_group" "deployment_group" {
  app_name              = aws_codedeploy_app.codedeploy_app.name
  deployment_group_name = "group-iic2173-terraform"
  service_role_arn      = aws_iam_role.codedeploy_role.arn
  deployment_config_name = "CodeDeployDefault.AllAtOnce"
  autoscaling_groups = [aws_autoscaling_group.autoscaling_group.name]
  auto_rollback_configuration {
    enabled = true
    events  = ["DEPLOYMENT_FAILURE"]
  }
}

resource "null_resource" "deploy" {
  depends_on = [
    aws_codedeploy_app.codedeploy_app,
    aws_codedeploy_deployment_group.deployment_group,
    aws_s3_bucket.build_artifacts_bucket
  ]

  provisioner "local-exec" {
    command = "bash deploy.sh"
  }
}

# ==================== API Gateway ====================

# Fetch the instance IDs of the instances created by the Auto Scaling group
data "aws_instances" "autoscaling_instances" {
  filter {
    name   = "tag:aws:autoscaling:groupName"
    values = [aws_autoscaling_group.autoscaling_group.name]
  }
  filter {
    name   = "instance-state-name"
    values = ["running"]
  }
}

# Fetch the details of the first instance
data "aws_instance" "autoscaling_instance" {
  instance_id = data.aws_instances.autoscaling_instances.ids[0]
}

# Define the API Gateway
resource "aws_api_gateway_rest_api" "api" {
  name        = "api-terraform"
  description = "Example API Gateway"
}

# Define a resource in the API Gateway for /example
resource "aws_api_gateway_resource" "example_resource" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "example"
}

# Define a GET method for the /example resource
resource "aws_api_gateway_method" "example_get" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.example_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

# Define the integration for the GET method on /example
resource "aws_api_gateway_integration" "example_get_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.example_resource.id
  http_method = aws_api_gateway_method.example_get.http_method
  type        = "MOCK"
}

# Define a resource in the API Gateway for /fixtures
resource "aws_api_gateway_resource" "fixtures_resource" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "fixtures"
}

# Define a GET method for the /fixtures resource
resource "aws_api_gateway_method" "fixtures_get" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.fixtures_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

# Modify the integration for the GET method on /fixtures
resource "aws_api_gateway_integration" "fixtures_get_integration" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.fixtures_resource.id
  http_method             = aws_api_gateway_method.fixtures_get.http_method
  type                    = "HTTP"
  integration_http_method = "GET"
  uri                     = "http://${data.aws_instance.autoscaling_instance.public_dns}/fixtures"
}

# Define a deployment for the API Gateway
resource "aws_api_gateway_deployment" "example_deployment" {
  depends_on = [
    aws_api_gateway_integration.example_get_integration,
    aws_api_gateway_integration.fixtures_get_integration
  ]
  rest_api_id = aws_api_gateway_rest_api.api.id
}

# Define a stage for the API Gateway
resource "aws_api_gateway_stage" "example_stage" {
  deployment_id = aws_api_gateway_deployment.example_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.api.id
  stage_name    = "dev"
}

output "instance_public_dns" {
  value       = data.aws_instance.autoscaling_instance.public_dns
  description = "The public DNS of the instance created by the Auto Scaling group"
}