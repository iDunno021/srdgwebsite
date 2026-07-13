def get_client_ip(request):
    return (
        request.META.get('HTTP_X_REAL_IP')
        or request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[-1].strip()
        or request.META.get('REMOTE_ADDR', 'unknown')
    )
