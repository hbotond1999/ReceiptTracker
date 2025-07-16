# ReceiptTracker Documentation

Welcome to the ReceiptTracker project documentation! Here you will find information about the application's architecture, development, and deployment.

## Demo Video

<a href="https://drive.google.com/file/d/1o6nS1RKkWH3d9bTuY_hFgFFpADR2sZkt/view?usp=drive_link">
  <img src="images/app.jpg" width="150px" alt="Video Title" />
</a>

#### The video was created with AI:
- I recorded the app on my phone using screen recording, without sound
- Then I uploaded this video to Vertex AI and generated narration with the gemini-2.0-flash-preview model
- I generated a voiceover using a TTS model (named Noemi) on [Clipchamp](https://app.clipchamp.com/) and edited the video with AI
- The whole process took **15 minutes**

## 📁 Documentation Files

### 🏗️ [Architecture Documentation](./architecture.en.md)
A detailed overview of the application's architecture, including:
- **System architecture diagram** (Mermaid diagram) - Production and development environments
- **Component descriptions** (Frontend, Backend, Database)
- **JWT authentication** (RSA256, token rotation, RBAC)
- **Data model diagram** (Entity Relationship Diagram)
- **Technology stack** details
- **Scalability**

## 🎯 Project Overview

ReceiptTracker is a modern, cross-platform application that:
- Enables **digitization and processing of receipts**
- Uses **AI-based text recognition**
- Has an **Angular/Ionic frontend** supporting mobile and web
- Uses a **FastAPI backend**
- Runs on **Google Cloud infrastructure**

### Production Environment
- **Frontend**: Google Cloud Run container
- **Backend**: Google Cloud Run container
- **Database**: Google Cloud SQL (PostgreSQL)
- **Files**: Google Cloud Storage

## 📱 Supported Platforms

- **🌐 Web application**
- **📱 Android app**: Available on Google Play Store
- **🍎 iOS app**: Available on App Store

## 🔧 Technologies

### Backend
- FastAPI (Python)
- PostgreSQL
- SQLAlchemy ORM
- OpenAI API

### Frontend
- Angular
- Ionic Framework
- TypeScript

### Infrastructure
- Docker
- Google Cloud Platform
- Cloud Run (container service)
- Cloud SQL (database)
- Cloud Storage (file management)

### Security
- JWT (JSON Web Token) authentication
- RSA256 asymmetric encryption
- bcrypt password hashing
- Role-based Access Control (RBAC)
- Refresh token rotation
- HTTPS encrypted communication

## 🚀 Quick Start

### Automatic Setup (Recommended)

**Simple automatic initialization:**
```bash
# Run in the root folder from Command Prompt
init-project.bat
```

The automatic script performs:
- Creating/activating a Python virtual environment
- Installing requirements
- Creating a .env file
- Generating and copying RSA keys
- Starting Docker containers
- Initializing the database
- Creating an admin user (interactive)
- Optionally generating test data

### Manual Setup (Local Development Environment)

If you want to perform step-by-step setup or encounter issues with the automatic script:

#### 1. Set environment variables
First, create a `.env` file in the `docker` folder based on `.env.example`:

```bash
cd docker
# Copy .env.example to .env and fill in the required values
```

The `.env` file content:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/receipt_tracker
# Access token expiration time (in minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Refresh token expiration time (in days)
REFRESH_TOKEN_EXPIRE_DAYS=7
AI_MODEL=gpt-4.1
OPENAI_API_KEY=your_openai_api_key_here
```

#### 2. Generate RSA keys
Generate the RSA keys required for JWT authentication:

```bash
cd backend
python generate_rsa_keys.py
```

This creates the `backend/keys` folder with `private_key.pem` and `public_key.pem` files.

Then copy the keys to the docker folder:

```bash
# In PowerShell (Windows)
Copy-Item -Path "keys\*" -Destination "..\docker\keys\" -Force

# Or manually copy from backend/keys to docker/keys:
# - private_key.pem
# - public_key.pem
```

#### 3. Start Docker containers
```bash
cd ../docker
# Start Docker containers (database is required for the next steps)
docker-compose up -d

# PostgreSQL: localhost:5432
```

#### 4. Initialize the database
```bash
cd ../backend
# Create database tables and default roles
python init_db.py
```

#### 5. Create admin user
```bash
# Create admin user interactively
python create_admin.py
```

The script will ask for the admin username, email, full name, and password.

#### 6. Generate test data (optional)
If you want to work with test data, you can generate stores and receipts:

```bash
python generate_test_data.py
```

The script will ask interactively:
- How many receipts to generate (default: 500)
- Creates 10 stores with Hungarian names
- Generates receipts with real Hungarian data (addresses, product names)
- Uses multithreading for fast generation

**Note:** Run this only after creating the admin user!

#### 7. Access the application
```bash
# Frontend available at: http://localhost
# Backend API: http://localhost:8000
# PostgreSQL: localhost:5432
```

## 🔗 Useful Links

- [Docker Compose configuration](../docker/docker-compose.yaml)
- [Backend source](../backend/)
- [Frontend source](../frontend/ReceiptTracker/)
- [API documentation](http://localhost:8000/docs) (for local development) 