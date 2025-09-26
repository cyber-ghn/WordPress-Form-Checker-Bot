def str_to_bool(value: str)-> bool:
    return value.strip().lower() == 'true'

def str_to_list(value: str) -> list:
    return [item.strip() for item in value.split(',') if item.strip()]