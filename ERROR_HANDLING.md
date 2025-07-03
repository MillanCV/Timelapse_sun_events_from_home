# Error Handling System

## 🎯 **Overview**

The camera module now features a comprehensive error handling system that provides:
- **Centralized Error Management**: All errors are handled through a single service
- **Error Categorization**: Errors are classified by type for appropriate handling
- **Structured Error Responses**: Consistent error response format across all endpoints
- **Request Tracking**: Each request gets a unique ID for tracing
- **Detailed Logging**: Comprehensive error logging with context
- **Custom Exceptions**: Domain-specific exceptions for different error types

## 🔧 **Error Types**

### **Error Categories**

| Error Type            | Description               | HTTP Status | Example                  |
| --------------------- | ------------------------- | ----------- | ------------------------ |
| `validation_error`    | Input validation failures | 400         | Invalid framerate value  |
| `configuration_error` | Configuration issues      | 500         | Missing CHDKPTP path     |
| `camera_error`        | Camera hardware issues    | 500         | Camera not connected     |
| `chdkptp_error`       | CHDKPTP command failures  | 500         | Command execution failed |
| `file_error`          | File system operations    | 500         | Cannot read image file   |
| `network_error`       | Network communication     | 500         | Connection timeout       |
| `permission_error`    | Access permission issues  | 403         | Cannot access camera     |
| `timeout_error`       | Operation timeouts        | 408         | Command timeout          |
| `resource_error`      | Resource exhaustion       | 503         | Memory full              |
| `unknown_error`       | Unclassified errors       | 500         | Unexpected exceptions    |

## 🏗️ **Architecture**

### **Error Handling Flow**

```
Request → API Endpoint → Use Case → Service → Error Handling Service → Response
```

1. **Request comes in** with optional `X-Request-ID` header
2. **API endpoint** catches exceptions and delegates to error service
3. **Error service** analyzes error type and creates structured response
4. **Response** includes error details, request ID, and appropriate HTTP status

### **Components**

- **ErrorHandlingService**: Central error management
- **Custom Exceptions**: Domain-specific error types
- **ErrorResponse**: Standardized error response format
- **ErrorDetails**: Detailed error information
- **Request ID Tracking**: Unique identifier for each request

## 🚀 **Usage Examples**

### **1. API Endpoint Error Handling**

```python
@router.post("/shoot")
async def shoot_camera(
    request: Request,
    container=Depends(get_camera_container_dependency),
    error_service=Depends(get_error_handling_service_dependency)
):
    """Take a single photo with the camera."""
    request_id = str(request.headers.get("X-Request-ID", ""))
    
    try:
        # Business logic here
        result = await use_case.execute(request_data)
        
        if result.is_success:
            return error_service.create_success_response(data, request_id)
        else:
            error_response = error_service.handle_error(
                Exception(result.error), 
                {"operation": "camera_shooting"}, 
                request_id
            )
            raise HTTPException(status_code=500, detail=error_response.dict())
            
    except HTTPException:
        raise
    except Exception as e:
        error_response = error_service.handle_error(
            e, 
            {"operation": "camera_shooting"}, 
            request_id
        )
        raise HTTPException(status_code=500, detail=error_response.dict())
```

### **2. Custom Exception Usage**

```python
# In service layer
if not chdkptp_script.exists():
    raise CHDKPTPError(
        message="CHDKPTP script not found",
        code="CHDKPTP_SCRIPT_MISSING",
        details={"path": str(chdkptp_script)}
    )

# In validation
if framerate < 0.1 or framerate > 8.0:
    raise ValidationError(
        message="Framerate must be between 0.1 and 8.0 FPS",
        code="INVALID_FRAMERATE",
        details={"provided": framerate, "min": 0.1, "max": 8.0}
    )
```

### **3. Error Response Format**

```json
{
  "success": false,
  "error_type": "validation_error",
  "message": "Framerate must be between 0.1 and 8.0 FPS",
  "code": "INVALID_FRAMERATE",
  "details": {
    "provided": 15.0,
    "min": 0.1,
    "max": 8.0
  },
  "timestamp": "2024-01-15T10:30:45.123456",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### **4. Success Response Format**

```json
{
  "success": true,
  "data": {
    "message": "Camera shooting successful",
    "shooting_id": "shoot_20240115_103045",
    "image_path": "/home/arrumada/Images/IMG_001.jpg",
    "timestamp": "2024-01-15T10:30:45.123456"
  },
  "timestamp": "2024-01-15T10:30:45.123456",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## 🔧 **Custom Error Handlers**

### **Registering Custom Handlers**

```python
def custom_chdkptp_handler(error: Exception, details: ErrorDetails, request_id: str) -> ErrorResponse:
    """Custom handler for CHDKPTP errors."""
    return ErrorResponse(
        success=False,
        error_type=ErrorType.CHDKPTP_ERROR.value,
        message=f"CHDKPTP Error: {details.message}",
        code=details.code or "CUSTOM_CHDKPTP_ERROR",
        details=details.details,
        request_id=request_id,
    )

# Register custom handler
error_service = get_error_handling_service()
error_service.register_error_handler(ErrorType.CHDKPTP_ERROR, custom_chdkptp_handler)
```

### **Decorator Usage**

```python
from ...camera.infrastructure.error_handling_service import handle_errors

@handle_errors({"operation": "camera_shooting"})
async def shoot_camera_async():
    """Async function with automatic error handling."""
    # Your code here
    pass

@handle_sync_errors({"operation": "validation"})
def validate_config(config):
    """Sync function with automatic error handling."""
    # Your code here
    pass
```

## 📊 **Error Monitoring**

### **Logging Levels**

- **WARNING**: Validation and configuration errors
- **ERROR**: Camera, CHDKPTP, and file errors
- **DEBUG**: Full traceback information

### **Log Format**

```
Error [550e8400-e29b-41d4-a716-446655440000] - Type: validation_error, 
Message: Framerate must be between 0.1 and 8.0 FPS, 
Code: INVALID_FRAMERATE, 
Context: {'operation': 'live_view_stream', 'framerate': 15.0, 'quality': 80}
```

### **Request ID Tracking**

- **Client-provided**: Set `X-Request-ID` header
- **Auto-generated**: UUID4 if not provided
- **Response headers**: Include request ID in all responses
- **Log correlation**: All logs include request ID

## 🛡️ **Error Prevention**

### **Input Validation**

```python
# Validate parameters before processing
if framerate < 0.1 or framerate > 8.0:
    error_response = error_service.handle_error(
        ValueError("Framerate must be between 0.1 and 8.0 FPS"),
        {"operation": "live_view_stream", "framerate": framerate},
        request_id
    )
    raise HTTPException(status_code=400, detail=error_response.dict())
```

### **Resource Validation**

```python
# Check resources before operations
if not await self.subprocess_service.validate_executable("chdkptp.sh"):
    raise CHDKPTPError(
        message="CHDKPTP script not found",
        code="CHDKPTP_SCRIPT_MISSING",
        details={"expected_path": str(chdkptp_script)}
    )
```

### **Configuration Validation**

```python
# Validate configuration at startup
result = config_service.load_configuration()
if not result.is_success:
    raise ConfigurationError(
        message=f"Configuration validation failed: {result.error}",
        code="CONFIG_VALIDATION_FAILED"
    )
```

## 🔄 **Error Recovery**

### **Retry Logic**

```python
async def execute_with_retry(operation, max_retries=3, delay=1.0):
    """Execute operation with retry logic."""
    for attempt in range(max_retries):
        try:
            return await operation()
        except TimeoutError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
```

### **Graceful Degradation**

```python
async def get_camera_status():
    """Get camera status with graceful degradation."""
    try:
        return await camera_service.get_status()
    except CameraError:
        # Return basic status if camera is unavailable
        return CameraStatus(
            is_connected=False,
            is_recording=False,
            current_mode=None,
            battery_level=None,
            storage_available=None,
        )
```

## 📋 **Best Practices**

### **1. Error Context**

Always provide meaningful context:

```python
error_response = error_service.handle_error(
    e, 
    {
        "operation": "camera_shooting",
        "parameters": {"quality": quality, "framerate": framerate},
        "user_id": user_id,
        "session_id": session_id
    }, 
    request_id
)
```

### **2. Error Codes**

Use consistent, descriptive error codes:

```python
# Good
raise ValidationError("Invalid framerate", code="INVALID_FRAMERATE")

# Bad
raise ValidationError("Invalid framerate", code="ERR_001")
```

### **3. Error Messages**

Provide user-friendly error messages:

```python
# Good
raise ConfigurationError("CHDKPTP installation not found. Please install CHDKPTP first.")

# Bad
raise ConfigurationError("File not found: /path/to/chdkptp.sh")
```

### **4. Error Details**

Include relevant details for debugging:

```python
raise CHDKPTPError(
    message="Command execution failed",
    code="CHDKPTP_COMMAND_FAILED",
    details={
        "command": " ".join(cmd),
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    }
)
```

## ✅ **Benefits Achieved**

- **Consistency**: All errors follow the same format and handling pattern
- **Traceability**: Request IDs enable end-to-end error tracking
- **Debugging**: Detailed error information and context
- **User Experience**: Clear, actionable error messages
- **Monitoring**: Structured logging for error analysis
- **Maintainability**: Centralized error handling logic
- **Extensibility**: Easy to add new error types and handlers

This error handling system provides a robust foundation for managing errors across the camera module, ensuring consistent behavior and excellent debugging capabilities. 