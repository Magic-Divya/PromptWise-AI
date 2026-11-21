import tempfile
from pathlib import Path

import src.database as db
from src.engine import optimize_prompt, FRAMEWORKS

print("\n========== FRAMEWORK TESTS ==========")

for framework in FRAMEWORKS:
    result = optimize_prompt(
        prompt="Explain the applications of artificial intelligence in education.",
        framework=framework,
        task="Educational explanation",
        audience="Computer science students",
        role="AI tutor",
        output_format="Structured paragraphs",
        context="Academic project",
        constraints="Use clear examples and avoid unsupported claims."
    )

    assert result["framework"] == framework
    assert len(result["improved_prompt"]) > 0
    assert "requirements" in result["analysis"]

    print("[PASS]", framework)

print("\n========== AUTHENTICATION TESTS ==========")

# Use a temporary database so your actual project accounts are untouched.
with tempfile.TemporaryDirectory() as temp_dir:
    db.DB_PATH = Path(temp_dir) / "test_database.db"

    db.init_db()

    success, message = db.create_user(
        "Test User",
        "promptwise_test_user",
        "promptwise_test@example.com",
        "TestPassword123"
    )

    assert success, message
    print("[PASS] Registration:", message)

    user = db.verify_user(
        "promptwise_test_user",
        "TestPassword123"
    )

    assert user is not None
    assert user["username"] == "promptwise_test_user"
    print("[PASS] Login with correct password")

    wrong_user = db.verify_user(
        "promptwise_test_user",
        "WrongPassword123"
    )

    assert wrong_user is None
    print("[PASS] Incorrect password rejected")

    duplicate, duplicate_message = db.create_user(
        "Another User",
        "promptwise_test_user",
        "another@example.com",
        "AnotherPassword123"
    )

    assert not duplicate
    print("[PASS] Duplicate username rejected")

    print("[PASS] Temporary database tests completed")

print("\n========== APPLICATION SYNTAX ==========")
print("All backend tests completed.")
