# pyright: reportUnknownArgumentType=false,reportUnknownVariableType=false,reportUnknownMemberType=false,reportArgumentType=false
"""Tests to validate that Result[T, E] satisfies the monad laws."""

import result
from result import Ok, Err, Result


def double(x: int) -> Result[int, str]:
    """Returns Ok(x * 2)"""
    return Ok(x * 2)


def add_ten(x: int) -> Result[int, str]:
    """Returns Ok(x + 10)"""
    return Ok(x + 10)


def hundred_over(x: int) -> Result[float, str]:
    """Returns Ok(100 / x) or Err if x is 0"""
    return Ok(100.0 / x) if x != 0 else Err("division by zero")


def stringify(x: int) -> Result[str, str]:
    """Returns Ok(str(x))"""
    return Ok(str(x))


def fail(x: int) -> Result[int, str]:
    """Always returns an error"""
    return Err(f"failed with {x}")


class TestMonadLaws:
    # LEFT IDENTITY LAW: result.pure(a).and_then(f) === f(a)

    def test_left_identity_with_ok(self):
        """Left identity law with a function that returns Ok"""
        a = 5

        left = result.pure(a).and_then(double)

        right = double(a)

        assert result.is_ok(left) and result.is_ok(right)
        assert left.value == right.value
        assert left.value == 10

    def test_left_identity_with_err(self):
        """Left identity law with a function that returns Err"""
        a = 0

        left = result.pure(a).and_then(hundred_over)
        right = hundred_over(a)

        assert result.is_err(left) and result.is_err(right)
        assert left.error == right.error
        assert left.error == "division by zero"

    def test_left_identity_with_type_change(self):
        """Left identity law with a function that changes types"""
        a = 42

        left = result.pure(a).and_then(stringify)
        right = stringify(a)

        assert result.is_ok(left) and result.is_ok(right)
        assert left.value == right.value
        assert left.value == "42"

    # RIGHT IDENTITY LAW: m.and_then(result.pure) === m

    def test_right_identity_with_ok(self):
        """Right identity law with Ok value"""
        m: Result[int, str] = Ok(10)

        it = m.and_then(result.pure)

        assert result.is_ok(it) and result.is_ok(m)
        assert it.value == m.value
        assert it.value == 10

    def test_right_identity_with_err(self):
        """Right identity law with Err value"""
        m: Result[int, str] = Err("something went wrong")

        it = m.and_then(result.pure)

        assert result.is_err(it) and result.is_err(m)
        assert it.error == m.error
        assert it.error == "something went wrong"

    # ASSOCIATIVITY LAW: m.and_then(f).and_then(g) === m.and_then(lambda x: f(x).and_then(g))

    def test_associativity_with_ok_chain(self):
        """Associativity law with chain of Ok results"""
        m: Result[int, str] = Ok(5)

        left = m.and_then(double).and_then(add_ten)

        right = m.and_then(lambda x: double(x).and_then(add_ten))

        assert result.is_ok(left) and result.is_ok(right)
        assert left.value == right.value
        assert left.value == 20  # (5 * 2) + 10 = 20

    def test_associativity_with_three_functions(self):
        """Associativity law with three different functions"""
        m: Result[int, str] = Ok(4)

        left = m.and_then(double).and_then(add_ten).and_then(double)

        right = m.and_then(
            lambda x: double(x).and_then(lambda y: add_ten(y).and_then(double))
        )

        assert result.is_ok(left) and result.is_ok(right)
        assert left.value == right.value
        assert left.value == 36  # ((4 * 2) + 10) * 2 = 36

    def test_associativity_with_error_in_first_function(self):
        """Associativity law when first function returns Err"""
        m: Result[int, str] = Ok(5)

        left = m.and_then(fail).and_then(double)
        right = m.and_then(lambda x: fail(x).and_then(double))

        assert result.is_err(left) and result.is_err(right)
        assert left.error == right.error
        assert left.error == "failed with 5"

    def test_associativity_with_error_in_second_function(self):
        """Associativity law when second function returns Err"""
        m: Result[int, str] = Ok(10)

        # double(10) => Ok(20), then hundred_over(20) => Ok(5.0)
        # But if we use 0, we get an error
        def return_zero(_: int) -> Result[int, str]:
            return Ok(0)

        left = m.and_then(return_zero).and_then(hundred_over)
        right = m.and_then(lambda x: return_zero(x).and_then(hundred_over))

        assert result.is_err(left) and result.is_err(right)
        assert left.error == right.error
        assert left.error == "division by zero"

    def test_associativity_with_initial_error(self):
        """Associativity law when starting with Err"""
        m: Result[int, str] = Err("initial error")

        left = m.and_then(double).and_then(add_ten)
        right = m.and_then(lambda x: double(x).and_then(add_ten))

        assert result.is_err(left) and result.is_err(right)
        assert left.error == right.error
        assert left.error == "initial error"

    def test_associativity_with_type_changes(self):
        """Associativity law with functions that change types"""
        m: Result[int, str] = Ok(42)

        def int_to_str(x: int) -> Result[str, str]:
            return Ok(str(x))

        def str_length(s: str) -> Result[int, str]:
            return Ok(len(s))

        left = m.and_then(int_to_str).and_then(str_length)
        right = m.and_then(lambda x: int_to_str(x).and_then(str_length))

        assert result.is_ok(left) and result.is_ok(right)
        assert left.value == right.value
        assert left.value == 2  # len("42") = 2


class TestMonadBehavior:
    """General tests for monadic behavior"""

    def test_short_circuit_on_error(self):
        """Test that Err short-circuits the chain"""
        call_count = {"count": 0}

        def track_calls(x: int) -> Result[int, str]:
            call_count["count"] += 1
            return Ok(x + 1)

        it = (
            Ok(5)
            .and_then(track_calls)  # Called: count = 1
            .and_then(fail)  # Returns Err
            .and_then(track_calls)  # Should NOT be called
            .and_then(track_calls)  # Should NOT be called
        )

        assert result.is_err(it)
        assert call_count["count"] == 1  # Only first track_calls was executed

    def test_err_propagation(self):
        """Test that errors propagate correctly through the chain"""
        error_msg = "custom error"

        it = (
            Ok(5)
            .and_then(double)
            .and_then(lambda _: Err(error_msg))
            .and_then(stringify)
        )

        assert result.is_err(it)
        assert it.error == error_msg
