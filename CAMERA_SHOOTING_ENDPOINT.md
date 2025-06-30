# Camera Shooting Endpoint

This document describes the new camera shooting endpoint that allows you to control the camera to take photos with specific parameters.

## Endpoint

**POST** `/camera/shoot`

## Description

This endpoint allows you to shoot the camera with specific parameters, similar to the bash script functionality. It uses CHDKPTP to control the Canon camera and execute the shooting sequence.

## Request Body

```json
{
  "subject_distance": 5.0,
  "speed": 1.0,
  "iso_value": 100,
  "shots": 10,
  "interval": 2.0
}
```

### Parameters

- **subject_distance** (float): Subject distance parameter (SD)
- **speed** (float): Shutter speed parameter (Speed)
- **iso_value** (int): ISO value for the camera
- **shots** (int): Number of shots to take
- **interval** (float): Interval time between shots in seconds

## Response

```json
{
  "success": true,
  "message": "Camera shooting completed with 10 shots",
  "shooting_id": "shooting_20241201_143022"
}
```

### Response Fields

- **success** (boolean): Whether the shooting operation was successful
- **message** (string): Description of the operation result
- **shooting_id** (string, optional): Unique identifier for the shooting session

## Example Usage

### Using curl

```bash
curl -X POST "http://localhost:8000/camera/shoot" \
     -H "Content-Type: application/json" \
     -d '{
       "subject_distance": 5.0,
       "speed": 1.0,
       "iso_value": 100,
       "shots": 10,
       "interval": 2.0
     }'
```

### Using Python

```python
import requests

url = "http://localhost:8000/camera/shoot"
data = {
    "subject_distance": 5.0,
    "speed": 1.0,
    "iso_value": 100,
    "shots": 10,
    "interval": 2.0
}

response = requests.post(url, json=data)
print(response.json())
```

## Implementation Details

The endpoint follows the clean architecture pattern:

1. **Domain Layer**: `CameraShootingParameters` entity defines the shooting parameters
2. **Application Layer**: `ShootCameraUseCase` orchestrates the shooting operation
3. **Infrastructure Layer**: `CHDKPTPCameraService` implements the actual camera control

The service executes CHDKPTP commands similar to the original bash script:

```bash
sudo /home/arrumada/Dev/CanonCameraControl/ChdkPTP/chdkptp.sh \
  -e "c" \
  -e "rec" \
  -e "clock -sync" \
  -e "luar set_lcd_display(0)" \
  -e "luar set_mf(1)" \
  -e "luar set_aelock(1)" \
  -e "luar set_aflock(1)" \
  -e "rs /home/arrumada/Images -shots=10 -int=2.0 -tv=1.0 -sd=5.0 -isomode=100" \
  -e "play" \
  -e "d A/rawopint.csv /home/arrumada/Dev/CanonCameraControl/Scripts/Logs" \
  -e "dis"
```

## Error Handling

The endpoint returns appropriate HTTP status codes:

- **200**: Success
- **400**: Bad request (invalid parameters)
- **500**: Internal server error (camera not connected, CHDKPTP error, etc.)

## Prerequisites

1. CHDKPTP must be installed at `/home/arrumada/Dev/CanonCameraControl/ChdkPTP`
2. Camera must be connected and accessible
3. User must have sudo privileges for CHDKPTP commands
4. Output directory `/home/arrumada/Images` must exist and be writable

## Testing

You can test the endpoint using the provided test script:

```bash
python test_camera_shooting.py
```

This will create a test request and verify the endpoint responds correctly. 