import bleach


ALLOWED_ICON_TAGS = {'i', 'span', 'svg', 'path', 'circle', 'rect', 'line', 'polyline', 'polygon'}
ALLOWED_ICON_ATTRIBUTES = {
    '*': {'class', 'aria-hidden', 'role', 'title'},
    'svg': {'viewBox', 'width', 'height', 'fill', 'stroke', 'stroke-width',
            'stroke-linecap', 'stroke-linejoin', 'xmlns', 'preserveAspectRatio'},
    'path': {'d', 'fill', 'stroke', 'stroke-width', 'stroke-linecap',
             'stroke-linejoin', 'fill-rule', 'clip-rule'},
    'circle': {'cx', 'cy', 'r', 'fill', 'stroke', 'stroke-width'},
    'rect': {'x', 'y', 'width', 'height', 'rx', 'ry', 'fill', 'stroke', 'stroke-width'},
    'line': {'x1', 'x2', 'y1', 'y2', 'stroke', 'stroke-width'},
    'polyline': {'points', 'fill', 'stroke', 'stroke-width'},
    'polygon': {'points', 'fill', 'stroke', 'stroke-width'},
}


def sanitize_icon_html(value):
    """Allow only presentational icon markup; never render arbitrary HTML."""
    return bleach.clean(
        value or '',
        tags=ALLOWED_ICON_TAGS,
        attributes=ALLOWED_ICON_ATTRIBUTES,
        protocols=[],
        strip=True,
    ).strip()