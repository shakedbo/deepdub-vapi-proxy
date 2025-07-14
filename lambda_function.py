import json
import base64
from main import app

def lambda_handler(event, context):
    """
    AWS Lambda handler for Flask Deepdub TTS proxy.
    Converts API Gateway events to Flask requests and back.
    """
    try:
        # Handle API Gateway event format
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        query_params = event.get('queryStringParameters') or {}
        headers = event.get('headers') or {}
        body = event.get('body', '')
        
        # Handle base64 encoded body (for binary data)
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body)
        
        # Create Flask test client
        with app.test_client() as client:
            # Prepare request
            response = client.open(
                path=path,
                method=http_method,
                headers=headers,
                data=body,
                query_string=query_params
            )
            
            # Handle binary response (PCM audio)
            if response.content_type == 'application/octet-stream':
                # Return binary data as base64 encoded
                return {
                    'statusCode': response.status_code,
                    'headers': dict(response.headers),
                    'body': base64.b64encode(response.data).decode('utf-8'),
                    'isBase64Encoded': True
                }
            else:
                # Return JSON response
                return {
                    'statusCode': response.status_code,
                    'headers': dict(response.headers),
                    'body': response.data.decode('utf-8'),
                    'isBase64Encoded': False
                }
                
    except Exception as e:
        print(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'}),
            'isBase64Encoded': False
        }
