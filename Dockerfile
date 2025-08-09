FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1
ENV NOVNC_PORT=8080
ENV VNC_PASS=aurora123
ENV HOME=/root

# Install packages
RUN apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    fluxbox \
    xterm \
    wget \
    python3 python3-pip python3-venv \
    net-tools x11-utils \
    supervisor \
    git \
    ca-certificates \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Locale (avoid locale warnings)
RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# Install noVNC (websockify included)
RUN git clone https://github.com/novnc/noVNC.git /opt/noVNC \
 && git clone https://github.com/novnc/websockify /opt/noVNC/utils/websockify

# Create app dir and copy files
WORKDIR /opt/app
COPY app ./app
COPY web ./web
COPY start.sh /opt/start.sh
RUN chmod +x /opt/start.sh

# Python deps
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install fastapi uvicorn[standard] python-multipart requests

# Expose noVNC port and API port
EXPOSE ${NOVNC_PORT}
EXPOSE 8000

# Start everything
CMD ["/opt/start.sh"]
