import re


PHONE_COUNTRY_CODE = '+255'
PHONE_PATTERN = re.compile(r'^\+255\d{9}$')


def normalize_phone_number(value):
    """Normalize a Tanzania phone number to E.164 format (e.g. +255674303431).

    Accepts:
      - '674303431'         (9 digits, as entered by the user)
      - '0754303451'        (10 digits with leading 0)
      - '255754303451'      (12 digits, local format)
      - '+255754303451'     (already normalized)
    Returns the normalized +255XXXXXXXXX string or None if invalid.
    """
    if not value:
        return None

    phone = str(value).strip().replace(' ', '').replace('-', '')

    if phone.startswith('0'):
        phone = phone[1:]
        phone = PHONE_COUNTRY_CODE + phone
    elif phone.startswith('255') and not phone.startswith('+255'):
        phone = PHONE_COUNTRY_CODE + phone[3:]
    elif phone.startswith('+255'):
        pass
    else:
        phone = PHONE_COUNTRY_CODE + phone

    if PHONE_PATTERN.match(phone):
        return phone
    return None