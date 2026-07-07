"""Tests for SecretDetector — F018 Git 密钥检测."""

import pytest


class TestDetectAWSKey:
    def test_detects_aws_access_key(self):
        from app.core.git_handler import SecretDetectedError, SecretDetector

        detector = SecretDetector()
        files = [{"path": "config.py", 'content': 'API_KEY = "AKIA1234567890123456"'}]
        with pytest.raises(SecretDetectedError) as excinfo:
            detector.detect(files)
        matches = excinfo.value.matches
        assert len(matches) >= 1
        assert any(m["pattern_name"] == "AWS Access Key" for m in matches)

    def test_detects_generic_password(self):
        from app.core.git_handler import SecretDetectedError, SecretDetector

        detector = SecretDetector()
        files = [{"path": ".env", 'content': 'password = "supersecret123"'}]
        with pytest.raises(SecretDetectedError) as excinfo:
            detector.detect(files)
        matches = excinfo.value.matches
        assert any(m["pattern_name"] == "Generic Password" for m in matches)

    def test_detects_bearer_token(self):
        from app.core.git_handler import SecretDetectedError, SecretDetector

        detector = SecretDetector()
        files = [{"path": "auth.py", 'content': 'bearer eyJhbGciOiJIUzI1NiJ9.test.signature'}]
        with pytest.raises(SecretDetectedError) as excinfo:
            detector.detect(files)
        matches = excinfo.value.matches
        assert any(m["pattern_name"] == "Bearer Token" for m in matches)

    def test_detects_private_key(self):
        from app.core.git_handler import SecretDetectedError, SecretDetector

        detector = SecretDetector()
        files = [{"path": "key.pem", "content": "-----BEGIN RSA PRIVATE KEY-----\nMIIE..."}]
        with pytest.raises(SecretDetectedError) as excinfo:
            detector.detect(files)
        matches = excinfo.value.matches
        assert any(m["pattern_name"] == "Private Key" for m in matches)

    def test_detects_github_token(self):
        from app.core.git_handler import SecretDetectedError, SecretDetector

        detector = SecretDetector()
        files = [{"path": "ci.yml", 'content': 'GITHUB_TOKEN: "ghp_abcdefghijklmnopqrstuvwxyz1234567890"'}]
        with pytest.raises(SecretDetectedError) as excinfo:
            detector.detect(files)
        matches = excinfo.value.matches
        assert any(m["pattern_name"] == "GitHub Token" for m in matches)

    def test_detects_github_token_in_var(self):
        from app.core.git_handler import SecretDetectedError, SecretDetector

        detector = SecretDetector()
        files = [{"path": "a.py", 'content': 'github_token = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"'}]
        with pytest.raises(SecretDetectedError) as excinfo:
            detector.detect(files)
        matches = excinfo.value.matches
        assert any(m["pattern_name"] == "GitHub Token" for m in matches)


class TestDetectEdgeCases:
    def test_empty_files(self):
        from app.core.git_handler import SecretDetector

        detector = SecretDetector()
        result = detector.detect([])
        assert result == []

    def test_empty_content(self):
        from app.core.git_handler import SecretDetector

        detector = SecretDetector()
        files = [{"path": "empty.py", "content": ""}]
        result = detector.detect(files)
        assert result == []

    def test_none_content(self):
        from app.core.git_handler import SecretDetector

        detector = SecretDetector()
        files = [{"path": "a.py", "content": None}]
        result = detector.detect(files)
        assert result == []

    def test_line_999(self):
        from app.core.git_handler import SecretDetectedError, SecretDetector

        detector = SecretDetector()
        lines = ["safe"] * 998 + ['github_token = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"']
        files = [{"path": "a.py", "content": "\n".join(lines)}]
        with pytest.raises(SecretDetectedError) as excinfo:
            detector.detect(files)
        matches = excinfo.value.matches
        assert any(m["line_number"] == 999 for m in matches)

    def test_truncation_80_chars(self):
        from app.core.git_handler import SecretDetectedError, SecretDetector

        detector = SecretDetector()
        long_line = 'password = "' + "x" * 100 + '"'
        files = [{"path": "a.py", "content": long_line}]
        with pytest.raises(SecretDetectedError) as excinfo:
            detector.detect(files)
        matches = excinfo.value.matches
        assert all(len(m["matched_text"]) <= 80 for m in matches)
