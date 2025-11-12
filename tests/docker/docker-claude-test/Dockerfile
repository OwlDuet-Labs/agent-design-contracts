FROM ubuntu:22.04

# Install basic tools
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    openssh-server \
    sudo \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install pipx globally
RUN python3 -m pip install pipx

# Create user
RUN useradd -m -s /bin/bash -G sudo testuser
RUN echo "testuser:testuser" | chpasswd

# Setup SSH
RUN mkdir /var/run/sshd
RUN echo "PermitRootLogin no" >> /etc/ssh/sshd_config
RUN echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config

# Switch to testuser
USER testuser
WORKDIR /home/testuser

# Add pipx to PATH
ENV PATH="/home/testuser/.local/bin:$PATH"

# Expose SSH port
EXPOSE 22

# Switch back to root for SSH daemon
USER root
CMD ["/usr/sbin/sshd", "-D"]
