# School QR Code Extractor

This application automatically extracts QR codes from your school's website (qehsn.ha.org.hk) for attendance taking and displays them via a web interface.

## Features

- **Automatic Extraction**: Periodically checks the school website for QR codes
- **Login Support**: Uses environment variables for secure credentials
- **Web Interface**: Displays the latest QR code for easy access
- **QR Decoding**: Attempts to decode the content of extracted QR codes
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **Reverse Proxy Ready**: Can be used behind a reverse proxy

## Setup Instructions

### Prerequisites

- Docker and Docker Compose installed on your system
- Network access to your school's website

### Quick Start

1. **Clone this repository or download the files**

2. **Create a `.env` file with your credentials**:
   ```
   QR_USERNAME=your_school_username
   QR_PASSWORD=your_school_password
   ```

3. **Build and start the container**:
   ```bash
   docker-compose up -d
   ```

4. **Access the web interface**:
   Open your browser and navigate to `http://localhost:3456`

### Reverse Proxy Setup

To use this application behind a reverse proxy (such as Nginx or Traefik):

1. Configure your reverse proxy to forward requests to `http://localhost:3456`

2. Example Nginx configuration:
   ```nginx
   server {
       listen 80;
       server_name qr.yourdomain.com;

       location / {
           proxy_pass http://localhost:3456;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

## Configuration Options

You can customize the application by changing the following environment variables in the `docker-compose.yml` file:

- `SCHOOL_URL`: URL of your school's website (default: https://qehsn.ha.org.hk)
- `USERNAME`: Your login username
- `PASSWORD`: Your login password
- `INTERVAL_MINUTES`: How often to check for new QR codes (default: 30 minutes)

## Troubleshooting

- **No QR codes found**: Check logs in the `logs` directory
- **Login issues**: Verify your credentials are correct
- **Access problems**: Ensure the container has network access to the school website

## Security Notes

- This application stores your credentials as environment variables for security
- The extracted QR codes are stored in the `qr_codes` directory
- Consider setting up HTTPS if deploying to a public server
