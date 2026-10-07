import unittest

from xautomation.oauth1 import authorization_header


class OAuthTests(unittest.TestCase):
    def test_oauth_header_is_deterministic(self):
        header = authorization_header(
            "POST", "https://api.x.com/2/tweets", "key", "secret", "token", "token-secret",
            nonce="abc", timestamp="1234567890"
        )
        self.assertTrue(header.startswith("OAuth oauth_consumer_key="))
        self.assertIn("oauth_signature=", header)
        self.assertIn('oauth_nonce="abc"', header)

