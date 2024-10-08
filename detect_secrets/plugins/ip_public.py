import re

from .base import RegexBasedDetector


class IPPublicDetector(RegexBasedDetector):
    """Scans for public ip address (ipv4)

    Some non-public ipv4 addresses are ignored, such as:
        - 127.
        - 10.
        - 172.(16-31)
        - 192.168.
        - 169.254. - Link Local Address IPv4

    Reference:
    https://www.iana.org/assignments/ipv4-address-space/ipv4-address-space.xhtml
    https://en.wikipedia.org/wiki/Private_network
    """
    secret_type = 'Public IP (ipv4)'

    denylist_ipv4_address = r"""
        (?<![\w.])         # Negative lookbehind: Ensures no preceding word character or dot
        (                  # Start of the main capturing group
            (?!            # Negative lookahead: Ensures the following pattern doesn't match
                192\.168\. # Exclude "192.168."
                |127\.     # Exclude "127."
                |10\.      # Exclude "10."
                |169\.254\. # Exclude IPv4 Link Local Address (169.254.0.0/16)
                |172\.(?:1[6-9]|2[0-9]|3[01])   # Exclude "172." with specific ranges
            )
            (?:            # Non-capturing group for octets
                           # Match numbers 0-255 followed by dot, properly handle leading zeros
                (?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.
            ){3}           # Repeat for three octets
                           # Match final octet (0-255), properly handle leading zeros
            (?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])
            (?:            # Optional non-capturing group for port number
                :\d{1,5}   # Match colon followed by 1 to 5 digits
            )?
        )                  # End of the main capturing group
        (?![\w.])          # Negative lookahead: Ensures no following word character or dot
    """

    denylist = [
        re.compile(denylist_ipv4_address, flags=re.IGNORECASE | re.VERBOSE),
    ]
