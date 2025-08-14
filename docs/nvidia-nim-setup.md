# NVIDIA NIM API Setup Guide

## Quick Setup

1. **Get your NVIDIA NIM API Key:**
   - Visit [NVIDIA NGC Catalog](https://catalog.ngc.nvidia.com/)
   - Sign up/login to your NVIDIA account
   - Generate an API key

2. **Configure the API Key:**
   - Edit `apps/ccm-api/.env`
   - Replace `your-nvidia-nim-api-key-here` with your actual API key
   - Save the file

3. **Start the backend:**
   ```bash
   cd /path/to/PulseDev
   bash scripts/quick-test-setup.sh
   ```

## Environment Variables

The `.env` file supports these configurations:

### AI Configuration
- `NVIDIA_NIM_API_KEY`: Your NVIDIA NIM API key (required for AI features)
- `NVIDIA_NIM_BASE_URL`: API base URL (default: https://integrate.api.nvidia.com/v1)
- `AI_PROVIDER`: AI provider to use (default: nvidia_nim)
- `DEFAULT_MODEL`: Model to use (default: nvidia/llama-3.1-nemotron-70b-instruct)

### Database Configuration (Optional)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

### Security (Optional)
- `ENCRYPTION_KEY`: 32-byte key for AES-256 encryption
- `SESSION_SECRET`: Secret key for sessions

### Features (Optional)
- `AUTO_COMMIT_ENABLED`: Enable auto-commit (default: true)
- `FLOW_DETECTION_ENABLED`: Enable flow detection (default: true)
- `ENERGY_SCORING_ENABLED`: Enable energy scoring (default: true)

## Testing

To test if your API key works:

```bash
cd apps/ccm-api
source venv/bin/activate
python scripts/test-nvidia-nim.py
```

## Troubleshooting

- **401 Unauthorized**: Check your API key is correct
- **Environment not loading**: Make sure `.env` file is in `apps/ccm-api/` directory
- **Python dotenv**: The `python-dotenv` package should be installed automatically
