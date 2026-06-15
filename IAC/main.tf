############################
# Provider
############################
provider "aws" {
  region = "ap-south-1"
}

############################
# VPC
############################
resource "aws_vpc" "demo_vpc" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "demo_vpc"
  }
}

############################
# Subnets (2 public subnets)
############################
resource "aws_subnet" "demo_subnet" {
  count = 2
  vpc_id = aws_vpc.demo_vpc.id
  cidr_block = cidrsubnet(aws_vpc.demo_vpc.cidr_block, 8, count.index)

  availability_zone = element(["ap-south-1a", "ap-south-1b"], count.index)
  map_public_ip_on_launch = true

  tags = {
    Name = "demo_subnet-${count.index}"
  }
}

############################
# Internet Gateway
############################
resource "aws_internet_gateway" "demo_igw" {
  vpc_id = aws_vpc.demo_vpc.id

  tags = {
    Name = "demo_igw"
  }
}

############################
# Route Table
############################
resource "aws_route_table" "demo_rt" {
  vpc_id = aws_vpc.demo_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.demo_igw.id
  }

  tags = {
    Name = "demo_route_table"
  }
}

############################
# Route Table Association
############################
resource "aws_route_table_association" "demo_rt_assoc" {
  count = 2
  subnet_id = aws_subnet.demo_subnet[count.index].id
  route_table_id = aws_route_table.demo_rt.id
}

############################
# Security Groups
############################

# EKS Cluster Security Group
resource "aws_security_group" "demo_cluster_sg" {
  vpc_id = aws_vpc.demo_vpc.id

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "demo-cluster-sg"
  }
}

# Worker Node Security Group
resource "aws_security_group" "demo_node_sg" {
  vpc_id = aws_vpc.demo_vpc.id

  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "demo-node-sg"
  }
}

############################
# IAM Role - EKS Cluster
############################
resource "aws_iam_role" "demo_eks_cluster_role" {
  name = "demo_eks_cluster_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "eks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "cluster_policy" {
  role       = aws_iam_role.demo_eks_cluster_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

############################
# IAM Role - Worker Nodes
############################
resource "aws_iam_role" "demo_eks_node_role" {
  name = "demo_eks_node_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

# Worker node required policies
resource "aws_iam_role_policy_attachment" "node_worker_policy" {
  role       = aws_iam_role.demo_eks_node_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}

resource "aws_iam_role_policy_attachment" "node_cni_policy" {
  role       = aws_iam_role.demo_eks_node_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}

resource "aws_iam_role_policy_attachment" "node_registry_policy" {
  role       = aws_iam_role.demo_eks_node_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

############################
# EKS Cluster
############################
resource "aws_eks_cluster" "demo" {
  name     = "demo-cluster"
  role_arn = aws_iam_role.demo_eks_cluster_role.arn

  vpc_config {
    subnet_ids         = aws_subnet.demo_subnet[*].id
    security_group_ids = [aws_security_group.demo_cluster_sg.id]
  }

  depends_on = [
    aws_iam_role_policy_attachment.cluster_policy
  ]
}

############################
# EKS Node Group
############################
resource "aws_eks_node_group" "demo" {
  cluster_name    = aws_eks_cluster.demo.name
  node_group_name = "demo-node-group"
  node_role_arn   = aws_iam_role.demo_eks_node_role.arn

  subnet_ids = aws_subnet.demo_subnet[*].id

  scaling_config {
    desired_size = 2
    max_size     = 100
    min_size     = 2
  }

  instance_types = ["t3.micro"]

  remote_access {
    ec2_ssh_key               = var.ssh_key_name
    source_security_group_ids = [aws_security_group.demo_node_sg.id]
  }

  depends_on = [
    aws_iam_role_policy_attachment.node_worker_policy,
    aws_iam_role_policy_attachment.node_cni_policy,
    aws_iam_role_policy_attachment.node_registry_policy
  ]
}
