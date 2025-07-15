import json
import base64
from main import app

def lambda_handler(event, context):
    """AWS Lambda handler for Flask Deepdub TTS proxy"""
    try:
        print(f"Lambda invoked with event: {json.dumps(event, default=str)}")
        
        # Handle both API Gateway v1.0 and v2.0 event formats
        http_method = event.get('httpMethod', 'GET')  # v1.0 format
        raw_path = event.get('path', '/')  # v1.0 format
        
        # Check for v2.0 format
        request_context = event.get('requestContext', {})
        if 'http' in request_context:
            http_context = request_context['http']
            http_method = http_context.get('method', http_method)
            raw_path = http_context.get('path', raw_path)
        
        # Strip stage prefix from path
        stage = request_context.get('stage', 'prod')
        if raw_path.startswith(f'/{stage}'):
            path = raw_path[len(f'/{stage}'):] or '/'
        else:
            path = raw_path
            
        query_params = event.get('queryStringParameters') or {}
        headers = event.get('headers') or {}
        body = event.get('body', '')
        
        print(f"Parsed request: method={http_method}, raw_path={raw_path}, path={path}")
        
        # Handle base64 encoded body
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body)
        
        # Create Flask test client and make request
        with app.test_client() as client:
            response = client.open(
                path=path,
                method=http_method,
                headers=headers,
                data=body,
                query_string=query_params
            )
            
            print(f"Flask response: status={response.status_code}, content_type={response.content_type}")
            
            # Handle binary audio response
            if (response.content_type == 'application/octet-stream' or 
                response.content_type == 'audio/pcm' or 
                response.content_type == 'audio/wav' or
                response.content_type == 'audio/mpeg'):
                
                # Return binary data as base64
                return {
                    'statusCode': response.status_code,
                    'headers': dict(response.headers),
                    'body': base64.b64encode(response.data).decode('utf-8'),
                    'isBase64Encoded': True
                }
            else:
                # Return text/JSON response
                return {
                    'statusCode': response.status_code,
                    'headers': dict(response.headers),
                    'body': response.get_data(as_text=True)
                }
                
    except Exception as e:
        print(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }
