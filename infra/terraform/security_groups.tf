resource "aws_security_group" "app_sg" {
  name        = "traffic-analyzer-app-sg"
  description = "Security group for Traffic Analyzer and Demo Site workloads"
  vpc_id      = aws_vpc.main.id

  # 1. SSH Administrative Access
  ingress {
    description = "SSH from admin workstation"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_ip]
  }

  # 2. Standard Web Traffic
  ingress {
    description = "HTTP reverse proxy"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS secure proxy"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # 3. Frontend Dashboard Application
  ingress {
    description = "React Telemetry Dashboard"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # 4. Demo Website (Traffic Generation Target)
  ingress {
    description = "CloudScale Demo Site"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # 5. FastAPI Telemetry Collector & Health
  ingress {
    description = "FastAPI Telemetry Collector"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # 6. Observability (Prometheus & Grafana)
  ingress {
    description = "Prometheus Metrics UI"
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Grafana Dashboards"
    from_port   = 3001
    to_port     = 3001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound rule: Full egress to internet for package updates & container pulls
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "traffic-analyzer-app-sg"
  }
}

# Database Security Group: Strictly internal, CLOSED to public internet
resource "aws_security_group" "db_sg" {
  name        = "traffic-analyzer-db-sg"
  description = "Database Security Group - strictly isolated from public internet"
  vpc_id      = aws_vpc.main.id

  # Port 5432 is ONLY accessible from application security group
  ingress {
    description     = "PostgreSQL access from App workloads only"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "traffic-analyzer-db-sg-isolated"
  }
}
