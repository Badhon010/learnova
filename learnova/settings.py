from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.environ.get('SECRET_KEY', 'learnova-dev-secret-key-change-in-production')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django_ckeditor_5',
    'core',
    'learning',
    'accounts',
    'newsletter',
    'quizzes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'learnova.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'learnova.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CSRF_TRUSTED_ORIGINS = ['https://*.replit.dev', 'https://*.repl.co', 'http://localhost:5000', 'http://localhost:8000']

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ─── Site URL (used in sitemaps and JSON-LD) ──────────────────────────────────
SITE_URL = os.environ.get('SITE_URL', 'https://learnova.replit.app')

# ─── Email Configuration ──────────────────────────────────────────────────────
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Learnova <noreply@learnova.dev>')
CONTACT_EMAIL = os.environ.get('CONTACT_EMAIL', EMAIL_HOST_USER)

# ─── CKEditor 5 Configuration ───────────────────────────────────────────────
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': {
            'items': [
                'heading', '|',
                'bold', 'italic', 'underline', 'strikethrough', '|',
                'link', 'insertImage', 'mediaEmbed', '|',
                'bulletedList', 'numberedList', 'todoList', '|',
                'blockQuote', 'codeBlock', 'code', '|',
                'insertTable', '|',
                'alignment', '|',
                'horizontalLine', '|',
                'undo', 'redo',
                '|', 'sourceEditing',
            ],
            'shouldNotGroupWhenFull': True,
        },
        'image': {
            'toolbar': [
                'imageTextAlternative', '|',
                'imageStyle:inline', 'imageStyle:block', 'imageStyle:side',
            ],
        },
        'table': {
            'contentToolbar': ['tableColumn', 'tableRow', 'mergeTableCells', 'tableCellProperties'],
        },
        'codeBlock': {
            'languages': [
                {'language': 'plaintext', 'label': 'Plain text'},
                {'language': 'python', 'label': 'Python'},
                {'language': 'javascript', 'label': 'JavaScript'},
                {'language': 'typescript', 'label': 'TypeScript'},
                {'language': 'html', 'label': 'HTML'},
                {'language': 'css', 'label': 'CSS'},
                {'language': 'sql', 'label': 'SQL'},
                {'language': 'bash', 'label': 'Bash/Shell'},
                {'language': 'json', 'label': 'JSON'},
                {'language': 'yaml', 'label': 'YAML'},
            ]
        },
        'mediaEmbed': {
            'previewsInData': True,
        },
        'height': 500,
        'width': '100%',
    },
    'minimal': {
        'toolbar': ['bold', 'italic', 'link', 'bulletedList', 'numberedList', 'blockQuote'],
        'height': 200,
    },
}

# ─── Unfold Configuration ───────────────────────────────────────────────
UNFOLD = {
    "SITE_TITLE": "Learnova Admin",
    "SITE_HEADER": "Learnova",
    "SITE_SYMBOL": "school",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "DASHBOARD_CALLBACK": "core.dashboard.dashboard_callback",
    "COLORS": {
        "primary": {
            "50": "240 253 244",
            "100": "220 252 231",
            "200": "187 247 208",
            "300": "134 239 172",
            "400": "74 222 128",
            "500": "34 197 94",
            "600": "22 163 74",
            "700": "21 128 61",
            "800": "22 101 52",
            "900": "20 83 45",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Content",
                "separator": True,
                "items": [
                    {"title": "Topics", "icon": "book", "link": "/admin/learning/topic/"},
                    {"title": "Chapters", "icon": "layers", "link": "/admin/learning/chapter/"},
                    {"title": "Lessons", "icon": "article", "link": "/admin/learning/lesson/"},
                    {"title": "Quizzes", "icon": "quiz", "link": "/admin/quizzes/quiz/"},
                ],
            },
            {
                "title": "Community",
                "separator": True,
                "items": [
                    {"title": "Users", "icon": "person", "link": "/admin/auth/user/"},
                    {"title": "User Profiles", "icon": "manage_accounts", "link": "/admin/accounts/userprofile/"},
                    {"title": "Comments", "icon": "forum", "link": "/admin/learning/lessoncomment/"},
                    {"title": "Ratings", "icon": "star", "link": "/admin/learning/lessonrating/"},
                    {"title": "Certificates", "icon": "workspace_premium", "link": "/admin/learning/certificate/"},
                    {"title": "Subscribers", "icon": "mail", "link": "/admin/core/newslettersubscriber/"},
                    {"title": "Contact Messages", "icon": "chat", "link": "/admin/core/contactmessage/"},
                ],
            },
            {
                "title": "Newsletter",
                "separator": True,
                "items": [
                    {"title": "Send Newsletter", "icon": "send", "link": "/admin/newsletter/newslettercampaign/"},
                ],
            },
        ],
    },
}
