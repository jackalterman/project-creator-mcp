#!/usr/bin/env python3
"""
Create a Terraform project for GCP GKE (Google Kubernetes Engine)
"""
import os
import sys

def create_gke_project(project_name):
    """Create a complete Terraform GKE project structure"""
    
    # Create project directory
    os.makedirs(project_name, exist_ok=True)
    os.chdir(project_name)
    
    # Create main.tf
    main_tf = """# Google Cloud GKE Terraform Configuration
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "${var.cluster_name}-vpc"
  auto_create_subnetworks = false
}

# Subnet
resource "google_compute_subnetwork" "subnet" {
  name          = "${var.cluster_name}-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = var.pods_cidr
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = var.services_cidr
  }
}

# Cloud Router for NAT
resource "google_compute_router" "router" {
  name    = "${var.cluster_name}-router"
  region  = var.region
  network = google_compute_network.vpc.id
}

# Cloud NAT for private nodes
resource "google_compute_router_nat" "nat" {
  name                               = "${var.cluster_name}-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# GKE Cluster
resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.regional ? var.region : "${var.region}-a"

  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name

  # Enable Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # IP allocation for pods and services
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  # Network policy
  network_policy {
    enabled = true
    # Recommended provider: 'CALICO'
    provider = "CALICO"
  }

  # Enable binary authorization
  binary_authorization {
    evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
  }

  # Maintenance window
  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00"
    }
  }

  # Addons
  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
    network_policy_config {
      disabled = false
    }
    gcp_filestore_csi_driver_config {
      enabled = true
    }
  }

  # Enable shielded nodes
  enable_shielded_nodes = true

  # Release channel
  release_channel {
    channel = var.release_channel
  }

  # Master authorized networks (optional)
  dynamic "master_authorized_networks_config" {
    for_each = var.master_authorized_networks != null ? [1] : []
    content {
      dynamic "cidr_blocks" {
        for_each = var.master_authorized_networks
        content {
          cidr_block   = cidr_blocks.value.cidr_block
          display_name = cidr_blocks.value.display_name
        }
      }
    }
  }

  # Private cluster config
  private_cluster_config {
    enable_private_nodes    = var.enable_private_nodes
    enable_private_endpoint = var.enable_private_endpoint
    master_ipv4_cidr_block  = var.master_ipv4_cidr_block
  }

  # Logging and monitoring
  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"

  # Resource labels
  resource_labels = var.labels
}

# Node Pool
resource "google_container_node_pool" "primary_nodes" {
  name       = "${var.cluster_name}-node-pool"
  location   = google_container_cluster.primary.location
  cluster    = google_container_cluster.primary.name
  node_count = var.node_count

  autoscaling {
    min_node_count = var.min_nodes
    max_node_count = var.max_nodes
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    # Use a secure, maintained GKE node image
    image_type   = "COS_CONTAINERD"
    preemptible  = var.preemptible
    machine_type = var.machine_type
    disk_size_gb = var.disk_size_gb
    disk_type    = "pd-standard"

    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    service_account = google_service_account.gke_sa.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = var.labels

    tags = ["gke-node", "${var.cluster_name}-node"]

    metadata = {
      disable-legacy-endpoints = "true"
    }

    # Shielded instance config
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    # Workload metadata config
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }
}

# Service Account for GKE nodes
resource "google_service_account" "gke_sa" {
  account_id   = "${var.cluster_name}-sa"
  display_name = "Service Account for ${var.cluster_name} GKE nodes"
}

# IAM binding for logging
resource "google_project_iam_member" "gke_sa_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gke_sa.email}"
}

# IAM binding for monitoring
resource "google_project_iam_member" "gke_sa_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.gke_sa.email}"
}

# IAM binding for monitoring viewer
resource "google_project_iam_member" "gke_sa_monitoring_viewer" {
  project = var.project_id
  role    = "roles/monitoring.viewer"
  member  = "serviceAccount:${google_service_account.gke_sa.email}"
}

# IAM binding for resource metadata writer
resource "google_project_iam_member" "gke_sa_resource_metadata" {
  project = var.project_id
  role    = "roles/stackdriver.resourceMetadata.writer"
  member  = "serviceAccount:${google_service_account.gke_sa.email}"
}
"""
    
    with open("main.tf", "w") as f:
        f.write(main_tf)
    
    # Create variables.tf
    variables_tf = """# GCP Project Configuration
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "regional" {
  description = "Create a regional cluster (true) or zonal cluster (false)"
  type        = bool
  default     = true
}

# Cluster Configuration
variable "cluster_name" {
  description = "Name of the GKE cluster"
  type        = string
  default     = "my-gke-cluster"
}

variable "release_channel" {
  description = "GKE release channel (RAPID, REGULAR, STABLE)"
  type        = string
  default     = "REGULAR"
}

# Network Configuration
variable "subnet_cidr" {
  description = "CIDR range for the subnet"
  type        = string
  default     = "10.0.0.0/24"
}

variable "pods_cidr" {
  description = "CIDR range for pods"
  type        = string
  default     = "10.1.0.0/16"
}

variable "services_cidr" {
  description = "CIDR range for services"
  type        = string
  default     = "10.2.0.0/16"
}

# Private Cluster Configuration
variable "enable_private_nodes" {
  description = "Enable private nodes"
  type        = bool
  default     = true
}

variable "enable_private_endpoint" {
  description = "Enable private endpoint for the master"
  type        = bool
  default     = false
}

variable "master_ipv4_cidr_block" {
  description = "CIDR block for the master network"
  type        = string
  default     = "172.16.0.0/28"
}

variable "master_authorized_networks" {
  description = "List of master authorized networks"
  type = list(object({
    cidr_block   = string
    display_name = string
  }))
  default = null
}

# Node Pool Configuration
variable "machine_type" {
  description = "Machine type for nodes"
  type        = string
  default     = "e2-medium"
}

variable "node_count" {
  description = "Initial number of nodes per zone"
  type        = number
  default     = 1
}

variable "min_nodes" {
  description = "Minimum number of nodes per zone"
  type        = number
  default     = 1
}

variable "max_nodes" {
  description = "Maximum number of nodes per zone"
  type        = number
  default     = 3
}

variable "disk_size_gb" {
  description = "Disk size in GB for nodes"
  type        = number
  default     = 50
}

variable "preemptible" {
  description = "Use preemptible nodes for cost savings"
  type        = bool
  default     = false
}

# Labels
variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default = {
    terraform   = "true"
    environment = "development"
  }
}
"""
    
    with open("variables.tf", "w") as f:
        f.write(variables_tf)
    
    # Create outputs.tf
    outputs_tf = """# Network Outputs
output "network_name" {
  description = "VPC network name"
  value       = google_compute_network.vpc.name
}

output "subnet_name" {
  description = "Subnet name"
  value       = google_compute_subnetwork.subnet.name
}

# GKE Cluster Outputs
output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "cluster_location" {
  description = "GKE cluster location"
  value       = google_container_cluster.primary.location
}

output "cluster_id" {
  description = "GKE cluster ID"
  value       = google_container_cluster.primary.id
}

# Service Account Outputs
output "service_account_email" {
  description = "Service account email for GKE nodes"
  value       = google_service_account.gke_sa.email
}

# Node Pool Outputs
output "node_pool_name" {
  description = "Node pool name"
  value       = google_container_node_pool.primary_nodes.name
}

# Kubectl Configuration
output "kubectl_config" {
  description = "kubectl config instructions"
  value       = <<-EOT
    Run the following command to configure kubectl:
    
    gcloud container clusters get-credentials ${google_container_cluster.primary.name} --region ${var.region} --project ${var.project_id}
    
    Verify the connection:
    kubectl get nodes
  EOT
}

output "region" {
  description = "GCP region"
  value       = var.region
}

output "project_id" {
  description = "GCP project ID"
  value       = var.project_id
}
"""
    
    with open("outputs.tf", "w") as f:
        f.write(outputs_tf)
    
    # Create terraform.tfvars example
    tfvars = """# Example terraform.tfvars - Copy and customize as needed
# project_id          = "your-gcp-project-id"
# region              = "us-central1"
# cluster_name        = "my-gke-cluster"
# regional            = true
# machine_type        = "e2-medium"
# node_count          = 1
# min_nodes           = 1
# max_nodes           = 3
# enable_private_nodes = true
# preemptible         = false
"""
    
    with open("terraform.tfvars.example", "w") as f:
        f.write(tfvars)
    
    # Create README.md
    readme = f"""# Google Cloud GKE Terraform Configuration

This Terraform configuration creates a production-ready Google Kubernetes Engine (GKE) cluster with:

- Custom VPC network with secondary IP ranges for pods and services
- Regional or zonal GKE cluster
- Auto-scaling node pool
- Workload Identity enabled
- Private nodes with Cloud NAT
- Network policies enabled
- Shielded nodes for security
- Logging and monitoring integration
- Custom service account with minimal permissions

## Prerequisites

1. **Google Cloud SDK** installed and configured
2. **Terraform** (version >= 1.0)
3. **kubectl** for cluster management
4. GCP project with billing enabled

## Quick Start

### 1. Login to Google Cloud

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Enable Required APIs

```bash
gcloud services enable compute.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com
```

### 3. Configure Variables

Copy and customize the example variables:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
project_id           = "your-gcp-project-id"
region               = "us-central1"
cluster_name         = "my-production-cluster"
regional             = true
machine_type         = "e2-standard-4"
node_count           = 1
min_nodes            = 1
max_nodes            = 5
enable_private_nodes = true
```

### 4. Initialize Terraform

```bash
terraform init
```

### 5. Review the Plan

```bash
terraform plan
```

### 6. Deploy the Cluster

```bash
terraform apply
```

Deployment takes approximately 10-15 minutes.

### 7. Configure kubectl

```bash
gcloud container clusters get-credentials my-gke-cluster --region us-central1 --project YOUR_PROJECT_ID
```

### 8. Verify the Cluster

```bash
kubectl get nodes
kubectl get pods -A
kubectl cluster-info
```

## Configuration Options

### Machine Types

- **Development**: `e2-medium` (2 vCPU, 4 GB RAM)
- **Production**: `e2-standard-4` (4 vCPU, 16 GB RAM)
- **High Performance**: `n2-standard-8` or `c2-standard-8`

[GCP Machine Types Documentation](https://cloud.google.com/compute/docs/machine-types)

### Regions and Zones

View available regions:
```bash
gcloud compute regions list
```

Common regions:
- us-central1 (Iowa)
- us-east1 (South Carolina)
- europe-west1 (Belgium)
- asia-southeast1 (Singapore)

### Regional vs Zonal Clusters

**Regional Cluster** (recommended for production):
- High availability across multiple zones
- Automatic master failover
- Higher cost

```hcl
regional = true
```

**Zonal Cluster** (development):
- Lower cost
- Single zone deployment

```hcl
regional = false
```

### Preemptible Nodes

For non-critical workloads, use preemptible nodes for up to 80% cost savings:

```hcl
preemptible = true
```

## Private Cluster Configuration

### Private Nodes Only (Recommended)

```hcl
enable_private_nodes    = true
enable_private_endpoint = false
```

Nodes have private IPs but control plane is publicly accessible.

### Fully Private Cluster

```hcl
enable_private_nodes    = true
enable_private_endpoint = true
```

Requires VPN or Cloud Interconnect for access.

### Authorized Networks

Allow specific IP ranges to access the control plane:

```hcl
master_authorized_networks = [
  {{
    cidr_block   = "YOUR_IP/32"
    display_name = "My Office"
  }}
]
```

## Outputs

View all outputs:

```bash
terraform output
```

Key outputs:
- **cluster_name**: GKE cluster name
- **cluster_endpoint**: Cluster API endpoint
- **kubectl_config**: Configuration instructions

Get sensitive outputs:
```bash
terraform output -raw cluster_ca_certificate | base64 -d
```

## Workload Identity

Enable Workload Identity for pods to access GCP services:

```bash
# Create Kubernetes service account
kubectl create serviceaccount my-ksa -n default

# Create GCP service account
gcloud iam service-accounts create my-gsa

# Grant permissions to GCP SA
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \\
    --member "serviceAccount:my-gsa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \\
    --role "roles/storage.objectViewer"

# Bind KSA to GSA
gcloud iam service-accounts add-iam-policy-binding my-gsa@YOUR_PROJECT_ID.iam.gserviceaccount.com \\
    --role roles/iam.workloadIdentityUser \\
    --member "serviceAccount:YOUR_PROJECT_ID.svc.id.goog[default/my-ksa]"

# Annotate KSA
kubectl annotate serviceaccount my-ksa \\
    iam.gke.io/gcp-service-account=my-gsa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## Deploying Applications

### Deploy sample application:

```bash
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --port=80 --type=LoadBalancer
kubectl get services
```

### Using Google Container Registry:

```bash
gcloud auth configure-docker
docker tag myapp:latest gcr.io/YOUR_PROJECT_ID/myapp:latest
docker push gcr.io/YOUR_PROJECT_ID/myapp:latest
kubectl create deployment myapp --image=gcr.io/YOUR_PROJECT_ID/myapp:latest
```

## Monitoring and Logging

### View logs in Cloud Console:
1. Navigate to Kubernetes Engine > Workloads
2. Select your deployment
3. Click "Logs" tab

### Query logs with gcloud:

```bash
gcloud logging read "resource.type=k8s_cluster AND resource.labels.cluster_name=my-gke-cluster" --limit 50
```

### View metrics:

```bash
kubectl top nodes
kubectl top pods
```

## Upgrading

### Check available versions:

```bash
gcloud container get-server-config --region us-central1
```

### Upgrade control plane:

The cluster will auto-upgrade based on the release channel. To manually upgrade:

```bash
gcloud container clusters upgrade my-gke-cluster --master --region us-central1
```

### Upgrade node pool:

Node pools auto-upgrade by default. To manually upgrade:

```bash
gcloud container clusters upgrade my-gke-cluster --node-pool=my-gke-cluster-node-pool --region us-central1
```

## Scaling

### Scale node pool:

Update `node_count`, `min_nodes`, or `max_nodes` in `terraform.tfvars`:

```bash
terraform apply
```

Or use gcloud:

```bash
gcloud container clusters resize my-gke-cluster --num-nodes=5 --region us-central1
```

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This permanently deletes your cluster and all resources.

## Security Best Practices

1. ✅ Use private nodes
2. ✅ Enable Workload Identity
3. ✅ Enable Binary Authorization
4. ✅ Use shielded nodes
5. ✅ Enable network policies
6. ✅ Use least-privilege service accounts
7. ✅ Enable audit logging
8. ✅ Restrict master authorized networks
9. ✅ Keep clusters updated via release channels

## Cost Optimization

1. Use preemptible nodes for batch workloads
2. Enable cluster autoscaling
3. Right-size machine types
4. Use regional persistent disks cautiously
5. Clean up unused load balancers
6. Use Committed Use Discounts for stable workloads
7. Consider zonal clusters for development

## Troubleshooting

### Issue: kubectl cannot connect

**Solution**: Update credentials:
```bash
gcloud container clusters get-credentials my-gke-cluster --region us-central1 --project YOUR_PROJECT_ID
```

### Issue: Private cluster access

**Solution**: For fully private clusters, connect via:
- Cloud Shell
- Compute Engine VM in same VPC
- VPN or Cloud Interconnect

### Issue: Node registration failing

**Solution**: Check:
```bash
gcloud container operations list
kubectl get events
```

### Issue: Quota exceeded

**Solution**: Request quota increase:
```bash
gcloud compute project-info describe --project YOUR_PROJECT_ID
```

## Additional Resources

- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [GKE Best Practices](https://cloud.google.com/kubernetes-engine/docs/best-practices)
- [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)

## Support

For issues:
1. Check Terraform output for errors
2. Review GKE cluster logs in Cloud Console
3. Check Cloud Logging for detailed errors
4. Review GCP quotas and limits
"""
    
    with open("README.md", "w", encoding="utf-8") as f:
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
*.json
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
    
    print(f"[OK] Created Google Cloud GKE Terraform project: {project_name}")
    print(f"[OK] Files created: main.tf, variables.tf, outputs.tf, terraform.tfvars.example, README.md")
    print(f"\nNext steps:")
    print(f"1. cd {project_name}")
    print(f"2. Login to GCP: gcloud auth login")
    print(f"3. Enable required APIs:")
    print(f"   gcloud services enable compute.googleapis.com container.googleapis.com")
    print(f"4. Copy terraform.tfvars.example to terraform.tfvars and customize")
    print(f"5. terraform init")
    print(f"6. terraform plan")
    print(f"7. terraform apply")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_terraform_gke.py <project_name>")
        sys.exit(1)
    
    project_name = sys.argv[1]
    create_gke_project(project_name)
