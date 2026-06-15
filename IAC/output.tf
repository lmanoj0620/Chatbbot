output "cluster_id" {
  value = aws_eks_cluster.demo.id
}

output "node_group_id" {
  value = aws_eks_node_group.demo.id
}

output "vpc_id" {
  value = aws_vpc.demo_vpc.id
}

output "subnet_id" {
  value = aws_subnet.demo_subnet[*].id
}
