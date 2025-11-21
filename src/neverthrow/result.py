from collections.abc import Awaitable
from typing import Callable, Literal, TypeIs, final, override

type Result[T, E] = Ok[T] | Err[E]


def is_ok[T, E](result: Result[T, E]) -> TypeIs[Ok[T]]:
    return result.is_ok()


def is_err[T, E](result: Result[T, E]) -> TypeIs[Err[E]]:
    return result.is_err()


def wrap[T](func: Callable[..., T]) -> Callable[..., Result[T, Exception]]:
    def decorator(*args: object, **kwargs: object) -> Result[T, Exception]:
        try:
            return Ok(func(*args, **kwargs))
        except Exception as e:
            return Err(e)

    return decorator


def wrap_async[T](
    func: Callable[..., Awaitable[T]],
) -> Callable[..., Awaitable[Result[T, Exception]]]:
    async def decorator(*args: object, **kwargs: object) -> Result[T, Exception]:
        try:
            return Ok(await func(*args, **kwargs))
        except Exception as e:
            return Err(e)

    return decorator


def pure[T, _E](value: T) -> Result[T, _E]:
    return Ok(value)


@final
class Ok[T]:
    __match_args__ = ("value",)

    def __init__(self, value: T):
        self.value: T = value

    @override
    def __repr__(self) -> str:
        return f"Ok({self.value!r})"

    def is_ok(self) -> Literal[True]:
        return True

    def is_err(self) -> Literal[False]:
        return False

    def and_then[NewT, E](
        self, func: Callable[[T], Result[NewT, E]]
    ) -> Result[NewT, E]:
        return func(self.value)

    def map[NewT](self, func: Callable[[T], NewT]) -> Ok[NewT]:
        return Ok(func(self.value))

    def __or__[NewT](self, func: Callable[[T], NewT]) -> Ok[NewT]:
        return self.map(func)

    def map_err[_E](self, _func: Callable[[_E], _E]) -> Ok[T]:
        return self

    def or_else[_E](self, _func: Callable[[_E], Result[T, _E]]) -> Result[T, _E]:
        return self

    def unwrap_or(self, _default: T) -> T:
        return self.value

    def unwrap_or_else[_E](self, _func: Callable[[_E], T]) -> T:
        return self.value

    def inspect(self, func: Callable[[T], object]) -> Ok[T]:
        _ = func(self.value)
        return self

    def inspect_err[_E](self, _func: Callable[[_E], object]) -> Ok[T]:
        return self


@final
class Err[E]:
    __match_args__ = ("error",)

    def __init__(self, error: E):
        self.error: E = error

    @override
    def __repr__(self) -> str:
        return f"Err({self.error!r})"

    def is_ok(self) -> Literal[False]:
        return False

    def is_err(self) -> Literal[True]:
        return True

    def and_then[_T, _U](self, _func: Callable[[_T], Result[_U, E]]) -> Err[E]:
        return self

    def map[_T, _U](self, _func: Callable[[_T], _U]) -> Err[E]:
        return self

    def __or__[_T, _U](self, _func: Callable[[_T], _U]) -> Err[E]:
        return self

    def map_err[NewE](self, func: Callable[[E], NewE]) -> Err[NewE]:
        return Err(func(self.error))

    def or_else[T](self, func: Callable[[E], Result[T, E]]) -> Result[T, E]:
        return func(self.error)

    def unwrap_or[T](self, default: T) -> T:
        return default

    def unwrap_or_else[T](self, func: Callable[[E], T]) -> T:
        return func(self.error)

    def inspect[_T](self, _func: Callable[[_T], object]) -> Err[E]:
        return self

    def inspect_err(self, func: Callable[[E], object]) -> Err[E]:
        _ = func(self.error)
        return self
