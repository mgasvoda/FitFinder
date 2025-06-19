# FitFinder Data Persistence Configuration

This document explains how to configure FitFinder for persistent data storage across container restarts and ephemeral host deployments.

## Overview

FitFinder stores data in three main components:
- **SQLite Database**: Stores clothing items, outfits, and metadata
- **ChromaDB**: Vector embeddings for similarity search
- **Images**: Uploaded clothing and outfit photos

## Configuration

### Environment Variable

Set the `DATA_PATH` environment variable to specify where all data should be stored:

```bash
# Development (optional - defaults to current directory)
export DATA_PATH=./data

# Production with persistent volume
export DATA_PATH=/mnt/fitfinder
```

### Data Structure

When configured, all data will be organized under the specified path:

```
{DATA_PATH}/
├── fitfinder.db          # SQLite database
├── chroma_db/            # ChromaDB vector storage
│   ├── chroma.sqlite3
│   └── [other ChromaDB files]
└── images/               # Image storage
    ├── clothing_items/   # Individual clothing item photos
    ├── outfits/         # Outfit photos
    └── temp/            # Temporary upload storage
```

## Deployment Scenarios

### Development Environment

For local development, no configuration is needed. Data will be stored in the current directory:

```bash
# .env file (optional)
# DATA_PATH=./dev_data

python start_fitfinder_chainlit.py
```

### Production with Docker Volumes

For production deployments with persistent storage:

1. **Create a persistent volume or mount point:**
   ```bash
   # Create volume
   docker volume create fitfinder-data
   
   # Or prepare a host directory
   mkdir -p /opt/fitfinder-data
   ```

2. **Configure your deployment:**
   ```yaml
   # docker-compose.yml
   version: '3.8'
   services:
     fitfinder:
       image: fitfinder:latest
       environment:
         - DATA_PATH=/mnt/fitfinder
       volumes:
         - fitfinder-data:/mnt/fitfinder
   
   volumes:
     fitfinder-data:
   ```

3. **Or with Docker run:**
   ```bash
   docker run -d \
     -e DATA_PATH=/mnt/fitfinder \
     -v /opt/fitfinder-data:/mnt/fitfinder \
     -p 8001:8001 \
     fitfinder:latest
   ```

### Kubernetes Deployment

For Kubernetes with persistent volumes:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fitfinder
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fitfinder
  template:
    metadata:
      labels:
        app: fitfinder
    spec:
      containers:
      - name: fitfinder
        image: fitfinder:latest
        env:
        - name: DATA_PATH
          value: "/mnt/fitfinder"
        volumeMounts:
        - name: data-storage
          mountPath: /mnt/fitfinder
      volumes:
      - name: data-storage
        persistentVolumeClaim:
          claimName: fitfinder-data-pvc

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: fitfinder-data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_PATH` | `.` | Root directory for all data storage |
| `DATABASE_URL` | `sqlite:///[DATA_PATH]/fitfinder.db` | SQLite database connection string |
| `CHAINLIT_AUTH_SECRET` | auto-generated | Chainlit authentication secret |
| `ANTHROPIC_API_KEY` | required | Anthropic API key for AI features |

## Migration from Previous Versions

If you're upgrading from a version without configurable data paths:

1. **Backup your existing data:**
   ```bash
   mkdir backup
   cp fitfinder.db backup/
   cp -r chroma_db backup/
   cp -r images backup/
   ```

2. **Set up persistent volume:**
   ```bash
   # Create and mount your persistent volume
   mkdir -p /mnt/fitfinder
   ```

3. **Copy data to persistent location:**
   ```bash
   cp backup/fitfinder.db /mnt/fitfinder/
   cp -r backup/chroma_db /mnt/fitfinder/
   cp -r backup/images /mnt/fitfinder/
   ```

4. **Update configuration:**
   ```bash
   export DATA_PATH=/mnt/fitfinder
   ```

5. **Restart the application**

## Troubleshooting

### Common Issues

1. **Permission denied errors:**
   ```bash
   # Ensure the container has write permissions
   sudo chown -R 1000:1000 /mnt/fitfinder
   chmod -R 755 /mnt/fitfinder
   ```

2. **Database locked errors:**
   - Ensure only one instance of the application is running
   - Check that the SQLite database file isn't being accessed by another process

3. **ChromaDB initialization errors:**
   - Verify the ChromaDB directory has proper permissions
   - Ensure sufficient disk space is available

### Validation

Run the included test script to validate your configuration:

```bash
python test_data_persistence.py
```

This will verify that all components are using the correct data paths.

### Logs

Check the application logs for data path information:

```bash
# The application will log the configured paths on startup
docker logs <container_id> | grep -i "path"
```

## Data Backup Recommendations

### Regular Backups

1. **Database backup:**
   ```bash
   # Create SQLite backup
   sqlite3 /mnt/fitfinder/fitfinder.db ".backup /backup/fitfinder_$(date +%Y%m%d).db"
   ```

2. **Complete data backup:**
   ```bash
   # Backup entire data directory
   tar -czf fitfinder_backup_$(date +%Y%m%d).tar.gz -C /mnt fitfinder/
   ```

### Automated Backup Script

```bash
#!/bin/bash
# backup_fitfinder.sh

BACKUP_DIR="/opt/backups/fitfinder"
DATA_PATH="/mnt/fitfinder"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup SQLite database
sqlite3 "$DATA_PATH/fitfinder.db" ".backup $BACKUP_DIR/fitfinder_$DATE.db"

# Backup entire data directory
tar -czf "$BACKUP_DIR/fitfinder_complete_$DATE.tar.gz" -C "$(dirname $DATA_PATH)" "$(basename $DATA_PATH)"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "fitfinder_*" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/fitfinder_complete_$DATE.tar.gz"
```

## Security Considerations

1. **File Permissions**: Ensure the data directory is not world-readable
2. **Volume Encryption**: Consider encrypting persistent volumes in production
3. **Access Control**: Limit access to the data path directory
4. **Backup Security**: Encrypt backup files and store them securely

## Performance Considerations

1. **Storage Type**: Use SSD storage for better database performance
2. **Volume Performance**: Ensure persistent volumes have adequate IOPS
3. **Backup Strategy**: Schedule backups during low-usage periods

---

For additional support or questions, please refer to the main README.md or create an issue in the project repository. 