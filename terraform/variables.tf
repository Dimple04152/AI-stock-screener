variable "aws_region" {
  default = "us-east-1"
}

variable "instance_type" {
  default = "t3.small" # 2GB RAM - recommended for stable K8s clusters
}

variable "key_name" {
  description = "Name of the AWS key pair"
  type        = string
}
