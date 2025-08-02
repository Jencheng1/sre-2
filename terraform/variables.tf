variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"  # Changed to us-east-1
}

variable "environment" {
  description = "Environment name (e.g., dev, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "sre-copilot"
} 