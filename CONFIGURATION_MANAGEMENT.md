# Configuration Management System

## 🎯 **Overview**

The camera module now features a comprehensive configuration management system that supports:
- **Environment Variables**: Runtime configuration override
- **Configuration Files**: JSON-based configuration files
- **Default Values**: Sensible defaults for all settings
- **Validation**: Automatic validation of all configuration values
- **Type Safety**: Strong typing with proper type conversion

## 📁 **Configuration Sources Priority**

Configuration is loaded in the following priority order (highest to lowest):

1. **Environment Variables** (highest priority)
2. **Configuration File** (JSON)
3. **Default Values** (lowest priority)

## 🔧 **Configuration Structure**

### **Camera Configuration**
Controls camera hardware and CHDKPTP settings.

| Setting                | Environment Variable          | Default                                         | Range   | Description                         |
| ---------------------- | ----------------------------- | ----------------------------------------------- | ------- | ----------------------------------- |
| `chdkptp_location`     | `CHDKPTP_LOCATION`            | `/home/arrumada/Dev/CanonCameraControl/ChdkPTP` | -       | Path to CHDKPTP installation        |
| `output_directory`     | `CAMERA_OUTPUT_DIRECTORY`     | `/home/arrumada/Images`                         | -       | Directory for captured images       |
| `frame_file_name`      | `CAMERA_FRAME_FILE_NAME`      | `frame.ppm`                                     | -       | Name of live view frame file        |
| `default_jpeg_quality` | `CAMERA_DEFAULT_JPEG_QUALITY` | `80`                                            | 1-100   | Default JPEG compression quality    |
| `max_framerate`        | `CAMERA_MAX_FRAMERATE`        | `8.0`                                           | 0.1-8.0 | Maximum frames per second           |
| `command_timeout`      | `CAMERA_COMMAND_TIMEOUT`      | `30`                                            | 5-300   | Command execution timeout (seconds) |

### **Image Processing Configuration**
Controls image processing and timestamp overlay settings.

| Setting                    | Environment Variable             | Default       | Range   | Description                         |
| -------------------------- | -------------------------------- | ------------- | ------- | ----------------------------------- |
| `default_jpeg_quality`     | `IMAGE_DEFAULT_JPEG_QUALITY`     | `80`          | 1-100   | Default JPEG quality for processing |
| `timestamp_font_scale`     | `IMAGE_TIMESTAMP_FONT_SCALE`     | `0.7`         | 0.1-5.0 | Font size for timestamp overlay     |
| `timestamp_font_thickness` | `IMAGE_TIMESTAMP_FONT_THICKNESS` | `2`           | 1-10    | Font thickness for timestamp        |
| `timestamp_color`          | `IMAGE_TIMESTAMP_COLOR`          | `255,255,255` | 0-255   | RGB color for timestamp text        |
| `timestamp_outline_color`  | `IMAGE_TIMESTAMP_OUTLINE_COLOR`  | `0,0,0`       | 0-255   | RGB color for timestamp outline     |

### **Environment Configuration**
Controls application behavior and performance settings.

| Setting                  | Environment Variable     | Default                                                | Range                             | Description                          |
| ------------------------ | ------------------------ | ------------------------------------------------------ | --------------------------------- | ------------------------------------ |
| `environment`            | `ENVIRONMENT`            | `development`                                          | dev/staging/prod                  | Application environment              |
| `debug`                  | `DEBUG`                  | `false`                                                | true/false                        | Enable debug mode                    |
| `log_level`              | `LOG_LEVEL`              | `INFO`                                                 | DEBUG/INFO/WARNING/ERROR/CRITICAL | Logging level                        |
| `log_format`             | `LOG_FORMAT`             | `%(asctime)s - %(name)s - %(levelname)s - %(message)s` | -                                 | Log message format                   |
| `enable_authentication`  | `ENABLE_AUTHENTICATION`  | `false`                                                | true/false                        | Enable API authentication            |
| `api_key_required`       | `API_KEY_REQUIRED`       | `false`                                                | true/false                        | Require API key for requests         |
| `max_concurrent_streams` | `MAX_CONCURRENT_STREAMS` | `5`                                                    | 1-20                              | Maximum concurrent live view streams |
| `stream_buffer_size`     | `STREAM_BUFFER_SIZE`     | `1048576`                                              | 1024-10485760                     | Stream buffer size in bytes          |

## 🚀 **Usage Examples**

### **1. Using Configuration File**

Create a configuration file `config/camera_config.json`:

```json
{
  "camera": {
    "chdkptp_location": "/opt/chdkptp",
    "output_directory": "/var/camera/images",
    "default_jpeg_quality": 90,
    "max_framerate": 5.0
  },
  "image_processing": {
    "timestamp_font_scale": 1.0,
    "timestamp_color": [255, 0, 0]
  },
  "environment": {
    "environment": "production",
    "log_level": "WARNING",
    "max_concurrent_streams": 3
  }
}
```

Initialize the container with the configuration file:

```python
from app.camera.infrastructure.container import get_camera_container

# Use configuration file
container = get_camera_container("config/camera_config.json")
await container.initialize()
```

### **2. Using Environment Variables**

Set environment variables to override configuration:

```bash
# Camera settings
export CHDKPTP_LOCATION="/opt/chdkptp"
export CAMERA_OUTPUT_DIRECTORY="/var/camera/images"
export CAMERA_DEFAULT_JPEG_QUALITY=90
export CAMERA_MAX_FRAMERATE=5.0

# Image processing settings
export IMAGE_TIMESTAMP_FONT_SCALE=1.0
export IMAGE_TIMESTAMP_COLOR="255,0,0"

# Environment settings
export ENVIRONMENT="production"
export LOG_LEVEL="WARNING"
export MAX_CONCURRENT_STREAMS=3
```

### **3. Programmatic Configuration**

Access configuration programmatically:

```python
from app.camera.infrastructure.container import get_camera_container
from app.camera.infrastructure.configuration_service import get_configuration_service

# Get configuration service
config_service = get_configuration_service()

# Get specific configurations
camera_config = config_service.get_camera_config()
image_config = config_service.get_image_processing_config()
env_config = config_service.get_environment_config()

# Access specific values
chdkptp_path = camera_config.chdkptp_location
jpeg_quality = image_config.default_jpeg_quality
log_level = env_config.log_level

# Validate configuration
result = config_service.load_configuration()
if result.is_success:
    print("Configuration is valid")
else:
    print(f"Configuration error: {result.error}")
```

### **4. Configuration Validation**

All configurations are automatically validated:

```python
# Validate individual configurations
camera_result = camera_config.validate()
image_result = image_config.validate()
env_result = env_config.validate()

# Validate complete application configuration
app_config = config_service.configuration
result = app_config.validate()

if not result.is_success:
    print(f"Configuration validation failed: {result.error}")
```

## 🔄 **Configuration Reloading**

Configuration can be reloaded at runtime:

```python
# Reload configuration from sources
success = container.reload_configuration()
if success:
    print("Configuration reloaded successfully")
else:
    print("Failed to reload configuration")

# Export current configuration
container.export_configuration("current_config.json")
```

## 🛡️ **Validation Rules**

### **Camera Configuration Validation**
- `chdkptp_location`: Must exist and be accessible
- `output_directory`: Will be created if it doesn't exist
- `default_jpeg_quality`: Must be between 1 and 100
- `max_framerate`: Must be between 0.1 and 8.0 FPS
- `command_timeout`: Must be between 5 and 300 seconds

### **Image Processing Validation**
- `default_jpeg_quality`: Must be between 1 and 100
- `timestamp_font_scale`: Must be between 0.1 and 5.0
- `timestamp_font_thickness`: Must be between 1 and 10
- `timestamp_color`: Must be valid RGB tuple (0-255 for each component)
- `timestamp_outline_color`: Must be valid RGB tuple (0-255 for each component)

### **Environment Configuration Validation**
- `environment`: Must be one of: "development", "staging", "production"
- `log_level`: Must be valid Python logging level
- `max_concurrent_streams`: Must be between 1 and 20
- `stream_buffer_size`: Must be between 1KB and 10MB

## 🚨 **Error Handling**

Configuration errors are handled gracefully:

```python
# Configuration loading with error handling
result = config_service.load_configuration()
if not result.is_success:
    logger.error(f"Configuration error: {result.error}")
    # Use default configuration or exit gracefully
    return False

# Service initialization with configuration validation
try:
    container = get_camera_container()
    success = await container.initialize()
    if not success:
        logger.error("Failed to initialize camera container")
        return False
except RuntimeError as e:
    logger.error(f"Configuration not available: {e}")
    return False
```

## 📋 **Best Practices**

### **1. Environment-Specific Configuration**
- Use different configuration files for different environments
- Override sensitive settings with environment variables
- Never commit production credentials to version control

### **2. Configuration Validation**
- Always validate configuration before using it
- Provide meaningful error messages for validation failures
- Use sensible defaults for optional settings

### **3. Security Considerations**
- Use environment variables for sensitive data
- Validate all configuration inputs
- Limit file permissions on configuration files

### **4. Performance Optimization**
- Use `@lru_cache` for configuration service singleton
- Cache configuration objects to avoid repeated file reads
- Validate configuration once at startup

## 🔧 **Migration from Hard-Coded Values**

### **Before (Hard-Coded)**
```python
class CHDKPTPCameraService:
    def __init__(self):
        self.chdkptp_location = "/home/arrumada/Dev/CanonCameraControl/ChdkPTP"
        self.output_directory = "/home/arrumada/Images"
        self.jpeg_quality = 80
```

### **After (Configuration-Driven)**
```python
class RefactoredCHDKPTPCameraService:
    def __init__(self, subprocess_service, image_service, file_service, config):
        self.config = config  # CameraConfiguration object
        self.chdkptp_location = config.chdkptp_location
        self.output_directory = config.output_directory
        self.jpeg_quality = config.default_jpeg_quality
```

## ✅ **Benefits Achieved**

- **Flexibility**: Easy to configure for different environments
- **Security**: Sensitive data can be externalized
- **Maintainability**: No hard-coded values in code
- **Validation**: Automatic validation prevents configuration errors
- **Type Safety**: Strong typing with proper type conversion
- **Observability**: Clear logging of configuration loading and validation
- **Testability**: Easy to test with different configurations

This configuration management system provides a robust, flexible, and secure way to manage application settings across different environments and deployment scenarios. 