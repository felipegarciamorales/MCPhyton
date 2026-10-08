from auth_service.infrastructure.security.bcrypt_password_hasher import BcryptPasswordHasher


class TestBcryptPasswordHasher:
    def test_hash_produces_a_different_string_than_the_plain_password(self):
        hasher = BcryptPasswordHasher()

        assert hasher.hash("Str0ngPass") != "Str0ngPass"

    def test_verify_succeeds_for_the_correct_password(self):
        hasher = BcryptPasswordHasher()
        hashed = hasher.hash("Str0ngPass")

        assert hasher.verify("Str0ngPass", hashed) is True

    def test_verify_fails_for_an_incorrect_password(self):
        hasher = BcryptPasswordHasher()
        hashed = hasher.hash("Str0ngPass")

        assert hasher.verify("WrongPass1", hashed) is False

    def test_verify_fails_gracefully_for_a_malformed_hash(self):
        hasher = BcryptPasswordHasher()

        assert hasher.verify("Str0ngPass", "not-a-valid-hash") is False

    def test_two_hashes_of_the_same_password_differ_due_to_salting(self):
        hasher = BcryptPasswordHasher()

        assert hasher.hash("Str0ngPass") != hasher.hash("Str0ngPass")
