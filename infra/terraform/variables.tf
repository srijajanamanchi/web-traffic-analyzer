variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "production"
}

variable "instance_type" {
  description = "EC2 instance size (t3.micro is AWS Free Tier eligible)"
  type        = string
  default     = "t3.micro"
}

variable "ssh_key_name" {
  description = "Name of the existing AWS EC2 Key Pair for SSH access"
  type        = string
  default     = "traffic-analyzer-key"
}

variable "admin_ip" {
  description = "CIDR block permitted for SSH access (default to admin workstation IP)"
  type        = string
  default     = "0.0.0.0/0"
}
