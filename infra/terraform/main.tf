# Lookup the latest Ubuntu 22.04 LTS AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "traffic_server" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.app_sg.id]
  key_name                    = var.ssh_key_name
  associate_public_ip_address = true

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    delete_on_termination = true
  }

  user_data = <<-EOF
              #!/bin/bash
              set -ex

              # Update and install Docker prerequisite packages
              apt-get update -y
              apt-get install -y ca-certificates curl gnupg lsb-release git make

              # Install Docker engine
              mkdir -p /etc/apt/keyrings
              curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
              echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
              apt-get update -y
              apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

              # Enable Docker for ubuntu user
              usermod -aG docker ubuntu
              systemctl enable docker
              systemctl start docker

              # Setup application deployment directory
              mkdir -p /opt/traffic-analyzer
              chown -R ubuntu:ubuntu /opt/traffic-analyzer
              chmod 755 /opt/traffic-analyzer

              echo "Server initialization completed successfully." > /var/log/user_data_complete.log
              EOF

  tags = {
    Name = "traffic-analyzer-${var.environment}-server"
  }
}
