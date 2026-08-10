import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import auth
import main
import models
import schemas


class AccountSafetyRouteTests(unittest.TestCase):
    def test_staff_management_routes_require_owner(self):
        protected_routes = {
            ("GET", "/users"),
            ("POST", "/users"),
            ("PATCH", "/users/{user_id}/status"),
            ("PATCH", "/users/{user_id}/role"),
            ("PATCH", "/users/{user_id}/password"),
        }

        for route in main.app.routes:
            for method in route.methods or set():
                route_key = (method, route.path)
                if route_key not in protected_routes:
                    continue

                dependency_calls = {
                    dependency.call for dependency in route.dependant.dependencies
                }
                self.assertIn(auth.require_owner, dependency_calls, route_key)
                protected_routes.remove(route_key)

        self.assertEqual(protected_routes, set())


class AccountSafetyDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.original_secret = auth.SECRET_KEY
        auth.SECRET_KEY = "account-safety-test-secret-key-for-hs256"
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        models.Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()

        self.owner = models.User(
            username="test_owner",
            password_hash=auth.hash_password("OwnerPass123"),
            role="owner",
        )
        self.employee = models.User(
            username="test_employee",
            password_hash=auth.hash_password("EmployeePass123"),
            role="employee",
        )
        self.db.add_all([self.owner, self.employee])
        self.db.commit()
        self.db.refresh(self.owner)
        self.db.refresh(self.employee)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()
        auth.SECRET_KEY = self.original_secret

    def token_for(self, user):
        return auth.create_access_token(
            user_id=user.id,
            role=user.role,
            token_version=user.token_version,
        )

    def test_access_token_lasts_exactly_thirty_minutes(self):
        token = self.token_for(self.owner)
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])

        self.assertEqual(auth.ACCESS_TOKEN_EXPIRE_MINUTES, 30)
        self.assertEqual(payload["exp"] - payload["iat"], 30 * 60)
        self.assertEqual(payload["ver"], self.owner.token_version)

    def test_current_user_rejects_missing_or_malformed_session_claims(self):
        now = datetime.now(timezone.utc)
        invalid_payloads = [
            {"sub": str(self.owner.id), "exp": now + timedelta(minutes=30)},
            {
                "sub": str(self.owner.id),
                "ver": "1",
                "exp": now + timedelta(minutes=30),
            },
            {
                "sub": "not-a-user-id",
                "ver": 1,
                "exp": now + timedelta(minutes=30),
            },
        ]

        for payload in invalid_payloads:
            token = jwt.encode(payload, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
            with self.assertRaises(HTTPException) as error:
                auth.get_current_user(token=token, db=self.db)
            self.assertEqual(error.exception.status_code, 401)

    def test_current_user_accepts_valid_token_and_rejects_expired_token(self):
        current_user = auth.get_current_user(
            token=self.token_for(self.owner),
            db=self.db,
        )
        self.assertEqual(current_user.id, self.owner.id)

        now = datetime.now(timezone.utc)
        expired_token = jwt.encode(
            {
                "sub": str(self.owner.id),
                "ver": self.owner.token_version,
                "iat": now - timedelta(minutes=31),
                "exp": now - timedelta(minutes=1),
            },
            auth.SECRET_KEY,
            algorithm=auth.ALGORITHM,
        )
        with self.assertRaises(HTTPException) as error:
            auth.get_current_user(token=expired_token, db=self.db)
        self.assertEqual(error.exception.status_code, 401)

    def test_status_change_invalidates_old_token_and_reactivation_allows_login(self):
        old_token = self.token_for(self.employee)
        starting_version = self.employee.token_version

        updated = main.update_user_status(
            self.employee.id,
            schemas.UserStatusUpdate(is_active=False),
            db=self.db,
            current_user=self.owner,
        )
        self.assertFalse(updated.is_active)
        self.assertEqual(updated.token_version, starting_version + 1)

        with self.assertRaises(HTTPException) as token_error:
            auth.get_current_user(token=old_token, db=self.db)
        self.assertEqual(token_error.exception.status_code, 401)

        with self.assertRaises(HTTPException) as login_error:
            main.login(
                SimpleNamespace(
                    username="test_employee",
                    password="EmployeePass123",
                ),
                db=self.db,
            )
        self.assertEqual(login_error.exception.status_code, 401)
        self.assertEqual(login_error.exception.detail, "Incorrect username or password")

        reactivated = main.update_user_status(
            self.employee.id,
            schemas.UserStatusUpdate(is_active=True),
            db=self.db,
            current_user=self.owner,
        )
        self.assertEqual(reactivated.token_version, starting_version + 2)

        with self.assertRaises(HTTPException):
            auth.get_current_user(token=old_token, db=self.db)

        login_result = main.login(
            SimpleNamespace(
                username=" test_employee ",
                password="EmployeePass123",
            ),
            db=self.db,
        )
        self.assertEqual(login_result["user_id"], self.employee.id)
        self.assertEqual(login_result["username"], "test_employee")

    def test_repeating_the_same_status_does_not_invalidate_sessions(self):
        starting_version = self.employee.token_version
        main.update_user_status(
            self.employee.id,
            schemas.UserStatusUpdate(is_active=True),
            db=self.db,
            current_user=self.owner,
        )
        self.assertEqual(self.employee.token_version, starting_version)

    def test_owner_cannot_deactivate_or_change_their_own_role(self):
        with self.assertRaises(HTTPException) as status_error:
            main.update_user_status(
                self.owner.id,
                schemas.UserStatusUpdate(is_active=False),
                db=self.db,
                current_user=self.owner,
            )
        self.assertEqual(status_error.exception.detail, "You cannot deactivate your own account")

        with self.assertRaises(HTTPException) as role_error:
            main.update_user_role(
                self.owner.id,
                schemas.UserRoleUpdate(role="employee"),
                db=self.db,
                current_user=self.owner,
            )
        self.assertEqual(role_error.exception.detail, "You cannot change your own role")

    def test_final_active_owner_cannot_be_removed(self):
        outside_owner = SimpleNamespace(id=999, is_active=True, role="owner")

        with self.assertRaises(HTTPException) as status_error:
            main.update_user_status(
                self.owner.id,
                schemas.UserStatusUpdate(is_active=False),
                db=self.db,
                current_user=outside_owner,
            )
        self.assertEqual(status_error.exception.detail, "At least one active owner must remain")

        with self.assertRaises(HTTPException) as role_error:
            main.update_user_role(
                self.owner.id,
                schemas.UserRoleUpdate(role="employee"),
                db=self.db,
                current_user=outside_owner,
            )
        self.assertEqual(role_error.exception.detail, "At least one active owner must remain")

    def test_one_owner_can_deactivate_another_when_a_second_owner_remains(self):
        second_owner = models.User(
            username="second_owner",
            password_hash=auth.hash_password("SecondOwnerPass123"),
            role="owner",
        )
        self.db.add(second_owner)
        self.db.commit()
        self.db.refresh(second_owner)

        updated = main.update_user_status(
            self.owner.id,
            schemas.UserStatusUpdate(is_active=False),
            db=self.db,
            current_user=second_owner,
        )
        self.assertFalse(updated.is_active)
        self.assertEqual(main.active_owner_count(self.db), 1)

    def test_password_and_role_changes_invalidate_previous_tokens(self):
        password_token = self.token_for(self.employee)
        main.reset_user_password(
            self.employee.id,
            schemas.UserPasswordReset(password="NewEmployeePass123"),
            db=self.db,
            current_user=self.owner,
        )
        with self.assertRaises(HTTPException):
            auth.get_current_user(token=password_token, db=self.db)

        role_token = self.token_for(self.employee)
        updated = main.update_user_role(
            self.employee.id,
            schemas.UserRoleUpdate(role="owner"),
            db=self.db,
            current_user=self.owner,
        )
        self.assertEqual(updated.role, "owner")
        with self.assertRaises(HTTPException):
            auth.get_current_user(token=role_token, db=self.db)

    def test_staff_list_and_create_responses_do_not_expose_security_fields(self):
        created = main.create_user(
            schemas.UserCreate(
                username="new_employee",
                password="SecurePass123",
                role="employee",
            ),
            db=self.db,
            current_user=self.owner,
        )
        users = main.list_users(db=self.db, current_user=self.owner)
        response = schemas.UserOut.model_validate(created).model_dump()

        self.assertEqual([user.id for user in users], sorted(user.id for user in users))
        self.assertTrue(response["is_active"])
        self.assertNotIn("password_hash", response)
        self.assertNotIn("token_version", response)

        with self.assertRaises(HTTPException) as duplicate_error:
            main.create_user(
                schemas.UserCreate(
                    username="new_employee",
                    password="AnotherPass123",
                    role="employee",
                ),
                db=self.db,
                current_user=self.owner,
            )
        self.assertEqual(duplicate_error.exception.status_code, 400)

        with self.assertRaises(HTTPException) as missing_error:
            main.update_user_status(
                9999,
                schemas.UserStatusUpdate(is_active=False),
                db=self.db,
                current_user=self.owner,
            )
        self.assertEqual(missing_error.exception.status_code, 404)


class AccountSafetySchemaTests(unittest.TestCase):
    def test_new_account_limits_are_enforced_after_username_trimming(self):
        valid = schemas.UserCreate(
            username="  employee.name@example.com  ",
            password="12345678",
            role="employee",
        )
        self.assertEqual(valid.username, "employee.name@example.com")

        for username in ["ab", "x" * 51, "   "]:
            with self.assertRaises(ValidationError):
                schemas.UserCreate(
                    username=username,
                    password="12345678",
                    role="employee",
                )

        for password in ["1234567", "        ", "x" * 73, "é" * 37]:
            with self.assertRaises(ValidationError):
                schemas.UserCreate(
                    username="employee",
                    password=password,
                    role="employee",
                )


if __name__ == "__main__":
    unittest.main()
