#!/usr/bin/env python3
"""
Create a Terraform project for AWS EKS (Elastic Kubernetes Service)
"""
import os
import sys

def create_eks_project(project_name):
    """Create a complete Terraform EKS project structure"""
    
    # Create project directory
    os.makedirs(project_name, exist_ok=True)
    os.chdir(project_name)
    
    # Create main.tf
    main_tf = """# AWS EKS Terraform Configuration
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC Module
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = var.vpc_cidr

  azs             = slice(data.aws_availability_zones.available.names, 0, 3)
  private_subnets = [for k, v in slice(data.aws_availability_zones.available.names, 0, 3) : cidrsubnet(var.vpc_cidr, 4, k)]
  public_subnets  = [for k, v in slice(data.aws_availability_zones.available.names, 0, 3) : cidrsubnet(var.vpc_cidr, 8, k + 48)]

  enable_nat_gateway   = true
  single_nat_gateway   = var.single_nat_gateway
  enable_dns_hostnames = true
  enable_dns_support   = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.cluster_name}-vpc"
    }
  )
}

# EKS Module
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version

  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.private_subnets
  cluster_endpoint_public_access = true

  # EKS Managed Node Group(s)
  eks_managed_node_group_defaults = {
    ami_type       = "AL2_x86_64"
    instance_types = [var.instance_type]
    
    attach_cluster_primary_security_group = true
  }

  eks_managed_node_groups = {
    default = {
      name = "${var.cluster_name}-node-group"

      min_size     = var.min_nodes
      max_size     = var.max_nodes
      desired_size = var.desired_nodes

      instance_types = [var.instance_type]
      capacity_type  = var.capacity_type

      labels = {
        Environment = var.environment
      }

      update_config = {
        max_unavailable_percentage = 33
      }

      tags = merge(
        var.tags,
        {
          NodeGroup = "default"
        }
      )
    }
  }

  # Cluster access entry
  enable_cluster_creator_admin_permissions = true

  tags = var.tags
}

# Outputs for kubectl configuration
data "aws_eks_cluster_auth" "cluster" {
  name = module.eks.cluster_name
}
"""
    
    with open("main.tf", "w") as f:
        f.write(main_tf)
    
    # Create variables.tf
    variables_tf = """# AWS Region
variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}

# Cluster Configuration
variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "my-eks-cluster"
}

variable "kubernetes_version" {
  description = "Kubernetes version to use for the EKS cluster"
  type        = string
  default     = "1.28"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "development"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "single_nat_gateway" {
  description = "Use a single NAT gateway for cost savings"
  type        = bool
  default     = true
}

# Node Group Configuration
variable "instance_type" {
  description = "EC2 instance type for EKS nodes"
  type        = string
  default     = "t3.medium"
}

variable "min_nodes" {
  description = "Minimum number of nodes"
  type        = number
  default     = 1
}

variable "max_nodes" {
  description = "Maximum number of nodes"
  type        = number
  default     = 3
}

variable "desired_nodes" {
  description = "Desired number of nodes"
  type        = number
  default     = 2
}

variable "capacity_type" {
  description = "Capacity type (ON_DEMAND or SPOT)"
  type        = string
  default     = "ON_DEMAND"
}

# Tags
variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default = {
    Terraform   = "true"
    Environment = "development"
  }
}
"""
    
    with open("variables.tf", "w") as f:
        f.write(variables_tf)
    
    # Create outputs.tf
    outputs_tf = """# VPC Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnets" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnets
}

# EKS Cluster Outputs
output "cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "cluster_name" {
  description = "Kubernetes Cluster Name"
  value       = module.eks.cluster_name
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

# Node Group Outputs
output "node_group_id" {
  description = "EKS node group ID"
  value       = [for ng in module.eks.eks_managed_node_groups : ng.node_group_id]
}

output "node_group_status" {
  description = "Status of the EKS node group"
  value       = [for ng in module.eks.eks_managed_node_groups : ng.node_group_status]
}

# Kubectl Configuration
output "kubectl_config" {
  description = "kubectl config as generated by the module"
  value       = <<-EOT
    Run the following command to configure kubectl:
    
    aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}
    
    Verify the connection:
    kubectl get nodes
  EOT
}

output "region" {
  description = "AWS region"
  value       = var.aws_region
}
"""
    
    with open("outputs.tf", "w") as f:
        f.write(outputs_tf)
    
    # Create terraform.tfvars example
    tfvars = """# Example terraform.tfvars - Copy and customize as needed
# aws_region       = "us-west-2"
# cluster_name     = "my-eks-cluster"
# kubernetes_version = "1.28"
# environment      = "development"
# instance_type    = "t3.medium"
# min_nodes        = 1
# max_nodes        = 3
# desired_nodes    = 2
# capacity_type    = "ON_DEMAND"
"""
    
    with open("terraform.tfvars.example", "w") as f:
        f.write(tfvars)
    
    # Create README.md
    readme = f"""# AWS EKS Terraform Configuration

This Terraform configuration creates a production-ready AWS EKS (Elastic Kubernetes Service) cluster with:

- VPC with public and private subnets across multiple availability zones
- EKS cluster with configurable Kubernetes version
- Managed node group with auto-scaling
- Proper security groups and IAM roles
- Network configuration optimized for Kubernetes

## Prerequisites

1. **AWS CLI** installed and configured
2. **Terraform** (version >= 1.0)
3. **kubectl** for cluster management
4. AWS credentials with appropriate permissions

## Quick Start

### 1. Configure Variables

Copy and customize the example variables:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your settings:

```hcl
aws_region         = "us-west-2"
cluster_name       = "my-production-cluster"
kubernetes_version = "1.28"
environment        = "production"
instance_type      = "t3.large"
min_nodes          = 2
max_nodes          = 5
desired_nodes      = 3
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Review the Plan

```bash
terraform plan
```

### 4. Deploy the Cluster

```bash
terraform apply
```

This will take approximately 10-15 minutes to complete.

### 5. Configure kubectl

After deployment, configure kubectl to connect to your cluster:

```bash
aws eks update-kubeconfig --region us-west-2 --name my-eks-cluster
```

### 6. Verify the Cluster

```bash
kubectl get nodes
kubectl get pods -A
```

## Configuration Options

### Instance Types

- **Development**: `t3.medium` (2 vCPU, 4 GB RAM)
- **Production**: `t3.large` or `t3.xlarge`
- **High Performance**: `c5.xlarge` or `c5.2xlarge`

### Capacity Types

- **ON_DEMAND**: Guaranteed capacity (default)
- **SPOT**: Cost-optimized, subject to interruption

### Cost Optimization

For development environments, enable single NAT gateway:

```hcl
single_nat_gateway = true
```

## Outputs

After deployment, Terraform provides:

- **cluster_endpoint**: API server endpoint
- **cluster_name**: Name of the EKS cluster
- **kubectl_config**: Instructions to configure kubectl
- **vpc_id**: VPC ID
- **node_group_id**: Managed node group ID

View outputs:

```bash
terraform output
```

## Deploying Applications

### Deploy a sample application:

```bash
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --port=80 --type=LoadBalancer
kubectl get services
```

## Monitoring and Management

### View cluster status:

```bash
kubectl cluster-info
kubectl get nodes
kubectl get pods --all-namespaces
```

### Scale node group:

Update `desired_nodes` in `terraform.tfvars` and run:

```bash
terraform apply
```

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will permanently delete your cluster and all associated resources.

## Security Best Practices

1. Enable pod security policies
2. Use IAM roles for service accounts (IRSA)
3. Enable cluster encryption
4. Use private endpoints for production
5. Implement network policies
6. Enable audit logging

## Troubleshooting

### Issue: kubectl cannot connect

**Solution**: Update kubeconfig:
```bash
aws eks update-kubeconfig --region <region> --name <cluster-name>
```

### Issue: Nodes not joining cluster

**Solution**: Check security groups and IAM roles:
```bash
terraform output
aws eks describe-cluster --name <cluster-name>
```

### Issue: Terraform timeout

**Solution**: EKS provisioning can take 10-15 minutes. If it fails, check AWS console for errors.

## Additional Resources

- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [EKS Best Practices Guide](https://aws.github.io/aws-eks-best-practices/)

## Support

For issues or questions:
1. Check Terraform output for errors
2. Review AWS CloudWatch logs
3. Check EKS cluster events in AWS Console
"""
    
    with open("README.md", "w") as f:
        f.write(readme)
    
    # Create .gitignore
    gitignore = """# Terraform files
.terraform/
*.tfstate
*.tfstate.*
terraform.tfvars
.terraform.lock.hcl

# Sensitive files
*.pem
*.key

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore)
    
    print(f"[OK] Created AWS EKS Terraform project: {project_name}")
    print(f"[OK] Files created: main.tf, variables.tf, outputs.tf, terraform.tfvars.example, README.md")
    print(f"\nNext steps:")
    print(f"1. cd {project_name}")
    print(f"2. Configure AWS credentials: aws configure")
    print(f"3. Copy terraform.tfvars.example to terraform.tfvars and customize")
    print(f"4. terraform init")
    print(f"5. terraform plan")
    print(f"6. terraform apply")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_terraform_eks.py <project_name>")
        sys.exit(1)
    
    project_name = sys.argv[1]
    create_eks_project(project_name)
