def is_caba_zipcode(zipcode: str) -> bool:
    """Rough CABA postal code check (starts with 'C' or 1000–1429 range)"""
    if not zipcode:
        return False
    zipcode = str(zipcode).upper().strip()
    if zipcode.startswith("C"):
        return True
    try:
        z = int(zipcode)
        return 1000 <= z <= 1429
    except ValueError:
        return False
