# DBA_Tik_Supp_Sys

## Docker Deployment

### Prerequisites
- Docker
- Docker Compose

### Deployment Steps
1. Clone the repository
2. Create a `.env` file with your `DATABASE_URL`
3. Build and run the container:
   ```
   docker-compose up --build
   ```

### Development
To run in development mode:
```
docker-compose up -d
```

### Stopping the Application
```
docker-compose down
```
