def format_datetime(value, format='%d %B %Y %H:%M'):
    if value is None:
        return ""
    return value.strftime(format)
