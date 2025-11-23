# pyright: reportUnknownArgumentType=false,reportUnknownVariableType=false,reportUnknownMemberType=false,reportArgumentType=false
"""Comprehensive tests for all Result methods."""

from neverthrow import result
from neverthrow.result import Ok, Err, Result, is_ok, is_err, wrap, wrap_async
import pytest


class TestMap:
    """Tests for the map method"""

    def test_map_on_ok_transforms_value(self):
        """map on Ok applies the function to the value"""
        r: Result[int, str] = Ok(5)
        mapped = r.map(lambda x: x * 2)

        assert is_ok(mapped)
        assert mapped.value == 10

    def test_map_on_ok_with_type_change(self):
        """map on Ok can change the value type"""
        r: Result[int, str] = Ok(42)
        mapped = r.map(str)

        assert is_ok(mapped)
        assert mapped.value == "42"

    def test_map_on_err_does_not_apply_function(self):
        """map on Err does not apply the function"""
        r: Result[int, str] = Err("error")
        mapped = r.map(lambda x: f"x is {x}")

        assert is_err(mapped)
        assert mapped.error == "error"

    def test_map_chains_multiple_transformations(self):
        """multiple map calls chain together"""
        r: Result[int, str] = Ok(5)
        result = r.map(lambda x: x * 2).map(lambda x: x + 3).map(str)

        assert is_ok(result)
        assert result.value == "13"  # (5 * 2 + 3) = "13"


class TestMapErr:
    """Tests for the map_err method"""

    def test_map_err_on_err_transforms_error(self):
        """map_err on Err applies the function to the error"""
        r: Result[int, str] = Err("error")
        mapped = r.map_err(lambda e: e.upper())

        assert is_err(mapped)
        assert mapped.error == "ERROR"

    def test_map_err_on_err_with_type_change(self):
        """map_err on Err can change the error type"""
        r: Result[int, str] = Err("error")
        mapped = r.map_err(lambda e: len(e))

        assert is_err(mapped)
        assert mapped.error == 5

    def test_map_err_on_ok_does_not_apply_function(self):
        """map_err on Ok does not apply the function"""
        r: Result[int, str] = Ok(42)
        mapped = r.map_err(lambda e: str(e).upper())

        assert is_ok(mapped)
        assert mapped.value == 42

    def test_map_err_chains_multiple_transformations(self):
        """multiple map_err calls chain together"""
        r: Result[int, str] = Err("error")
        result = r.map_err(lambda e: e.upper()).map_err(lambda e: f"[{e}]")

        assert is_err(result)
        assert result.error == "[ERROR]"


class TestOrElse:
    """Tests for the or_else method"""

    def test_or_else_on_err_recovers_with_ok(self):
        """or_else on Err can recover with an Ok"""
        r: Result[int, str] = Err("error")
        result = r.or_else(lambda _: Ok(42))

        assert is_ok(result)
        assert result.value == 42

    def test_or_else_on_err_can_return_another_err(self):
        """or_else on Err can return a different Err"""
        r: Result[int, str] = Err("first error")
        result = r.or_else(lambda e: Err(f"handled: {e}"))

        assert is_err(result)
        assert result.error == "handled: first error"

    def test_or_else_on_ok_does_not_apply_function(self):
        """or_else on Ok does not apply the function"""
        r: Result[int, str] = Ok(42)
        result = r.or_else(lambda _: Ok(0))

        assert is_ok(result)
        assert result.value == 42

    def test_or_else_chains_multiple_recovery_attempts(self):
        """multiple or_else calls can chain recovery logic"""
        r: Result[int, str] = Err("error")
        result = (
            r.or_else(lambda _: Err("still failing"))
            .or_else(lambda _: Err("still failing 2"))
            .or_else(lambda _: Ok(100))
        )

        assert is_ok(result)
        assert result.value == 100


class TestUnwrapOr:
    """Tests for the unwrap_or method"""

    def test_unwrap_or_on_ok_returns_value(self):
        """unwrap_or on Ok returns the Ok value"""
        r: Result[int, str] = Ok(42)
        value = r.unwrap_or(0)

        assert value == 42

    def test_unwrap_or_on_err_returns_default(self):
        """unwrap_or on Err returns the default value"""
        r: Result[int, str] = Err("error")
        value = r.unwrap_or(0)

        assert value == 0

    def test_unwrap_or_with_different_types(self):
        """unwrap_or works with different default types"""
        r: Result[str, str] = Err("error")
        value = r.unwrap_or("default")

        assert value == "default"


class TestUnwrapOrElse:
    """Tests for the unwrap_or_else method"""

    def test_unwrap_or_else_on_ok_returns_value(self):
        """unwrap_or_else on Ok returns the Ok value"""
        r: Result[int, str] = Ok(42)
        value = r.unwrap_or_else(lambda _: 0)

        assert value == 42

    def test_unwrap_or_else_on_err_calls_function(self):
        """unwrap_or_else on Err calls the function with the error"""
        r: Result[int, str] = Err("error")
        value = r.unwrap_or_else(lambda e: len(e))

        assert value == 5

    def test_unwrap_or_else_on_err_computes_default(self):
        """unwrap_or_else on Err can compute a default based on the error"""
        r: Result[int, str] = Err("custom error")
        value = r.unwrap_or_else(lambda e: 0 if "custom" in e else -1)

        assert value == 0


class TestInspect:
    """Tests for the inspect method"""

    def test_inspect_on_ok_calls_function(self):
        """inspect on Ok calls the function with the value"""
        side_effects = []
        r: Result[int, str] = Ok(42)
        result = r.inspect(lambda x: side_effects.append(x))

        assert is_ok(result)
        assert result.value == 42
        assert side_effects == [42]

    def test_inspect_on_err_does_not_call_function(self):
        """inspect on Err does not call the function"""
        side_effects = []
        r: Result[int, str] = Err("error")
        result = r.inspect(lambda x: side_effects.append(x))

        assert is_err(result)
        assert result.error == "error"
        assert side_effects == []

    def test_inspect_chains_with_other_operations(self):
        """inspect can be chained with other operations"""
        side_effects = []
        r: Result[int, str] = Ok(5)
        result = (
            r.map(lambda x: x * 2)
            .inspect(lambda x: side_effects.append(f"after map: {x}"))
            .map(lambda x: x + 3)
        )

        assert is_ok(result)
        assert result.value == 13
        assert side_effects == ["after map: 10"]


class TestInspectErr:
    """Tests for the inspect_err method"""

    def test_inspect_err_on_err_calls_function(self):
        """inspect_err on Err calls the function with the error"""
        side_effects = []
        r: Result[int, str] = Err("error")
        result = r.inspect_err(lambda e: side_effects.append(e))

        assert is_err(result)
        assert result.error == "error"
        assert side_effects == ["error"]

    def test_inspect_err_on_ok_does_not_call_function(self):
        """inspect_err on Ok does not call the function"""
        side_effects = []
        r: Result[int, str] = Ok(42)
        result = r.inspect_err(lambda e: side_effects.append(e))

        assert is_ok(result)
        assert result.value == 42
        assert side_effects == []

    def test_inspect_err_chains_with_other_operations(self):
        """inspect_err can be chained with other operations"""
        side_effects = []
        r: Result[int, str] = Err("error")
        result = (
            r.map_err(lambda e: e.upper())
            .inspect_err(lambda e: side_effects.append(f"after map_err: {e}"))
            .or_else(lambda _: Err("recovered"))
        )

        assert is_err(result)
        assert result.error == "recovered"
        assert side_effects == ["after map_err: ERROR"]


class TestFlatten:
    """Tests for the flatten method"""

    def test_flatten_ok_ok_returns_inner_ok(self):
        """flatten on Ok(Ok(x)) returns Ok(x)"""
        r: Result[Result[int, str], str] = Ok(Ok(42))
        result = r.flatten()

        assert is_ok(result)
        assert result.value == 42

    def test_flatten_ok_err_returns_inner_err(self):
        """flatten on Ok(Err(e)) returns Err(e)"""
        r: Result[Result[int, str], str] = Ok(Err("inner error"))
        result = r.flatten()

        assert is_err(result)
        assert result.error == "inner error"

    def test_flatten_err_returns_err(self):
        """flatten on Err returns Err"""
        r: Result[Result[int, str], str] = Err("outer error")
        result = r.flatten()

        assert is_err(result)
        assert result.error == "outer error"

    def test_flatten_chains_multiple_levels(self):
        """flatten can handle multiple levels of nesting"""
        r: Result[Result[int, str], str] = Ok(Ok(42))
        result = r.flatten().and_then(lambda x: Ok(Ok(x * 2))).flatten()

        assert is_ok(result)
        assert result.value == 84


class TestIsOkIsErr:
    """Tests for is_ok and is_err type guard functions"""

    def test_is_ok_returns_true_for_ok(self):
        """is_ok returns True for Ok values"""
        r: Result[int, str] = Ok(42)
        assert is_ok(r)
        assert not is_err(r)

    def test_is_err_returns_true_for_err(self):
        """is_err returns True for Err values"""
        r: Result[int, str] = Err("error")
        assert is_err(r)
        assert not is_ok(r)

    def test_is_ok_narrows_type(self):
        """is_ok can be used for type narrowing"""
        r: Result[int, str] = Ok(42)
        if is_ok(r):
            # Type checker should know r is Ok[int] here
            value: int = r.value
            assert value == 42

    def test_is_err_narrows_type(self):
        """is_err can be used for type narrowing"""
        r: Result[int, str] = Err("error")
        if is_err(r):
            # Type checker should know r is Err[str] here
            error: str = r.error
            assert error == "error"


class TestWrap:
    """Tests for the wrap decorator"""

    def test_wrap_on_successful_function(self):
        """wrap returns Ok for successful function calls"""

        @wrap
        def divide(a: int, b: int) -> float:
            return a / b

        result: Result[float, Exception] = divide(10, 2)

        assert is_ok(result)
        assert result.value == 5.0

    def test_wrap_on_function_that_raises(self):
        """wrap returns Err for functions that raise exceptions"""

        @wrap
        def divide(a: int, b: int) -> float:
            return a / b

        result: Result[float, Exception] = divide(10, 0)

        assert is_err(result)
        assert isinstance(result.error, ZeroDivisionError)

    def test_wrap_preserves_exception_details(self):
        """wrap preserves the exception object"""

        @wrap
        def raise_value_error() -> int:
            raise ValueError("custom message")

        result: Result[int, Exception] = raise_value_error()

        assert is_err(result)
        assert isinstance(result.error, ValueError)
        assert str(result.error) == "custom message"

    def test_wrap_with_args_and_kwargs(self):
        """wrap works with functions that take args and kwargs"""

        @wrap
        def complex_function(a: int, b: int, c: int = 0) -> int:
            if c == 0:
                raise ValueError("c cannot be zero")
            return a + b + c

        ok_result: Result[int, Exception] = complex_function(1, 2, c=3)
        err_result: Result[int, Exception] = complex_function(1, 2)

        assert is_ok(ok_result)
        assert ok_result.value == 6
        assert is_err(err_result)


class TestWrapAsync:
    """Tests for the wrap_async decorator"""

    @pytest.mark.asyncio
    async def test_wrap_async_on_successful_function(self):
        """wrap_async returns Ok for successful async function calls"""

        @wrap_async
        async def async_divide(a: int, b: int) -> float:
            return a / b

        result: Result[float, Exception] = await async_divide(10, 2)

        assert is_ok(result)
        assert result.value == 5.0

    @pytest.mark.asyncio
    async def test_wrap_async_on_function_that_raises(self):
        """wrap_async returns Err for async functions that raise exceptions"""

        @wrap_async
        async def async_divide(a: int, b: int) -> float:
            return a / b

        result: Result[float, Exception] = await async_divide(10, 0)

        assert is_err(result)
        assert isinstance(result.error, ZeroDivisionError)

    @pytest.mark.asyncio
    async def test_wrap_async_preserves_exception_details(self):
        """wrap_async preserves the exception object"""

        @wrap_async
        async def async_raise_value_error() -> int:
            raise ValueError("async custom message")

        result: Result[int, Exception] = await async_raise_value_error()

        assert is_err(result)
        assert isinstance(result.error, ValueError)
        assert str(result.error) == "async custom message"

    @pytest.mark.asyncio
    async def test_wrap_async_with_args_and_kwargs(self):
        """wrap_async works with async functions that take args and kwargs"""

        @wrap_async
        async def async_complex_function(a: int, b: int, c: int = 0) -> int:
            if c == 0:
                raise ValueError("c cannot be zero")
            return a + b + c

        ok_result: Result[int, Exception] = await async_complex_function(1, 2, c=3)
        err_result: Result[int, Exception] = await async_complex_function(1, 2)

        assert is_ok(ok_result)
        assert ok_result.value == 6
        assert is_err(err_result)


class TestRepr:
    """Tests for __repr__ methods"""

    def test_ok_repr(self):
        """Ok.__repr__ shows the value"""
        r = Ok(42)
        assert repr(r) == "Ok(42)"

    def test_ok_repr_with_string(self):
        """Ok.__repr__ shows string values with quotes"""
        r = Ok("hello")
        assert repr(r) == "Ok('hello')"

    def test_err_repr(self):
        """Err.__repr__ shows the error"""
        r = Err("error message")
        assert repr(r) == "Err('error message')"

    def test_err_repr_with_int(self):
        """Err.__repr__ shows non-string errors"""
        r = Err(404)
        assert repr(r) == "Err(404)"

    def test_err_repr_with_complex_str(self):
        """Err.__repr__ handles complex string errors"""
        r = Err("Line1\nLine2\tTabbed")
        assert repr(r) == "Err('Line1\\nLine2\\tTabbed')"


class TestPure:
    """Tests for the pure function"""

    def test_pure_creates_ok(self):
        """pure creates an Ok result"""
        r = result.pure(42)

        assert is_ok(r)
        assert r.value == 42

    def test_pure_with_different_types(self):
        """pure works with different value types"""
        r_str = result.pure("hello")
        r_list = result.pure([1, 2, 3])

        assert is_ok(r_str)
        assert r_str.value == "hello"
        assert is_ok(r_list)
        assert r_list.value == [1, 2, 3]
