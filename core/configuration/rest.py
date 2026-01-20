

# REST framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        # Global throttle if needed, but we rely on local throttling below
    ],
    'DEFAULT_THROTTLE_RATES': {
        # Custom throttle rate defined for the Resend Throttle class
        'otp_resend': '10000/hour', 
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'EXCEPTION_HANDLER': 'apps.base.exception_handler.custom_exception_handler',
}

# Apply tenant filter backend globally so API querysets are scoped to the
# requesting user's tenant (unless they are superuser).
REST_FRAMEWORK.setdefault('DEFAULT_FILTER_BACKENDS', [])
REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS'].insert(0, 'apps.base.drf.TenantFilterBackend')

# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'ServeIQ Admin API',
    'DESCRIPTION': 'API documentation for ServeIQ Admin Backend',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'AUTHENTICATION_WHITELIST': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'REDOC_UI_SETTINGS': {
        'hideDownloadButton': False,
        'hideHostname': False,
        'hideLoading': False,
        'hideSingleRequestSampleTab': False,
        'expandDefaultServerVariables': True,
        'expandResponses': '200,201',
        'jsonSampleExpandLevel': 2,
        'hideSchemaPattern': False,
        'pathInMiddlePanel': False,
        'requiredPropsFirst': True,
        'sortPropsAlphabetically': False,
        'sortOperationsAlphabetically': False,
        'sortTagsAlphabetically': False,
        'nativeScrollbars': False,
        'payloadSampleIdx': 0,
        'theme': {
            'colors': {
                'primary': {
                    'main': '#32329f'
                }
            },
            'typography': {
                'fontSize': '14px',
                'lineHeight': '1.5em',
                'code': {
                    'fontSize': '13px',
                    'fontFamily': 'Courier, monospace',
                    'fontWeight': '400',
                    'color': '#e83e8c',
                    'backgroundColor': 'rgba(27, 31, 35, 0.05)',
                    'wrap': False
                },
                'headings': {
                    'fontFamily': 'Montserrat, sans-serif',
                    'fontWeight': '400',
                    'lineHeight': '1.6em'
                }
            },
            'sidebar': {
                'backgroundColor': '#fafafa',
                'textColor': '#333333'
            },
            'rightPanel': {
                'backgroundColor': '#263238',
                'width': '40%'
            }
        }
    },
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_AUTHENTICATION': None,  # No authentication required for schema/docs
}