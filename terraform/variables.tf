variable "aws_region" {
  default = "us-east-1"
}

variable "instance_type" {
  default = "m7i-flex.large" # 8GB RAM - high performance for K8s and CI/CD
}

variable "key_name" {
  description = "Name of the AWS key pair"
  type        = string
}
