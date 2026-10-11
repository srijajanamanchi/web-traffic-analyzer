output "server_public_ip" {
  description = "Public IP address of the provisioned VM"
  value       = aws_instance.traffic_server.public_ip
}

output "dashboard_url" {
  description = "Live Real-Time Telemetry Dashboard URL"
  value       = "http://${aws_instance.traffic_server.public_ip}:3000"
}

output "demo_site_url" {
  description = "CloudScale Demo Site URL"
  value       = "http://${aws_instance.traffic_server.public_ip}:8080"
}

output "api_health_url" {
  description = "Telemetry API Health endpoint"
  value       = "http://${aws_instance.traffic_server.public_ip}:8000/health"
}

output "grafana_url" {
  description = "Grafana Observability Portal"
  value       = "http://${aws_instance.traffic_server.public_ip}:3001"
}

output "prometheus_url" {
  description = "Prometheus Metrics UI"
  value       = "http://${aws_instance.traffic_server.public_ip}:9090"
}

output "ssh_connection_command" {
  description = "SSH Command to connect to the server"
  value       = "ssh -i ~/.ssh/${var.ssh_key_name}.pem ubuntu@${aws_instance.traffic_server.public_ip}"
}
