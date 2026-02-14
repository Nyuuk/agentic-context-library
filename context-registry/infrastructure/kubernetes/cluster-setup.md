# Kubernetes Cluster Setup Guide

Complete guide for setting up production-ready Kubernetes clusters.

## Cluster Architecture

### High Availability Setup

Production clusters must use high-availability configuration:

- **Control Plane Nodes**: 3 nodes minimum (odd number for etcd quorum)
- **Worker Nodes**: Start with 3, scale based on workload
- **etcd**: Dedicated nodes or co-located with control plane
- **Load Balancer**: For API server high availability

### Node Specifications

#### Control Plane Nodes
- **CPU**: 4 cores minimum
- **RAM**: 8GB minimum
- **Disk**: 100GB SSD
- **OS**: Ubuntu 22.04 LTS or RHEL 8+

#### Worker Nodes
- **CPU**: 8 cores minimum
- **RAM**: 32GB minimum
- **Disk**: 200GB SSD
- **OS**: Ubuntu 22.04 LTS or RHEL 8+

## Installation Methods

### Method 1: kubeadm (Recommended for Self-Managed)

#### Prerequisites

Install on all nodes:

```bash
# Disable swap
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# Load required modules
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

# Set sysctl parameters
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sudo sysctl --system
```

#### Install Container Runtime (containerd)

```bash
# Install containerd
sudo apt-get update
sudo apt-get install -y containerd

# Configure containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml

# Enable SystemdCgroup
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

# Restart containerd
sudo systemctl restart containerd
sudo systemctl enable containerd
```

#### Install kubeadm, kubelet, kubectl

```bash
# Add Kubernetes apt repository
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl

curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Install
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

#### Initialize Control Plane

On first control plane node:

```bash
sudo kubeadm init \
  --control-plane-endpoint="k8s-api.company.com:6443" \
  --upload-certs \
  --pod-network-cidr=10.244.0.0/16 \
  --service-cidr=10.96.0.0/16
```

#### Join Additional Control Plane Nodes

Use the join command from init output:

```bash
sudo kubeadm join k8s-api.company.com:6443 \
  --token <token> \
  --discovery-token-ca-cert-hash sha256:<hash> \
  --control-plane \
  --certificate-key <key>
```

#### Join Worker Nodes

```bash
sudo kubeadm join k8s-api.company.com:6443 \
  --token <token> \
  --discovery-token-ca-cert-hash sha256:<hash>
```

### Method 2: Managed Kubernetes

For cloud-managed clusters:

#### AWS EKS

```bash
eksctl create cluster \
  --name production-cluster \
  --region us-west-2 \
  --version 1.28 \
  --nodegroup-name standard-workers \
  --node-type t3.xlarge \
  --nodes 3 \
  --nodes-min 3 \
  --nodes-max 10 \
  --managed
```

#### Google GKE

```bash
gcloud container clusters create production-cluster \
  --num-nodes=3 \
  --machine-type=n1-standard-4 \
  --zone=us-central1-a \
  --cluster-version=1.28
```

## Network Configuration

### Install CNI Plugin (Calico)

```bash
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
```

### Configure Network Policies

Default deny all ingress:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
```

## Storage Configuration

### Install CSI Driver

For persistent volumes:

```bash
# Example: AWS EBS CSI Driver
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=master"
```

### Create Storage Classes

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
volumeBindingMode: WaitForFirstConsumer
```

## Cluster Validation

### Verify Node Status

```bash
kubectl get nodes
# All nodes should show "Ready"
```

### Verify System Pods

```bash
kubectl get pods -n kube-system
# All pods should be "Running"
```

### Test Pod Deployment

```bash
kubectl run test-nginx --image=nginx
kubectl expose pod test-nginx --port=80 --type=NodePort
kubectl get svc test-nginx
# Access via NodePort to verify networking
```

## Monitoring Setup

### Install Metrics Server

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### Verify Metrics

```bash
kubectl top nodes
kubectl top pods -A
```

## Security Hardening

### Enable RBAC

RBAC should be enabled by default. Verify:

```bash
kubectl api-versions | grep rbac
```

### Pod Security Standards

Enforce pod security at namespace level:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### Audit Logging

Configure API server audit policy in `/etc/kubernetes/manifests/kube-apiserver.yaml`:

```yaml
--audit-policy-file=/etc/kubernetes/audit-policy.yaml
--audit-log-path=/var/log/kubernetes/audit.log
--audit-log-maxage=30
--audit-log-maxbackup=10
--audit-log-maxsize=100
```

## Troubleshooting

### Node Not Ready

Check kubelet status:
```bash
sudo systemctl status kubelet
sudo journalctl -u kubelet -f
```

### Pods Pending

Check events:
```bash
kubectl describe pod <pod-name>
kubectl get events --sort-by='.lastTimestamp'
```

### Network Issues

Test pod-to-pod connectivity:
```bash
kubectl run test-1 --image=busybox -- sleep 3600
kubectl run test-2 --image=busybox -- sleep 3600
kubectl exec test-1 -- ping <test-2-pod-ip>
```

## Maintenance

### Cluster Upgrade

Use kubeadm upgrade:

```bash
# Control plane
sudo kubeadm upgrade plan
sudo kubeadm upgrade apply v1.28.x

# Worker nodes
sudo kubeadm upgrade node
sudo systemctl restart kubelet
```

### Backup etcd

```bash
ETCDCTL_API=3 etcdctl snapshot save snapshot.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```
