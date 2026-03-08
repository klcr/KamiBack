"""ドメイン層の例外クラス。"""

from __future__ import annotations


class DomainError(Exception):
    """ドメイン層の基底例外。"""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ValidationError(DomainError):
    """バリデーション違反。複数のエラーメッセージを保持できる。"""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))
