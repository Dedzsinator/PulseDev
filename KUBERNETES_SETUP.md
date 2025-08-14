# PulseDev+ Kubernetes Deployment Setup

This guide covers the complete setup for deploying PulseDev+ on Kubernetes using only `kubectl`.

## Prerequisites

### 1. Container Runtime
You need a container runtime. Choose one:

**Option A: Docker (Recommended)**
```bash
# Install Docker
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

**Option B: containerd**
```bash
# Install containerd
sudo apt-get update
sudo apt-get install containerd
sudo systemctl enable containerd
sudo systemctl start containerd
```

### 2. Kubernetes Components
Install kubeadm, kubelet, and kubectl:

```bash
# Update and install dependencies
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

# Add Kubernetes GPG key
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

# Add Kubernetes repository
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Install Kubernetes components
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

### 3. System Configuration

**Disable swap:**
```bash
sudo swapoff -a
sudo sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
```

**Load kernel modules:**
```bash
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter
```

**Configure sysctl:**
```bash
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sudo sysctl --system
```

## Cluster Initialization

### 1. Initialize the Control Plane
```bash
# Initialize cluster
sudo kubeadm init --pod-network-cidr=10.244.0.0/16

# Set up kubectl for regular user
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

### 2. Install Pod Network (CNI)
Choose one of these network solutions:

**Option A: Flannel (Simple)**
```bash
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

**Option B: Calico (Advanced)**
```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.1/manifests/tigera-operator.yaml
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.1/manifests/custom-resources.yaml
```

### 3. Allow Pods on Control Plane (Single Node Setup)
```bash
kubectl taint nodes --all node-role.kubernetes.io/control-plane-
```

## Verify Installation

```bash
# Check nodes
kubectl get nodes

# Check system pods
kubectl get pods -A

# Verify all components are ready
kubectl get componentstatuses
```

## Alternative: Local Kubernetes Options

If you prefer easier local development setups:

### Option 1: Minikube
```bash
# Install minikube
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
chmod +x minikube
sudo mv minikube /usr/local/bin/

# Start cluster
minikube start --driver=docker
```

### Option 2: Kind (Kubernetes in Docker)
```bash
# Install kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Create cluster
kind create cluster --name pulsedev
```

### Option 3: K3s (Lightweight)
```bash
# Install k3s
curl -sfL https://get.k3s.io | sh -
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config
```

## Deploy PulseDev+ to Kubernetes

Once your cluster is ready:

### 1. Set up NVIDIA NIM API Key
```bash
# Create .env file in apps/ccm-api/
echo "NVIDIA_NIM_API_KEY=your-actual-api-key-here" > apps/ccm-api/.env
```

### 2. Deploy using kubectl
```bash
# Make deployment script executable
chmod +x scripts/deploy-k8s.sh

# Deploy to Kubernetes
./scripts/deploy-k8s.sh
```

### 3. Verify Deployment
```bash
# Check all resources
kubectl get all -n pulsedev

# Check pod logs
kubectl logs -n pulsedev deployment/ccm-api -f

# Port forward to access locally
kubectl port-forward -n pulsedev svc/ccm-api 8000:8000
```

### 4. Access the API
- Health Check: http://localhost:8000/health
- API Documentation: http://localhost:8000/docs

## Troubleshooting

### Common Issues

**Pods stuck in Pending:**
```bash
kubectl describe pod <pod-name> -n pulsedev
```

**Network issues:**
```bash
kubectl get pods -A | grep -E '(flannel|calico|kube-proxy)'
```

**Resource issues:**
```bash
kubectl top nodes
kubectl describe node <node-name>
```

**DNS issues:**
```bash
kubectl run test-pod --image=busybox:1.28 --rm -it --restart=Never -- nslookup kubernetes.default
```

### Useful Commands

```bash
# Get cluster info
kubectl cluster-info

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp

# Scale deployment
kubectl scale deployment ccm-api -n pulsedev --replicas=2

# Update deployment
kubectl set image deployment/ccm-api -n pulsedev ccm-api=your-new-image

# Access pod shell
kubectl exec -it <pod-name> -n pulsedev -- /bin/bash

# Port forward multiple services
kubectl port-forward -n pulsedev svc/postgres 5432:5432 &
kubectl port-forward -n pulsedev svc/redis 6379:6379 &
kubectl port-forward -n pulsedev svc/ccm-api 8000:8000 &
```

## Production Considerations

For production deployments, consider:

1. **Resource Limits**: Set appropriate CPU/memory limits
2. **Storage**: Use persistent volumes for database
3. **Monitoring**: Deploy Prometheus + Grafana
4. **Logging**: Centralized logging with ELK stack
5. **Security**: Network policies, RBAC, security contexts
6. **High Availability**: Multi-node cluster, multiple replicas
7. **Ingress**: Use Nginx/Traefik for external access
8. **Backup**: Regular database backups
9. **Secrets Management**: Use external secret managers
10. **Auto-scaling**: Horizontal Pod Autoscaler (HPA)

## Next Steps

Once Kubernetes is set up and PulseDev+ is deployed:

1. Configure the Neovim plugin to connect to the API
2. Test activity tracking and AI features
3. Monitor system performance and logs
4. Scale services based on usage patterns

For immediate testing without Kubernetes, use the Docker deployment:
```bash
./scripts/deploy-direct.sh
```
