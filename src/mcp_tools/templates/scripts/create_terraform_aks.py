#!/usr/bin/env python3
"""
Create a Terraform project for Azure AKS (Azure Kubernetes Service)
"""
import os
import sys

def create_aks_project(project_name):
    """Create a complete Terraform AKS project structure"""
    
    # Create project directory
    os.makedirs(project_name, exist_ok=True)
    os.chdir(project_name)
    
    # Create main.tf
    main_tf = """# Azure AKS Terraform Configuration
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Resource Group
resource "azurerm_resource_group" "aks" {
  name     = "${var.cluster_name}-rg"
  location = var.location

  tags = var.tags
}

# Virtual Network
resource "azurerm_virtual_network" "aks" {
  name                = "${var.cluster_name}-vnet"
  location            = azurerm_resource_group.aks.location
  resource_group_name = azurerm_resource_group.aks.name
  address_space       = [var.vnet_cidr]

  tags = var.tags
}

# Subnet for AKS
resource "azurerm_subnet" "aks" {
  name                 = "${var.cluster_name}-subnet"
  resource_group_name  = azurerm_resource_group.aks.name
  virtual_network_name = azurerm_virtual_network.aks.name
  address_prefixes     = [var.subnet_cidr]
}

# Log Analytics Workspace for monitoring
resource "azurerm_log_analytics_workspace" "aks" {
  name                = "${var.cluster_name}-workspace"
  location            = azurerm_resource_group.aks.location
  resource_group_name = azurerm_resource_group.aks.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = var.tags
}

resource "azurerm_log_analytics_solution" "aks" {
  solution_name         = "ContainerInsights"
  location              = azurerm_resource_group.aks.location
  resource_group_name   = azurerm_resource_group.aks.name
  workspace_resource_id = azurerm_log_analytics_workspace.aks.id
  workspace_name        = azurerm_log_analytics_workspace.aks.name

  plan {
    publisher = "Microsoft"
    product   = "OMSGallery/ContainerInsights"
  }

  tags = var.tags
}

# AKS Cluster
resource "azurerm_kubernetes_cluster" "aks" {
  name                = var.cluster_name
  location            = azurerm_resource_group.aks.location
  resource_group_name = azurerm_resource_group.aks.name
  dns_prefix          = var.cluster_name
  kubernetes_version  = var.kubernetes_version

  default_node_pool {
    name                = "default"
    node_count          = var.node_count
    vm_size             = var.vm_size
    vnet_subnet_id      = azurerm_subnet.aks.id
    enable_auto_scaling = var.enable_auto_scaling
    min_count           = var.enable_auto_scaling ? var.min_nodes : null
    max_count           = var.enable_auto_scaling ? var.max_nodes : null
    os_disk_size_gb     = 30
    type                = "VirtualMachineScaleSets"

    upgrade_settings {
      max_surge = "10%"
    }

    tags = var.tags
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "azure"
    network_policy    = "azure"
    load_balancer_sku = "standard"
    service_cidr      = "10.1.0.0/16"
    dns_service_ip    = "10.1.0.10"
  }

  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.aks.id
  }

  azure_policy_enabled = true

  tags = var.tags
}

# Role Assignment for AKS to access ACR (if needed)
resource "azurerm_role_assignment" "aks_acr" {
  count                = var.enable_acr_pull ? 1 : 0
  principal_id         = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id
  role_definition_name = "AcrPull"
  scope                = var.acr_id
  skip_service_principal_aad_check = true
}
"""
    
    with open("main.tf", "w") as f:
        f.write(main_tf)
    
    # Create variables.tf
    variables_tf = """# Azure Configuration
variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "East US"
}

# Cluster Configuration
variable "cluster_name" {
  description = "Name of the AKS cluster"
  type        = string
  default     = "my-aks-cluster"
}

variable "kubernetes_version" {
  description = "Kubernetes version to use for the AKS cluster"
  type        = string
  default     = "1.28.0"
}

# Network Configuration
variable "vnet_cidr" {
  description = "CIDR block for Virtual Network"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  description = "CIDR block for AKS subnet"
  type        = string
  default     = "10.0.1.0/24"
}

# Node Pool Configuration
variable "vm_size" {
  description = "Size of the Virtual Machine"
  type        = string
  default     = "Standard_D2s_v3"
}

variable "node_count" {
  description = "Initial number of nodes"
  type        = number
  default     = 2
}

variable "enable_auto_scaling" {
  description = "Enable auto-scaling for node pool"
  type        = bool
  default     = true
}

variable "min_nodes" {
  description = "Minimum number of nodes (if auto-scaling enabled)"
  type        = number
  default     = 1
}

variable "max_nodes" {
  description = "Maximum number of nodes (if auto-scaling enabled)"
  type        = number
  default     = 5
}

# Container Registry
variable "enable_acr_pull" {
  description = "Enable ACR pull role assignment"
  type        = bool
  default     = false
}

variable "acr_id" {
  description = "Azure Container Registry ID (if enable_acr_pull is true)"
  type        = string
  default     = ""
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
    outputs_tf = """# Resource Group Outputs
output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.aks.name
}

output "resource_group_location" {
  description = "Resource group location"
  value       = azurerm_resource_group.aks.location
}

# Network Outputs
output "vnet_id" {
  description = "Virtual Network ID"
  value       = azurerm_virtual_network.aks.id
}

output "subnet_id" {
  description = "Subnet ID"
  value       = azurerm_subnet.aks.id
}

# AKS Cluster Outputs
output "cluster_id" {
  description = "AKS cluster ID"
  value       = azurerm_kubernetes_cluster.aks.id
}

output "cluster_name" {
  description = "AKS cluster name"
  value       = azurerm_kubernetes_cluster.aks.name
}

output "cluster_fqdn" {
  description = "Fully Qualified Domain Name of the AKS cluster"
  value       = azurerm_kubernetes_cluster.aks.fqdn
}

output "kube_config" {
  description = "Kubernetes config to connect to the AKS cluster"
  value       = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive   = true
}

output "client_certificate" {
  description = "Client certificate for cluster authentication"
  value       = azurerm_kubernetes_cluster.aks.kube_config[0].client_certificate
  sensitive   = true
}

output "client_key" {
  description = "Client key for cluster authentication"
  value       = azurerm_kubernetes_cluster.aks.kube_config[0].client_key
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "Cluster CA certificate"
  value       = azurerm_kubernetes_cluster.aks.kube_config[0].cluster_ca_certificate
  sensitive   = true
}

output "host" {
  description = "Kubernetes host"
  value       = azurerm_kubernetes_cluster.aks.kube_config[0].host
  sensitive   = true
}

output "node_resource_group" {
  description = "Auto-generated Resource Group for AKS nodes"
  value       = azurerm_kubernetes_cluster.aks.node_resource_group
}

# Monitoring Outputs
output "log_analytics_workspace_id" {
  description = "Log Analytics Workspace ID"
  value       = azurerm_log_analytics_workspace.aks.id
}

# Kubectl Configuration
output "kubectl_config" {
  description = "kubectl config instructions"
  value       = <<-EOT
    Run the following command to configure kubectl:
    
    az aks get-credentials --resource-group ${azurerm_resource_group.aks.name} --name ${azurerm_kubernetes_cluster.aks.name}
    
    Verify the connection:
    kubectl get nodes
  EOT
}
"""
    
    with open("outputs.tf", "w") as f:
        f.write(outputs_tf)
    
    # Create terraform.tfvars example
    tfvars = """# Example terraform.tfvars - Copy and customize as needed
# location           = "East US"
# cluster_name       = "my-aks-cluster"
# kubernetes_version = "1.28.0"
# vm_size           = "Standard_D2s_v3"
# node_count        = 2
# enable_auto_scaling = true
# min_nodes         = 1
# max_nodes         = 5
"""
    
    with open("terraform.tfvars.example", "w") as f:
        f.write(tfvars)
    
    # Create README.md
    readme = f"""# Azure AKS Terraform Configuration

This Terraform configuration creates a production-ready Azure Kubernetes Service (AKS) cluster with:

- Virtual Network with dedicated subnet
- AKS cluster with configurable Kubernetes version
- Auto-scaling node pool
- Azure Monitor integration for logging
- Azure Policy for governance
- System-assigned managed identity

## Prerequisites

1. **Azure CLI** installed and configured
2. **Terraform** (version >= 1.0)
3. **kubectl** for cluster management
4. Azure subscription with appropriate permissions

## Quick Start

### 1. Login to Azure

```bash
az login
az account set --subscription "<your-subscription-id>"
```

### 2. Configure Variables

Copy and customize the example variables:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
location            = "East US"
cluster_name        = "my-production-cluster"
kubernetes_version  = "1.28.0"
vm_size            = "Standard_D4s_v3"
node_count         = 3
enable_auto_scaling = true
min_nodes          = 2
max_nodes          = 10
```

### 3. Initialize Terraform

```bash
terraform init
```

### 4. Review the Plan

```bash
terraform plan
```

### 5. Deploy the Cluster

```bash
terraform apply
```

Deployment takes approximately 5-10 minutes.

### 6. Configure kubectl

```bash
az aks get-credentials --resource-group my-aks-cluster-rg --name my-aks-cluster
```

### 7. Verify the Cluster

```bash
kubectl get nodes
kubectl get pods -A
```

## Configuration Options

### VM Sizes

- **Development**: `Standard_D2s_v3` (2 vCPU, 8 GB RAM)
- **Production**: `Standard_D4s_v3` (4 vCPU, 16 GB RAM)
- **High Performance**: `Standard_D8s_v3` or `Standard_F8s_v2`

[Azure VM Sizes Documentation](https://docs.microsoft.com/en-us/azure/virtual-machines/sizes)

### Available Azure Regions

```bash
az account list-locations -o table
```

Common regions:
- East US
- West US 2
- West Europe
- Southeast Asia

### Auto-scaling

Enable auto-scaling for dynamic workloads:

```hcl
enable_auto_scaling = true
min_nodes          = 2
max_nodes          = 10
```

## Integration with Azure Container Registry

To enable pulling images from Azure Container Registry:

1. Create an ACR:
```bash
az acr create --resource-group my-rg --name myacr --sku Standard
```

2. Get ACR ID:
```bash
az acr show --name myacr --query id --output tsv
```

3. Update `terraform.tfvars`:
```hcl
enable_acr_pull = true
acr_id          = "/subscriptions/.../resourceGroups/.../providers/Microsoft.ContainerRegistry/registries/myacr"
```

## Outputs

After deployment:

```bash
terraform output
terraform output -raw kube_config > ~/.kube/aks-config
```

Key outputs:
- **cluster_name**: AKS cluster name
- **cluster_fqdn**: Cluster FQDN
- **resource_group_name**: Resource group name
- **kubectl_config**: Configuration instructions

## Deploying Applications

### Deploy sample application:

```bash
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --port=80 --type=LoadBalancer
kubectl get services
```

### Using Azure Container Registry:

```bash
az acr login --name myacr
docker tag myapp:latest myacr.azurecr.io/myapp:latest
docker push myacr.azurecr.io/myapp:latest
kubectl create deployment myapp --image=myacr.azurecr.io/myapp:latest
```

## Monitoring and Management

### View cluster status:

```bash
kubectl cluster-info
kubectl get nodes
kubectl top nodes
```

### Azure Monitor:

View logs in Azure Portal:
1. Navigate to your AKS cluster
2. Click "Logs" under Monitoring
3. Run queries on ContainerLog, KubeEvents, etc.

### Scale cluster:

Update `node_count` in `terraform.tfvars`:

```bash
terraform apply
```

Or use Azure CLI:

```bash
az aks scale --resource-group my-aks-cluster-rg --name my-aks-cluster --node-count 5
```

## Upgrading Kubernetes Version

Check available versions:

```bash
az aks get-upgrades --resource-group my-aks-cluster-rg --name my-aks-cluster --output table
```

Update `kubernetes_version` in `terraform.tfvars` and apply:

```bash
terraform apply
```

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This permanently deletes your cluster and all resources.

## Security Best Practices

1. Enable Azure Policy for governance
2. Use Azure AD integration for RBAC
3. Enable network policies
4. Use pod security policies
5. Enable Azure Defender for Kubernetes
6. Implement Azure Key Vault integration
7. Use managed identities for applications

## Cost Optimization

1. Use auto-scaling to match demand
2. Consider spot VMs for non-critical workloads
3. Right-size VM selections
4. Use Azure Hybrid Benefit if applicable
5. Monitor and optimize with Azure Cost Management

## Troubleshooting

### Issue: kubectl cannot connect

**Solution**: Refresh credentials:
```bash
az aks get-credentials --resource-group <rg-name> --name <cluster-name> --overwrite-existing
```

### Issue: Nodes not ready

**Solution**: Check node status and logs:
```bash
kubectl describe nodes
kubectl get events
```

### Issue: Terraform state locked

**Solution**: Check Azure Storage for state lock and remove if stale.

## Additional Resources

- [Azure AKS Documentation](https://docs.microsoft.com/en-us/azure/aks/)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [AKS Best Practices](https://docs.microsoft.com/en-us/azure/aks/best-practices)

## Support

For issues:
1. Check Terraform output for errors
2. Review Azure Activity Log
3. Check AKS diagnostics in Azure Portal
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
kubeconfig

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore)
    
    print(f"[OK] Created Azure AKS Terraform project: {project_name}")
    print(f"[OK] Files created: main.tf, variables.tf, outputs.tf, terraform.tfvars.example, README.md")
    print(f"\nNext steps:")
    print(f"1. cd {project_name}")
    print(f"2. Login to Azure: az login")
    print(f"3. Copy terraform.tfvars.example to terraform.tfvars and customize")
    print(f"4. terraform init")
    print(f"5. terraform plan")
    print(f"6. terraform apply")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_terraform_aks.py <project_name>")
        sys.exit(1)
    
    project_name = sys.argv[1]
    create_aks_project(project_name)
